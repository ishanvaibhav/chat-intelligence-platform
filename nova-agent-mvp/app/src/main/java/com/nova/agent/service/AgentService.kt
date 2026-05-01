package com.nova.agent.service

import android.app.Notification
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Intent
import android.media.AudioManager
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.lifecycle.LifecycleService
import androidx.lifecycle.lifecycleScope
import com.nova.agent.MainActivity
import com.nova.agent.NovaApp
import com.nova.agent.R
import com.nova.agent.actions.CapturePhotoAction
import com.nova.agent.actions.SilentModeAction
import com.nova.agent.actions.SpeakReplyAction
import com.nova.agent.memory.GalleryHashStore
import com.nova.agent.memory.LifeLogger
import com.nova.agent.perception.EmotionDetector
import com.nova.agent.perception.SceneQualityScorer
import com.nova.agent.perception.VoiceActivityDetector
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.util.Locale

class AgentService : LifecycleService() {

    enum class State { IDLE, LISTENING, THINKING, SPEAKING, SLEEPING }

    private lateinit var audioManager: AudioManager
    private lateinit var silentMode: SilentModeAction
    private lateinit var tts: SpeakReplyAction
    private lateinit var lifeLogger: LifeLogger
    private lateinit var vad: VoiceActivityDetector
    private lateinit var sceneScorer: SceneQualityScorer
    private lateinit var galleryHashStore: GalleryHashStore
    private lateinit var capturePhoto: CapturePhotoAction
    private lateinit var emotionDetector: EmotionDetector

    private val meetingBuffer = mutableListOf<FloatArray>()
    private var agentState = State.IDLE
    private var inConversation = false
    private var speechFrameCount = 0
    private var silenceFrameCount = 0
    private var frameCount = 0L
    private var serviceJob: Job? = null
    private var lastAutoCaptureAt = 0L

    companion object {
        private const val TAG = "NovaAgent"
        const val NOTIF_ID = 1
        private const val CONVERSATION_START_FRAMES = 20
        private const val SILENCE_THRESHOLD_FRAMES = 100
        private const val CAMERA_CHECK_INTERVAL_MS = 12_000L
        private const val MIN_CAPTURE_GAP_MS = 90_000L
        var instance: AgentService? = null
    }

    override fun onCreate() {
        super.onCreate()
        instance = this
        Log.d(TAG, "AgentService created")
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        super.onStartCommand(intent, flags, startId)

        initComponentsIfNeeded()
        startForeground(NOTIF_ID, buildNotification(currentStatus()))

        if (serviceJob?.isActive == true) {
            Log.d(TAG, "AgentService already running; ignoring duplicate start")
            return START_STICKY
        }

        capturePhoto.initCamera()
        serviceJob = lifecycleScope.launch {
            launch(Dispatchers.IO) { seedGalleryHashes() }
            launch(Dispatchers.IO) { audioLoop() }
            launch(Dispatchers.IO) { cameraLoop() }
            launch(Dispatchers.Main) { statusLoop() }
        }

        lifeLogger.logEvent("Nova agent started")
        Log.d(TAG, "AgentService started")
        return START_STICKY
    }

    private fun initComponentsIfNeeded() {
        if (::silentMode.isInitialized) return

        audioManager = getSystemService(AUDIO_SERVICE) as AudioManager
        silentMode = SilentModeAction(this, audioManager)
        tts = SpeakReplyAction(this)
        lifeLogger = LifeLogger(this)
        vad = VoiceActivityDetector(this)
        sceneScorer = SceneQualityScorer(this)
        galleryHashStore = GalleryHashStore(this)
        capturePhoto = CapturePhotoAction(this, this)
        emotionDetector = EmotionDetector(this)
    }

    private suspend fun seedGalleryHashes() {
        val added = galleryHashStore.seedFromGalleryIfNeeded(sceneScorer)
        if (added > 0) {
            lifeLogger.logEvent("Primed scenic dedup from $added gallery images")
        }
    }

    private suspend fun audioLoop() {
        Log.d(TAG, "Audio loop started")
        if (!vad.isReady()) {
            Log.w(TAG, "VAD model not loaded; using amplitude detection fallback")
        }

        val audioRecord = AudioRecordHelper.create() ?: run {
            Log.e(TAG, "Could not create AudioRecord")
            return
        }

        try {
            audioRecord.startRecording()
            val buffer = ShortArray(AudioRecordHelper.FRAME_SIZE)

            while (isActive) {
                val read = audioRecord.read(buffer, 0, buffer.size)
                if (read <= 0) continue

                val floatAudio = buffer
                    .take(read)
                    .map { it / 32768f }
                    .toFloatArray()

                processAudioFrame(floatAudio)
                frameCount++
            }
        } finally {
            try {
                audioRecord.stop()
            } catch (_: Exception) {
            }
            audioRecord.release()
        }
    }

    private suspend fun processAudioFrame(audio: FloatArray) {
        emotionDetector.analyzeFrame(audio)

        val speechProb = if (vad.isReady()) {
            vad.process(audio)
        } else {
            val rms = kotlin.math.sqrt(audio.map { it * it }.average()).toFloat()
            when {
                rms > 0.05f -> 1.0f
                rms > 0.02f -> 0.6f
                else -> 0.0f
            }
        }

        if (speechProb > 0.75f) {
            speechFrameCount++
            silenceFrameCount = 0
            meetingBuffer.add(audio.copyOf())

            if (!inConversation && speechFrameCount >= CONVERSATION_START_FRAMES) {
                inConversation = true
                Log.d(TAG, "Conversation detected; silencing phone")
                withContext(Dispatchers.Main) {
                    silentMode.enable()
                    updateNotification("Conversation detected - phone silenced")
                }
                lifeLogger.logEvent("Conversation detected; phone set to silent")
            }
        } else {
            silenceFrameCount++
            speechFrameCount = (speechFrameCount - 1).coerceAtLeast(0)

            if (inConversation && silenceFrameCount > SILENCE_THRESHOLD_FRAMES) {
                inConversation = false
                silenceFrameCount = 0
                speechFrameCount = 0
                Log.d(TAG, "Conversation ended; restoring ringer")
                withContext(Dispatchers.Main) {
                    silentMode.disable()
                    updateNotification("Watching and listening...")
                }

                if (meetingBuffer.size > 200) {
                    saveMeetingNotes()
                }
                meetingBuffer.clear()
                lifeLogger.logEvent("Conversation ended; phone restored")
            }
        }

        if (frameCount % 300 == 0L) {
            Log.d(
                TAG,
                "Periodic check: speech=$speechProb mood=${emotionDetector.getCurrentMood()}"
            )
        }
    }

    private suspend fun cameraLoop() {
        Log.d(TAG, "Camera loop started")
        delay(4_000)

        while (isActive) {
            delay(CAMERA_CHECK_INTERVAL_MS)

            if (!capturePhoto.isReady()) {
                capturePhoto.initCamera()
                continue
            }

            if (inConversation || agentState == State.SLEEPING) {
                continue
            }

            evaluateSceneAndMaybeCapture()
        }
    }

    private suspend fun evaluateSceneAndMaybeCapture() {
        val now = System.currentTimeMillis()
        if (now - lastAutoCaptureAt < MIN_CAPTURE_GAP_MS) return

        val bitmap = capturePhoto.captureFrame() ?: return
        try {
            val assessment = sceneScorer.assess(bitmap)
            val hash = sceneScorer.computeHash(bitmap)
            val isNew = galleryHashStore.isNew(hash)

            Log.d(
                TAG,
                "Scene check: score=${assessment.overallScore.format()} new=$isNew sharp=${assessment.sharpness.format()}"
            )

            if (!sceneScorer.isGoodScene(assessment) || !isNew) {
                return
            }

            val uri = capturePhoto.saveBitmap(bitmap) ?: return
            galleryHashStore.save(hash)
            lastAutoCaptureAt = now

            lifeLogger.logPhoto(
                uri,
                "Auto-captured scenic photo score=${assessment.overallScore.format()}"
            )

            withContext(Dispatchers.Main) {
                updateNotification("Saved a new scenic photo")
            }
        } finally {
            bitmap.recycle()
        }
    }

    private fun saveMeetingNotes() {
        Log.d(TAG, "Meeting-like conversation recorded (${meetingBuffer.size} frames)")
        lifeLogger.logMeeting("Conversation detected and stored locally")
    }

    fun onWakeWordDetected() {
        if (agentState != State.IDLE) return
        agentState = State.LISTENING
        updateNotification("Listening...")
    }

    private suspend fun statusLoop() {
        while (isActive) {
            delay(30_000)
            updateNotification(currentStatus())
        }
    }

    private fun currentStatus(): String {
        return when {
            inConversation -> "Conversation detected - phone silenced"
            else -> when (agentState) {
                State.IDLE -> "Watching and listening..."
                State.LISTENING -> "Listening..."
                State.THINKING -> "Thinking..."
                State.SPEAKING -> "Speaking..."
                State.SLEEPING -> "Sleep mode active"
            }
        }
    }

    private fun buildNotification(status: String): Notification {
        val intent = PendingIntent.getActivity(
            this,
            0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(this, NovaApp.CHANNEL_AGENT)
            .setContentTitle("Nova Agent")
            .setContentText(status)
            .setSmallIcon(R.drawable.ic_nova)
            .setContentIntent(intent)
            .setOngoing(true)
            .setSilent(true)
            .build()
    }

    private fun updateNotification(status: String) {
        val manager = getSystemService(NOTIFICATION_SERVICE) as NotificationManager
        manager.notify(NOTIF_ID, buildNotification(status))
    }

    override fun onDestroy() {
        super.onDestroy()
        serviceJob?.cancel()
        instance = null
        if (::vad.isInitialized) vad.release()
        if (::tts.isInitialized) tts.shutdown()
        if (::capturePhoto.isInitialized) capturePhoto.release()
        Log.d(TAG, "AgentService destroyed")
    }

    private fun Float.format(): String = String.format(Locale.US, "%.2f", this)
}

package com.nova.agent.actions

import android.content.Context
import android.speech.tts.TextToSpeech
import android.util.Log
import java.util.Locale

/**
 * Text-to-speech output for Nova's voice replies.
 *
 * Phase 1: Uses Android's built-in TTS engine (works immediately).
 * Phase 2: Replace with Piper TTS for much better voice quality.
 *          Download from: https://github.com/rhasspy/piper
 *          Model: en_US-amy-medium.onnx (~50MB)
 */
class SpeakReplyAction(private val context: Context) : TextToSpeech.OnInitListener {

    private val TAG = "NovaTTS"
    private var tts: TextToSpeech? = null
    private var isReady = false
    private val pendingQueue = mutableListOf<String>()

    init {
        tts = TextToSpeech(context, this)
    }

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            tts?.language = Locale.US
            tts?.setSpeechRate(1.0f)
            tts?.setPitch(1.0f)
            isReady = true
            Log.d(TAG, "TTS ready")

            // Speak anything that was queued before init
            pendingQueue.forEach { speak(it) }
            pendingQueue.clear()
        } else {
            Log.e(TAG, "TTS init failed with status $status")
        }
    }

    fun speak(text: String) {
        if (!isReady) {
            pendingQueue.add(text)
            return
        }
        Log.d(TAG, "Speaking: $text")
        tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "nova_${System.currentTimeMillis()}")
    }

    fun speakQueued(text: String) {
        if (!isReady) {
            pendingQueue.add(text)
            return
        }
        tts?.speak(text, TextToSpeech.QUEUE_ADD, null, "nova_${System.currentTimeMillis()}")
    }

    fun stop() {
        tts?.stop()
    }

    fun isSpeaking() = tts?.isSpeaking == true

    fun shutdown() {
        tts?.stop()
        tts?.shutdown()
        tts = null
    }
}

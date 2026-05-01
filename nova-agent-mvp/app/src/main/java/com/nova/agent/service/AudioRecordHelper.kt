package com.nova.agent.service

import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.util.Log

object AudioRecordHelper {

    private const val TAG = "AudioRecordHelper"

    // Silero VAD expects 16kHz, 16-bit, mono, 512 samples (~32ms frames)
    const val SAMPLE_RATE = 16000
    const val FRAME_SIZE = 512
    const val CHANNEL = AudioFormat.CHANNEL_IN_MONO
    const val FORMAT = AudioFormat.ENCODING_PCM_16BIT

    fun create(): AudioRecord? {
        val minBuffer = AudioRecord.getMinBufferSize(SAMPLE_RATE, CHANNEL, FORMAT)
        if (minBuffer == AudioRecord.ERROR || minBuffer == AudioRecord.ERROR_BAD_VALUE) {
            Log.e(TAG, "Invalid buffer size: $minBuffer")
            return null
        }

        val bufferSize = maxOf(minBuffer, FRAME_SIZE * 2)

        return try {
            val record = AudioRecord(
                MediaRecorder.AudioSource.VOICE_RECOGNITION,
                SAMPLE_RATE,
                CHANNEL,
                FORMAT,
                bufferSize
            )
            if (record.state != AudioRecord.STATE_INITIALIZED) {
                Log.e(TAG, "AudioRecord failed to initialize")
                record.release()
                null
            } else {
                record
            }
        } catch (e: SecurityException) {
            Log.e(TAG, "Microphone permission denied: ${e.message}")
            null
        }
    }
}

package com.nova.agent.perception

import android.content.Context
import android.util.Log
import com.nova.agent.service.AgentService

/**
 * Wake word detection using Picovoice Porcupine.
 *
 * Setup:
 * 1. Get a FREE API key at https://console.picovoice.ai/
 * 2. Replace "YOUR_PICOVOICE_KEY_HERE" below with your key
 * 3. Optionally train a custom wake word at the Picovoice console
 *    and add the .ppn file to assets/models/
 */
class WakeWordDetector(
    private val context: Context,
    private val onWakeWord: () -> Unit
) {
    private val TAG = "NovaWakeWord"

    // ── REPLACE THIS WITH YOUR FREE KEY FROM console.picovoice.ai ──
    private val PICOVOICE_KEY = "YOUR_PICOVOICE_KEY_HERE"

    private var porcupine: Any? = null // ai.picovoice.porcupine.Porcupine
    private var isInitialized = false

    init {
        initialize()
    }

    private fun initialize() {
        if (PICOVOICE_KEY == "YOUR_PICOVOICE_KEY_HERE") {
            Log.w(TAG, "Porcupine key not set — wake word disabled. Add your key to WakeWordDetector.kt")
            return
        }

        try {
            // Porcupine initialization — uses built-in "Hey Siri"-style "Hi" keyword
            // Uncomment once key is set:
            //
            // porcupine = Porcupine.Builder()
            //     .setAccessKey(PICOVOICE_KEY)
            //     .setKeyword(Porcupine.BuiltInKeyword.HEY_SIRI) // or ALEXA, JARVIS, etc.
            //     .build(context)
            // isInitialized = true
            // Log.d(TAG, "Porcupine wake word detector ready")

            Log.d(TAG, "Porcupine ready to initialize — add your key first")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to init Porcupine: ${e.message}")
        }
    }

    /**
     * Process a 512-sample audio frame.
     * Returns true if wake word was detected.
     */
    fun process(audioFrame: ShortArray): Boolean {
        if (!isInitialized) return false

        return try {
            // val result = (porcupine as ai.picovoice.porcupine.Porcupine).process(audioFrame)
            // if (result >= 0) {
            //     Log.d(TAG, "Wake word detected!")
            //     onWakeWord()
            //     true
            // } else false
            false
        } catch (e: Exception) {
            Log.e(TAG, "Porcupine processing error: ${e.message}")
            false
        }
    }

    fun release() {
        try {
            // (porcupine as? ai.picovoice.porcupine.Porcupine)?.delete()
        } catch (e: Exception) {
            Log.e(TAG, "Error releasing Porcupine: ${e.message}")
        }
    }
}

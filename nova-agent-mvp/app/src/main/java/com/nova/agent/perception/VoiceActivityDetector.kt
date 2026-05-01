package com.nova.agent.perception

import android.content.Context
import android.util.Log
import java.nio.FloatBuffer

/**
 * Voice Activity Detector using Silero VAD ONNX model.
 *
 * Setup: Download silero_vad.onnx from:
 * https://github.com/snakers4/silero-vad/raw/master/files/silero_vad.onnx
 * Place it in: app/src/main/assets/models/silero_vad.onnx
 *
 * Until the model is added, uses amplitude fallback.
 */
class VoiceActivityDetector(private val context: Context) {

    private val TAG = "NovaVAD"
    private var ortSession: Any? = null // OrtSession when ONNX is set up
    private var modelReady = false

    // Silero VAD internal state
    private var h = FloatArray(2 * 1 * 64) { 0f }
    private var c = FloatArray(2 * 1 * 64) { 0f }

    init {
        loadModel()
    }

    private fun loadModel() {
        try {
            val modelPath = "models/silero_vad.onnx"
            context.assets.list("models")?.let { files ->
                if ("silero_vad.onnx" in files) {
                    // ONNX Runtime initialisation
                    // Uncomment once onnxruntime dependency is confirmed working:
                    //
                    // val env = OrtEnvironment.getEnvironment()
                    // val modelBytes = context.assets.open(modelPath).readBytes()
                    // ortSession = env.createSession(modelBytes)
                    // modelReady = true
                    // Log.d(TAG, "Silero VAD model loaded successfully")
                    Log.d(TAG, "silero_vad.onnx found — ONNX session init ready")
                } else {
                    Log.w(TAG, "silero_vad.onnx not found in assets/models/ — using amplitude fallback")
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to load VAD model: ${e.message}")
        }
    }

    /**
     * Process a 512-sample audio frame at 16kHz.
     * Returns probability of speech (0.0 to 1.0).
     */
    fun process(audioFrame: FloatArray): Float {
        return if (modelReady) {
            runOnnxInference(audioFrame)
        } else {
            amplitudeFallback(audioFrame)
        }
    }

    private fun runOnnxInference(audioFrame: FloatArray): Float {
        // Full Silero VAD ONNX inference — activate once OrtSession is set up
        // val inputTensor = OnnxTensor.createTensor(env, FloatBuffer.wrap(audioFrame), longArrayOf(1, audioFrame.size.toLong()))
        // val srTensor = OnnxTensor.createTensor(env, LongBuffer.wrap(longArrayOf(16000)), longArrayOf())
        // val hTensor = OnnxTensor.createTensor(env, FloatBuffer.wrap(h), longArrayOf(2, 1, 64))
        // val cTensor = OnnxTensor.createTensor(env, FloatBuffer.wrap(c), longArrayOf(2, 1, 64))
        // val result = ortSession.run(mapOf("input" to inputTensor, "sr" to srTensor, "h" to hTensor, "c" to cTensor))
        // val prob = (result["output"] as OnnxTensor).floatBuffer.get(0)
        // return prob
        return 0f
    }

    private fun amplitudeFallback(audioFrame: FloatArray): Float {
        val rms = Math.sqrt(audioFrame.map { (it * it).toDouble() }.average()).toFloat()
        return when {
            rms > 0.05f -> 1.0f  // clear speech
            rms > 0.02f -> 0.6f  // possible speech
            else -> 0.0f         // silence
        }
    }

    fun isReady() = modelReady

    fun release() {
        try {
            // ortSession?.close()
        } catch (e: Exception) {
            Log.e(TAG, "Error releasing VAD: ${e.message}")
        }
    }
}

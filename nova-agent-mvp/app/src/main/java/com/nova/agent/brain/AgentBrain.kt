package com.nova.agent.brain

import android.content.Context
import android.util.Log
import com.nova.agent.perception.Mood
import org.json.JSONObject

/**
 * Nova's AI brain — interfaces with the on-device LLM.
 *
 * Phase 1: Uses a rule-based system (no LLM needed, works immediately).
 * Phase 2: Plug in Phi-3 mini or Gemma 2B via MediaPipe LLM Inference API.
 *
 * To activate LLM (Phase 2):
 * 1. Add to build.gradle: implementation("com.google.mediapipe:tasks-genai:0.10.14")
 * 2. Download Phi-3 mini INT8 (~2.2GB) from HuggingFace
 * 3. Place in internal storage, update modelPath below
 * 4. Uncomment the MediaPipe code
 */
class AgentBrain(private val context: Context) {

    private val TAG = "NovaBrain"
    private var llmReady = false

    // Model path — user downloads this separately due to size
    private val MODEL_PATH = "/sdcard/nova_models/phi3-mini-q8.bin"

    init {
        tryInitLLM()
    }

    private fun tryInitLLM() {
        try {
            val modelFile = java.io.File(MODEL_PATH)
            if (modelFile.exists()) {
                // MediaPipe LLM init:
                // val options = LlmInference.LlmInferenceOptions.builder()
                //     .setModelPath(MODEL_PATH)
                //     .setMaxTokens(512)
                //     .setTemperature(0.7f)
                //     .build()
                // llm = LlmInference.createFromOptions(context, options)
                // llmReady = true
                Log.d(TAG, "LLM model found at $MODEL_PATH — ready to activate")
            } else {
                Log.w(TAG, "LLM model not found — using rule-based fallback")
                Log.w(TAG, "Download Phi-3 mini from HuggingFace and place at $MODEL_PATH")
            }
        } catch (e: Exception) {
            Log.e(TAG, "LLM init failed: ${e.message}")
        }
    }

    /**
     * Generate a response to the user's voice query.
     * Returns JSON: {"action": "...", "reply": "..."}
     */
    suspend fun generate(context: BrainContext): BrainResponse {
        return if (llmReady) {
            generateWithLLM(context)
        } else {
            generateWithRules(context)
        }
    }

    private suspend fun generateWithLLM(ctx: BrainContext): BrainResponse {
        val prompt = buildPrompt(ctx)
        Log.d(TAG, "LLM prompt: $prompt")

        // val response = llm.generateResponse(prompt)
        // return parseResponse(response)

        return BrainResponse("none", "LLM is configured but not yet activated.", emptyMap())
    }

    /**
     * Rule-based fallback — handles common commands without an LLM.
     * This works immediately with no model needed.
     */
    private fun generateWithRules(ctx: BrainContext): BrainResponse {
        val query = ctx.userText.lowercase().trim()
        Log.d(TAG, "Rule-based processing: $query")

        return when {
            query.contains("silent") || query.contains("silence") || query.contains("quiet") ->
                BrainResponse("silence", "Done, I've silenced your phone.", emptyMap())

            query.contains("unsilent") || query.contains("sound on") || query.contains("ringer on") ->
                BrainResponse("unsilence", "Ringer is back on.", emptyMap())

            query.contains("photo") || query.contains("picture") || query.contains("capture") ->
                BrainResponse("take_photo", "Taking a photo now.", emptyMap())

            query.contains("time") ->
                BrainResponse("none", "It's ${java.text.SimpleDateFormat("h:mm a", java.util.Locale.US).format(java.util.Date())}.", emptyMap())

            query.contains("how are you") || query.contains("you doing") ->
                BrainResponse("none", "I'm running perfectly, always watching out for you.", emptyMap())

            query.contains("hello") || query.contains("hi") || query.contains("hey") ->
                BrainResponse("none", "Hey! I'm Nova. How can I help?", emptyMap())

            query.contains("stop") || query.contains("goodbye") || query.contains("bye") ->
                BrainResponse("none", "Okay, going quiet. I'm still here if you need me.", emptyMap())

            else ->
                BrainResponse("none", "I heard you, but I need a smarter brain to answer that. Add the Phi-3 model to unlock full AI responses.", emptyMap())
        }
    }

    private fun buildPrompt(ctx: BrainContext): String = """
You are Nova, an always-on AI agent on this phone.

CONTEXT:
- Time: ${ctx.currentTime}
- Mood: ${ctx.mood}
- Phone silent: ${ctx.isSilent}
- Recent events: ${ctx.recentEvents.joinToString(", ")}

USER SAID: "${ctx.userText}"

Respond ONLY as JSON with no extra text:
{"action": "none|silence|unsilence|take_photo|recall_memory", "reply": "your spoken reply"}
    """.trimIndent()

    private fun parseResponse(raw: String): BrainResponse {
        return try {
            val json = JSONObject(raw.trim())
            BrainResponse(
                action = json.optString("action", "none"),
                reply = json.optString("reply", "I'm not sure how to respond to that."),
                data = emptyMap()
            )
        } catch (e: Exception) {
            Log.e(TAG, "Failed to parse LLM response: $raw")
            BrainResponse("none", raw.take(200), emptyMap())
        }
    }

    fun summarize(transcript: String): String {
        // Will use LLM to summarize meeting transcripts
        return "Meeting recorded: ${transcript.take(100)}..."
    }

    fun draftReply(message: String, from: String): String {
        // Will use LLM to draft contextual replies
        return "Thanks for your message, I'll get back to you soon."
    }
}

data class BrainContext(
    val userText: String,
    val currentTime: String,
    val mood: Mood,
    val isSilent: Boolean,
    val recentEvents: List<String>
)

data class BrainResponse(
    val action: String,
    val reply: String,
    val data: Map<String, String>
)

package com.nova.agent.memory

import android.content.Context
import android.content.SharedPreferences
import android.util.Log
import org.json.JSONArray
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Nova's life logging system.
 * Stores a searchable diary of events, conversations, and observations.
 *
 * Phase 1: Uses SharedPreferences (simple, works immediately).
 * Phase 2: Migrate to Room database for full-text search.
 */
class LifeLogger(context: Context) {

    private val TAG = "NovaLifeLogger"
    private val prefs: SharedPreferences =
        context.getSharedPreferences("nova_life_log", Context.MODE_PRIVATE)
    private val dateFormat = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.US)

    data class LogEntry(
        val timestamp: String,
        val type: String,
        val content: String
    )

    // ── Write operations ──────────────────────────────────────────

    fun logEvent(description: String) {
        saveEntry(LogEntry(now(), "event", description))
        Log.d(TAG, "Event logged: $description")
    }

    fun logConversation(summary: String) {
        saveEntry(LogEntry(now(), "conversation", summary))
    }

    fun logMeeting(summary: String) {
        saveEntry(LogEntry(now(), "meeting", summary))
        Log.d(TAG, "Meeting logged: ${summary.take(80)}")
    }

    fun logPhoto(path: String, description: String = "") {
        saveEntry(LogEntry(now(), "photo", "$path — $description"))
    }

    fun logFaceSeen(personName: String) {
        saveEntry(LogEntry(now(), "face", "Saw: $personName"))
    }

    fun logMood(mood: String) {
        saveEntry(LogEntry(now(), "mood", mood))
    }

    // ── Read operations ───────────────────────────────────────────

    fun recentSummaries(count: Int = 5): List<String> {
        return getAllEntries()
            .takeLast(count)
            .map { "[${it.timestamp}] ${it.type}: ${it.content}" }
    }

    fun search(query: String): String {
        val results = getAllEntries()
            .filter { it.content.contains(query, ignoreCase = true) }
            .takeLast(5)

        return if (results.isEmpty()) {
            "I don't have any memories matching '$query'."
        } else {
            results.joinToString("\n") { "${it.timestamp}: ${it.content}" }
        }
    }

    fun getTodaysSummary(): String {
        val today = SimpleDateFormat("yyyy-MM-dd", Locale.US).format(Date())
        val todayEntries = getAllEntries().filter { it.timestamp.startsWith(today) }
        return if (todayEntries.isEmpty()) {
            "Nothing logged today yet."
        } else {
            "Today: ${todayEntries.size} events. Last: ${todayEntries.last().content.take(60)}"
        }
    }

    // ── Internal storage ──────────────────────────────────────────

    private fun saveEntry(entry: LogEntry) {
        val all = getRawJson()
        val obj = JSONObject().apply {
            put("ts", entry.timestamp)
            put("type", entry.type)
            put("content", entry.content)
        }
        all.put(obj)

        // Keep only last 500 entries to avoid bloat
        val trimmed = if (all.length() > 500) {
            val newArr = JSONArray()
            for (i in (all.length() - 500) until all.length()) {
                newArr.put(all.get(i))
            }
            newArr
        } else all

        prefs.edit().putString("entries", trimmed.toString()).apply()
    }

    private fun getAllEntries(): List<LogEntry> {
        return try {
            val arr = getRawJson()
            (0 until arr.length()).map { i ->
                val obj = arr.getJSONObject(i)
                LogEntry(
                    timestamp = obj.getString("ts"),
                    type = obj.getString("type"),
                    content = obj.getString("content")
                )
            }
        } catch (e: Exception) {
            emptyList()
        }
    }

    private fun getRawJson(): JSONArray {
        val raw = prefs.getString("entries", "[]") ?: "[]"
        return try { JSONArray(raw) } catch (e: Exception) { JSONArray() }
    }

    private fun now() = dateFormat.format(Date())

    fun clearAll() {
        prefs.edit().remove("entries").apply()
        Log.d(TAG, "Life log cleared")
    }
}

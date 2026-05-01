package com.nova.agent.memory

import android.content.Context
import android.content.SharedPreferences
import com.nova.agent.perception.Mood
import org.json.JSONArray
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class MoodHistory(context: Context) {

    private val prefs: SharedPreferences =
        context.getSharedPreferences("nova_mood", Context.MODE_PRIVATE)
    private val fmt = SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.US)

    fun record(mood: Mood) {
        val arr = getAll()
        arr.put(JSONObject().apply {
            put("ts", fmt.format(Date()))
            put("mood", mood.name)
        })
        // Keep last 200 entries
        val trimmed = JSONArray()
        val start = if (arr.length() > 200) arr.length() - 200 else 0
        for (i in start until arr.length()) trimmed.put(arr.get(i))
        prefs.edit().putString("moods", trimmed.toString()).apply()
    }

    fun latest(): Mood {
        val arr = getAll()
        if (arr.length() == 0) return Mood.NEUTRAL
        return try {
            Mood.valueOf(arr.getJSONObject(arr.length() - 1).getString("mood"))
        } catch (e: Exception) { Mood.NEUTRAL }
    }

    fun todayDominant(): Mood {
        val today = SimpleDateFormat("yyyy-MM-dd", Locale.US).format(Date())
        val todayMoods = (0 until getAll().length())
            .map { getAll().getJSONObject(it) }
            .filter { it.getString("ts").startsWith(today) }
            .map { it.getString("mood") }

        if (todayMoods.isEmpty()) return Mood.NEUTRAL
        return Mood.valueOf(todayMoods.groupingBy { it }.eachCount().maxByOrNull { it.value }!!.key)
    }

    private fun getAll(): JSONArray {
        val raw = prefs.getString("moods", "[]") ?: "[]"
        return try { JSONArray(raw) } catch (e: Exception) { JSONArray() }
    }
}

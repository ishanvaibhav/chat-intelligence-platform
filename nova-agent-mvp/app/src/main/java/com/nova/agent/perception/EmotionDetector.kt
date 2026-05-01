package com.nova.agent.perception

import android.content.Context

enum class Mood { HAPPY, NEUTRAL, STRESSED, TIRED, UNKNOWN }

/**
 * Lightweight local mood estimation from voice energy and pitch trends.
 */
class EmotionDetector(@Suppress("unused") private val context: Context) {

    private val energyHistory = ArrayDeque<Float>()
    private val pitchHistory = ArrayDeque<Float>()

    private fun <T> ArrayDeque<T>.addCapped(item: T, maxSize: Int) {
        if (size >= maxSize) removeFirst()
        addLast(item)
    }

    fun analyzeFrame(audioFrame: FloatArray) {
        val energy = audioFrame.map { it * it }.average().toFloat()
        val zeroCrossings = audioFrame.zipWithNext().count { (a, b) -> (a < 0) != (b < 0) }
        val pitchEstimate = zeroCrossings.toFloat() / audioFrame.size * 16000f / 2f

        energyHistory.addCapped(energy, 120)
        pitchHistory.addCapped(pitchEstimate, 120)
    }

    fun getCurrentMood(): Mood {
        if (energyHistory.size < 10) return Mood.UNKNOWN

        val avgEnergy = energyHistory.average()
        val energyVariance = energyHistory
            .map { (it - avgEnergy) * (it - avgEnergy) }
            .average()
        val avgPitch = pitchHistory.average()

        return when {
            avgEnergy > 0.08 && energyVariance > 0.005 -> Mood.STRESSED
            avgEnergy < 0.01 -> Mood.TIRED
            avgPitch > 200 && avgEnergy > 0.04 -> Mood.HAPPY
            else -> Mood.NEUTRAL
        }
    }
}

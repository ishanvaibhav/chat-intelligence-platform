package com.nova.agent.perception

import android.content.Context
import android.graphics.Bitmap
import android.util.Log
import kotlin.math.abs
import kotlin.math.pow
import kotlin.math.sqrt

data class SceneAssessment(
    val overallScore: Float,
    val brightness: Float,
    val contrast: Float,
    val sharpness: Float,
    val colorfulness: Float
)

/**
 * Scores candidate frames locally.
 *
 * Phase 1 uses fast heuristics so the feature works immediately with no model download.
 * A future NIMA/TFLite model can be blended into the same API later.
 */
class SceneQualityScorer(private val context: Context) {

    private val tag = "NovaSceneScorer"
    private var modelReady = false
    private val qualityThreshold = 0.62f

    init {
        loadModel()
    }

    private fun loadModel() {
        try {
            context.assets.list("models")?.let { files ->
                if ("nima_scene.tflite" in files) {
                    Log.d(tag, "NIMA model found; heuristic scorer stays active until integrated")
                } else {
                    Log.d(tag, "No NIMA model found; using built-in heuristic scorer")
                }
            }
        } catch (e: Exception) {
            Log.w(tag, "Model probe failed: ${e.message}")
        }
    }

    fun assess(bitmap: Bitmap): SceneAssessment {
        return if (modelReady) {
            heuristicAssess(bitmap)
        } else {
            heuristicAssess(bitmap)
        }
    }

    fun score(bitmap: Bitmap): Float = assess(bitmap).overallScore

    fun isGoodScene(assessment: SceneAssessment): Boolean {
        return assessment.overallScore >= qualityThreshold &&
            assessment.sharpness >= 0.18f &&
            assessment.brightness >= 0.22f
    }

    fun computeHash(bitmap: Bitmap): Long {
        val small = Bitmap.createScaledBitmap(bitmap, 8, 8, true)
        val pixels = IntArray(64)
        small.getPixels(pixels, 0, 8, 0, 0, 8, 8)
        if (small != bitmap) small.recycle()

        val grays = pixels.map { px ->
            val r = (px shr 16) and 0xFF
            val g = (px shr 8) and 0xFF
            val b = px and 0xFF
            (0.299 * r + 0.587 * g + 0.114 * b).toInt()
        }
        val mean = grays.average()

        var hash = 0L
        grays.forEachIndexed { index, value ->
            if (value > mean) {
                hash = hash or (1L shl index)
            }
        }
        return hash
    }

    private fun heuristicAssess(bitmap: Bitmap): SceneAssessment {
        val scaled = Bitmap.createScaledBitmap(bitmap, 96, 96, true)
        val width = scaled.width
        val height = scaled.height
        val pixels = IntArray(width * height)
        scaled.getPixels(pixels, 0, width, 0, 0, width, height)
        if (scaled != bitmap) scaled.recycle()

        val luma = FloatArray(pixels.size)
        var totalBrightness = 0f
        var totalSaturation = 0f

        pixels.forEachIndexed { index, pixel ->
            val r = ((pixel shr 16) and 0xFF).toFloat()
            val g = ((pixel shr 8) and 0xFF).toFloat()
            val b = (pixel and 0xFF).toFloat()
            val maxChannel = maxOf(r, g, b)
            val minChannel = minOf(r, g, b)
            val luminance = (0.299f * r) + (0.587f * g) + (0.114f * b)
            luma[index] = luminance
            totalBrightness += luminance
            if (maxChannel > 0f) {
                totalSaturation += (maxChannel - minChannel) / maxChannel
            }
        }

        val averageBrightness = (totalBrightness / pixels.size) / 255f
        val brightnessScore = (1f - (abs(averageBrightness - 0.55f) / 0.55f))
            .coerceIn(0f, 1f)

        val meanLuma = luma.average().toFloat()
        val contrastStdDev = sqrt(
            luma.fold(0.0) { acc, value ->
                acc + (value - meanLuma).pow(2)
            } / luma.size
        ).toFloat()
        val contrastScore = (contrastStdDev / 64f).coerceIn(0f, 1f)

        var edgeEnergy = 0f
        var edgeCount = 0
        for (y in 0 until height - 1) {
            for (x in 0 until width - 1) {
                val index = y * width + x
                val dx = abs(luma[index] - luma[index + 1])
                val dy = abs(luma[index] - luma[index + width])
                edgeEnergy += dx + dy
                edgeCount += 2
            }
        }
        val sharpnessScore = ((edgeEnergy / edgeCount.coerceAtLeast(1)) / 36f)
            .coerceIn(0f, 1f)

        val colorfulnessScore = ((totalSaturation / pixels.size) / 0.65f)
            .coerceIn(0f, 1f)

        var overall = (
            (0.32f * brightnessScore) +
                (0.24f * contrastScore) +
                (0.28f * sharpnessScore) +
                (0.16f * colorfulnessScore)
            )

        if (averageBrightness < 0.12f || averageBrightness > 0.96f) {
            overall *= 0.35f
        }

        return SceneAssessment(
            overallScore = overall.coerceIn(0f, 1f),
            brightness = brightnessScore,
            contrast = contrastScore,
            sharpness = sharpnessScore,
            colorfulness = colorfulnessScore
        )
    }
}

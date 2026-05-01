package com.nova.agent.memory

import android.Manifest
import android.content.ContentUris
import android.content.Context
import android.content.SharedPreferences
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.ImageDecoder
import android.net.Uri
import android.os.Build
import android.provider.MediaStore
import android.util.Log
import androidx.core.content.ContextCompat
import com.nova.agent.perception.SceneQualityScorer
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * Stores perceptual hashes for gallery images and app-captured photos.
 * This lets Nova avoid saving the same scenic shot again and again.
 */
class GalleryHashStore(private val context: Context) {

    private val tag = "NovaGalleryStore"
    private val prefs: SharedPreferences =
        context.getSharedPreferences("nova_hashes", Context.MODE_PRIVATE)
    private val cachedHashes = linkedSetOf<Long>()

    init {
        loadFromPrefs()
    }

    fun isNew(hash: Long): Boolean {
        for (seen in cachedHashes) {
            val hammingDistance = java.lang.Long.bitCount(hash xor seen)
            if (hammingDistance < HASH_DISTANCE_THRESHOLD) {
                Log.d(tag, "Scene already known (distance=$hammingDistance)")
                return false
            }
        }
        return true
    }

    fun save(hash: Long) {
        cachedHashes.add(hash)
        persistToPrefs()
        Log.d(tag, "Hash saved. Total stored: ${cachedHashes.size}")
    }

    fun count() = cachedHashes.size

    suspend fun seedFromGalleryIfNeeded(
        scorer: SceneQualityScorer,
        maxImages: Int = 150
    ): Int = withContext(Dispatchers.IO) {
        if (!hasGalleryPermission()) {
            Log.w(tag, "Gallery permission missing; skipping dedup seed")
            return@withContext 0
        }

        val lastSync = prefs.getLong(KEY_LAST_SYNC, 0L)
        val now = System.currentTimeMillis()
        if (lastSync > 0L && now - lastSync < RESCAN_INTERVAL_MS) {
            return@withContext 0
        }

        val before = cachedHashes.size
        val projection = arrayOf(MediaStore.Images.Media._ID)
        val sortOrder = "${MediaStore.Images.Media.DATE_ADDED} DESC"

        context.contentResolver.query(
            MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
            projection,
            null,
            null,
            sortOrder
        )?.use { cursor ->
            val idColumn = cursor.getColumnIndexOrThrow(MediaStore.Images.Media._ID)
            var scanned = 0
            while (cursor.moveToNext() && scanned < maxImages) {
                val id = cursor.getLong(idColumn)
                val uri = ContentUris.withAppendedId(
                    MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
                    id
                )

                decodeTinyBitmap(uri)?.let { bitmap ->
                    try {
                        cachedHashes.add(scorer.computeHash(bitmap))
                    } catch (e: Exception) {
                        Log.w(tag, "Skipping gallery image $uri: ${e.message}")
                    } finally {
                        bitmap.recycle()
                    }
                }
                scanned++
            }
        }

        persistToPrefs()
        prefs.edit().putLong(KEY_LAST_SYNC, now).apply()
        val added = cachedHashes.size - before
        Log.d(tag, "Seeded $added gallery hashes")
        return@withContext added
    }

    fun clearAll() {
        cachedHashes.clear()
        prefs.edit()
            .remove(KEY_HASHES)
            .remove(KEY_LAST_SYNC)
            .apply()
    }

    private fun hasGalleryPermission(): Boolean {
        val permission = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            Manifest.permission.READ_MEDIA_IMAGES
        } else {
            Manifest.permission.READ_EXTERNAL_STORAGE
        }

        return ContextCompat.checkSelfPermission(
            context,
            permission
        ) == PackageManager.PERMISSION_GRANTED
    }

    private fun decodeTinyBitmap(uri: Uri): Bitmap? {
        return try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                val source = ImageDecoder.createSource(context.contentResolver, uri)
                ImageDecoder.decodeBitmap(source) { decoder, info, _ ->
                    val maxDimension = maxOf(info.size.width, info.size.height).coerceAtLeast(1)
                    decoder.setTargetSampleSize((maxDimension / 96).coerceAtLeast(1))
                    decoder.isMutableRequired = false
                }
            } else {
                val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
                context.contentResolver.openInputStream(uri)?.use { stream ->
                    BitmapFactory.decodeStream(stream, null, bounds)
                }

                val decodeOptions = BitmapFactory.Options().apply {
                    inSampleSize = calculateInSampleSize(bounds, 96, 96)
                }

                context.contentResolver.openInputStream(uri)?.use { stream ->
                    BitmapFactory.decodeStream(stream, null, decodeOptions)
                }
            }
        } catch (e: Exception) {
            Log.w(tag, "Failed to decode gallery image $uri: ${e.message}")
            null
        }
    }

    private fun calculateInSampleSize(
        options: BitmapFactory.Options,
        reqWidth: Int,
        reqHeight: Int
    ): Int {
        val (height, width) = options.outHeight to options.outWidth
        var inSampleSize = 1

        if (height > reqHeight || width > reqWidth) {
            while ((height / (inSampleSize * 2)) >= reqHeight &&
                (width / (inSampleSize * 2)) >= reqWidth
            ) {
                inSampleSize *= 2
            }
        }

        return inSampleSize.coerceAtLeast(1)
    }

    private fun loadFromPrefs() {
        val raw = prefs.getString(KEY_HASHES, "") ?: ""
        if (raw.isBlank()) return

        raw.split(",").forEach { value ->
            value.toLongOrNull()?.let(cachedHashes::add)
        }

        Log.d(tag, "Loaded ${cachedHashes.size} hashes from storage")
    }

    private fun persistToPrefs() {
        val toSave = cachedHashes.takeLast(MAX_HASH_COUNT)
        prefs.edit().putString(KEY_HASHES, toSave.joinToString(",")).apply()
    }

    companion object {
        private const val KEY_HASHES = "hashes"
        private const val KEY_LAST_SYNC = "gallery_seeded_at"
        private const val MAX_HASH_COUNT = 2000
        private const val HASH_DISTANCE_THRESHOLD = 10
        private const val RESCAN_INTERVAL_MS = 12L * 60L * 60L * 1000L
    }
}

package com.nova.agent.actions

import android.content.ContentValues
import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.ImageFormat
import android.graphics.Matrix
import android.graphics.Rect
import android.graphics.YuvImage
import android.os.Build
import android.provider.MediaStore
import android.util.Log
import android.util.Size
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.ImageProxy
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.core.content.ContextCompat
import androidx.lifecycle.LifecycleOwner
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import java.io.ByteArrayOutputStream
import java.util.Locale
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import kotlin.coroutines.resume

class CapturePhotoAction(
    private val context: Context,
    private val lifecycleOwner: LifecycleOwner
) {
    private val tag = "NovaCapturePhoto"
    private val cameraExecutor: ExecutorService = Executors.newSingleThreadExecutor()

    @Volatile
    private var imageCapture: ImageCapture? = null

    @Volatile
    private var cameraReady = false

    private var cameraProvider: ProcessCameraProvider? = null

    fun initCamera() {
        if (cameraReady) return

        val cameraProviderFuture = ProcessCameraProvider.getInstance(context)
        cameraProviderFuture.addListener({
            try {
                cameraProvider = cameraProviderFuture.get()
                val capture = ImageCapture.Builder()
                    .setCaptureMode(ImageCapture.CAPTURE_MODE_MINIMIZE_LATENCY)
                    .setTargetResolution(Size(1280, 720))
                    .build()

                cameraProvider?.unbindAll()
                cameraProvider?.bindToLifecycle(
                    lifecycleOwner,
                    CameraSelector.DEFAULT_BACK_CAMERA,
                    capture
                )

                imageCapture = capture
                cameraReady = true
                Log.d(tag, "Camera ready for scene checks")
            } catch (e: Exception) {
                cameraReady = false
                imageCapture = null
                Log.e(tag, "Camera bind failed: ${e.message}")
            }
        }, ContextCompat.getMainExecutor(context))
    }

    fun isReady(): Boolean = cameraReady && imageCapture != null

    suspend fun captureFrame(): Bitmap? = suspendCancellableCoroutine { continuation ->
        val capture = imageCapture
        if (!cameraReady || capture == null) {
            Log.w(tag, "Camera is not ready yet")
            continuation.resume(null)
            return@suspendCancellableCoroutine
        }

        capture.takePicture(
            cameraExecutor,
            object : ImageCapture.OnImageCapturedCallback() {
                override fun onCaptureSuccess(image: ImageProxy) {
                    val bitmap = try {
                        imageProxyToBitmap(image)
                    } catch (e: Exception) {
                        Log.e(tag, "Frame conversion failed: ${e.message}")
                        null
                    } finally {
                        image.close()
                    }

                    if (continuation.isActive) {
                        continuation.resume(bitmap)
                    } else {
                        bitmap?.recycle()
                    }
                }

                override fun onError(exception: ImageCaptureException) {
                    Log.e(tag, "Frame capture failed: ${exception.message}")
                    if (continuation.isActive) {
                        continuation.resume(null)
                    }
                }
            }
        )
    }

    suspend fun saveBitmap(bitmap: Bitmap): String? = withContext(Dispatchers.IO) {
        val timestamp = java.text.SimpleDateFormat(
            "yyyyMMdd_HHmmss",
            Locale.US
        ).format(System.currentTimeMillis())
        val filename = "Nova_$timestamp.jpg"

        val contentValues = ContentValues().apply {
            put(MediaStore.MediaColumns.DISPLAY_NAME, filename)
            put(MediaStore.MediaColumns.MIME_TYPE, "image/jpeg")
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                put(MediaStore.Images.Media.RELATIVE_PATH, "Pictures/NovaAgent")
            }
        }

        val uri = context.contentResolver.insert(
            MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
            contentValues
        ) ?: return@withContext null

        return@withContext try {
            context.contentResolver.openOutputStream(uri)?.use { stream ->
                bitmap.compress(Bitmap.CompressFormat.JPEG, 92, stream)
            }
            Log.d(tag, "Photo saved: $uri")
            uri.toString()
        } catch (e: Exception) {
            Log.e(tag, "Saving photo failed: ${e.message}")
            null
        }
    }

    fun release() {
        cameraReady = false
        cameraProvider?.unbindAll()
        cameraExecutor.shutdown()
    }

    private fun imageProxyToBitmap(image: ImageProxy): Bitmap? {
        val nv21 = yuv420888ToNv21(image)
        val yuvImage = YuvImage(
            nv21,
            ImageFormat.NV21,
            image.width,
            image.height,
            null
        )

        val outputStream = ByteArrayOutputStream()
        yuvImage.compressToJpeg(
            Rect(0, 0, image.width, image.height),
            88,
            outputStream
        )

        val jpegBytes = outputStream.toByteArray()
        val decoded = BitmapFactory.decodeByteArray(jpegBytes, 0, jpegBytes.size) ?: return null
        val rotationDegrees = image.imageInfo.rotationDegrees
        if (rotationDegrees == 0) return decoded

        val matrix = Matrix().apply { postRotate(rotationDegrees.toFloat()) }
        val rotated = Bitmap.createBitmap(
            decoded,
            0,
            0,
            decoded.width,
            decoded.height,
            matrix,
            true
        )
        if (rotated != decoded) decoded.recycle()
        return rotated
    }

    private fun yuv420888ToNv21(image: ImageProxy): ByteArray {
        val width = image.width
        val height = image.height
        val ySize = width * height
        val uvSize = width * height / 4
        val nv21 = ByteArray(ySize + uvSize * 2)

        val yPlane = image.planes[0]
        val uPlane = image.planes[1]
        val vPlane = image.planes[2]

        val yBuffer = yPlane.buffer
        val uBuffer = uPlane.buffer
        val vBuffer = vPlane.buffer

        val yBytes = ByteArray(yBuffer.remaining()).also { yBuffer.get(it) }
        val uBytes = ByteArray(uBuffer.remaining()).also { uBuffer.get(it) }
        val vBytes = ByteArray(vBuffer.remaining()).also { vBuffer.get(it) }

        var position = 0
        for (row in 0 until height) {
            val rowOffset = row * yPlane.rowStride
            for (col in 0 until width) {
                nv21[position++] = yBytes[rowOffset + col * yPlane.pixelStride]
            }
        }

        val chromaHeight = height / 2
        val chromaWidth = width / 2
        for (row in 0 until chromaHeight) {
            val uRowOffset = row * uPlane.rowStride
            val vRowOffset = row * vPlane.rowStride
            for (col in 0 until chromaWidth) {
                nv21[position++] = vBytes[vRowOffset + col * vPlane.pixelStride]
                nv21[position++] = uBytes[uRowOffset + col * uPlane.pixelStride]
            }
        }

        return nv21
    }
}

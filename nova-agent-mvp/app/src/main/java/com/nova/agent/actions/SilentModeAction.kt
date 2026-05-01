package com.nova.agent.actions

import android.app.NotificationManager
import android.content.Context
import android.media.AudioManager
import android.util.Log

class SilentModeAction(
    private val context: Context,
    private val audioManager: AudioManager
) {
    private val TAG = "NovaSilentMode"
    private var previousRingerMode = AudioManager.RINGER_MODE_NORMAL

    fun enable() {
        if (!hasDndPermission()) {
            Log.w(TAG, "DND permission not granted — go to Settings → Nova → Allow DND")
            // Fallback: vibrate mode (doesn't need DND permission)
            previousRingerMode = audioManager.ringerMode
            audioManager.ringerMode = AudioManager.RINGER_MODE_VIBRATE
            return
        }

        previousRingerMode = audioManager.ringerMode
        audioManager.ringerMode = AudioManager.RINGER_MODE_SILENT
        Log.d(TAG, "Phone silenced")
    }

    fun disable() {
        if (!hasDndPermission()) {
            audioManager.ringerMode = AudioManager.RINGER_MODE_NORMAL
            return
        }
        audioManager.ringerMode = previousRingerMode
        Log.d(TAG, "Ringer restored to mode $previousRingerMode")
    }

    fun toggle() {
        if (audioManager.ringerMode == AudioManager.RINGER_MODE_SILENT) {
            disable()
        } else {
            enable()
        }
    }

    fun isSilent() = audioManager.ringerMode == AudioManager.RINGER_MODE_SILENT

    private fun hasDndPermission(): Boolean {
        val nm = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        return nm.isNotificationPolicyAccessGranted
    }
}

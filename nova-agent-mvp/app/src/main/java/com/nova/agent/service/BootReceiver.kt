package com.nova.agent.service

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import androidx.core.content.ContextCompat

class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED ||
            intent.action == "android.intent.action.QUICKBOOT_POWERON"
        ) {
            Log.d("NovaBootReceiver", "Phone booted; trying to restart Nova Agent")
            try {
                ContextCompat.startForegroundService(
                    context,
                    Intent(context, AgentService::class.java)
                )
            } catch (e: Exception) {
                Log.w("NovaBootReceiver", "Boot restart skipped: ${e.message}")
            }
        }
    }
}

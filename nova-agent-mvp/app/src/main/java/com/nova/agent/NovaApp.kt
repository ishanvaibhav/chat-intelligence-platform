package com.nova.agent

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build

class NovaApp : Application() {

    override fun onCreate() {
        super.onCreate()
        createNotificationChannels()
    }

    private fun createNotificationChannels() {
        // Main persistent agent channel
        val agentChannel = NotificationChannel(
            CHANNEL_AGENT,
            "Nova Agent",
            NotificationManager.IMPORTANCE_LOW
        ).apply {
            description = "Nova is running in the background"
            setShowBadge(false)
        }

        // Smart reply suggestions channel
        val replyChannel = NotificationChannel(
            CHANNEL_REPLY,
            "Smart Replies",
            NotificationManager.IMPORTANCE_DEFAULT
        ).apply {
            description = "Nova's suggested replies to messages"
        }

        // Alerts channel (danger detection, emergency)
        val alertChannel = NotificationChannel(
            CHANNEL_ALERT,
            "Nova Alerts",
            NotificationManager.IMPORTANCE_HIGH
        ).apply {
            description = "Important alerts from Nova"
        }

        // Meeting notes channel
        val notesChannel = NotificationChannel(
            CHANNEL_NOTES,
            "Meeting Notes",
            NotificationManager.IMPORTANCE_DEFAULT
        ).apply {
            description = "Nova's auto-generated meeting summaries"
        }

        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannels(
            listOf(agentChannel, replyChannel, alertChannel, notesChannel)
        )
    }

    companion object {
        const val CHANNEL_AGENT = "nova_agent"
        const val CHANNEL_REPLY = "nova_reply"
        const val CHANNEL_ALERT = "nova_alert"
        const val CHANNEL_NOTES = "nova_notes"
    }
}

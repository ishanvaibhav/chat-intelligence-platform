package com.nova.agent.service

import android.app.Notification
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log
import com.nova.agent.memory.LifeLogger

class NovaNotificationListener : NotificationListenerService() {

    private val TAG = "NovaNotifListener"

    override fun onNotificationPosted(sbn: StatusBarNotification) {
        val extras = sbn.notification.extras
        val title = extras.getString(Notification.EXTRA_TITLE) ?: return
        val text = extras.getCharSequence(Notification.EXTRA_TEXT)?.toString() ?: return
        val pkg = sbn.packageName

        // Only process messaging apps
        val messagingApps = listOf(
            "com.whatsapp", "com.google.android.apps.messaging",
            "com.facebook.orca", "org.telegram.messenger",
            "com.instagram.android", "com.twitter.android"
        )
        if (pkg !in messagingApps) return

        Log.d(TAG, "Message from $pkg: $title → $text")

        // Log to life logger
        AgentService.instance?.let {
            val logger = LifeLogger(this)
            logger.logEvent("Message received from $title via $pkg")
        }

        // Smart reply drafting will be activated here once LLM is set up
        // AgentService.instance?.draftReply(title, text, pkg)
    }

    override fun onNotificationRemoved(sbn: StatusBarNotification) {
        // Clean up any pending smart reply suggestions
    }
}

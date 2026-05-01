package com.nova.agent

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.view.View
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.nova.agent.service.AgentService

class MainActivity : AppCompatActivity() {

    private val permissionRequest = 100

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        checkAndRequestPermissions()
        setupUi()
    }

    private fun setupUi() {
        val statusText = findViewById<TextView>(R.id.statusText)
        val startButton = findViewById<Button>(R.id.startButton)
        val stopButton = findViewById<Button>(R.id.stopButton)
        val dndButton = findViewById<Button>(R.id.dndButton)

        startButton.setOnClickListener {
            startNovaService()
            setRunningUi(statusText, startButton, stopButton, true)
        }

        stopButton.setOnClickListener {
            stopService(Intent(this, AgentService::class.java))
            setRunningUi(statusText, startButton, stopButton, false)
        }

        dndButton.setOnClickListener {
            startActivity(Intent(Settings.ACTION_NOTIFICATION_POLICY_ACCESS_SETTINGS))
        }

        if (allPermissionsGranted()) {
            startNovaService()
            setRunningUi(statusText, startButton, stopButton, true)
        }
    }

    private fun setRunningUi(
        statusText: TextView,
        startButton: View,
        stopButton: View,
        isRunning: Boolean
    ) {
        statusText.text = if (isRunning) {
            "Nova is running locally on this device"
        } else {
            "Nova is stopped"
        }
        startButton.visibility = if (isRunning) View.GONE else View.VISIBLE
        stopButton.visibility = if (isRunning) View.VISIBLE else View.GONE
    }

    private fun startNovaService() {
        val intent = Intent(this, AgentService::class.java)
        ContextCompat.startForegroundService(this, intent)
    }

    private fun checkAndRequestPermissions() {
        val missing = requiredPermissions().filter { permission ->
            ContextCompat.checkSelfPermission(this, permission) != PackageManager.PERMISSION_GRANTED
        }
        if (missing.isNotEmpty()) {
            ActivityCompat.requestPermissions(
                this,
                missing.toTypedArray(),
                permissionRequest
            )
        }
    }

    private fun allPermissionsGranted(): Boolean {
        return requiredPermissions().all { permission ->
            ContextCompat.checkSelfPermission(this, permission) == PackageManager.PERMISSION_GRANTED
        }
    }

    private fun requiredPermissions(): List<String> {
        val permissions = mutableListOf(
            Manifest.permission.RECORD_AUDIO,
            Manifest.permission.CAMERA
        )

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissions += Manifest.permission.POST_NOTIFICATIONS
            permissions += Manifest.permission.READ_MEDIA_IMAGES
        } else {
            permissions += Manifest.permission.READ_EXTERNAL_STORAGE
        }

        return permissions
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == permissionRequest && allPermissionsGranted()) {
            startNovaService()
        }
    }
}

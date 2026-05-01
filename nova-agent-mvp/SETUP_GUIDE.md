# Setup Guide

## 1. Open The Project

Open [nova-agent-mvp](/C:/Users/ishan/OneDrive/Desktop/whatsapp_chat_analyser/nova-agent-mvp) in Android Studio.

If Android Studio asks to trust the project, accept it and let Gradle sync finish.

## 2. Run On A Real Phone

This project is much more meaningful on a real Android phone than on an emulator because it needs:
- microphone input
- camera access
- gallery access
- Do Not Disturb access

## 3. Grant Permissions

On first launch, allow:
- microphone
- camera
- photo/media access
- notifications

Then tap `Grant DND Access` and allow the app to control Do Not Disturb / ringer mode.

## 4. Start Nova

Tap `Start Nova`.

You should then see:
- a persistent notification
- log output showing the audio loop and camera loop are running

## 5. Verify The Two Core Behaviors

Conversation detection:
- speak continuously near the phone for a short stretch
- Nova should switch the phone to silent mode
- after enough silence, Nova should restore the previous ringer state

Scenic auto-capture:
- point the camera at a bright, detailed, new scene
- Nova should periodically evaluate the frame
- if the frame scores well and does not resemble gallery images already hashed, it will save a photo into `Pictures/NovaAgent`

## 6. Optional Model Upgrades

If you want better quality later, you can wire in:
- Silero VAD
- Porcupine wake word
- NIMA/TFLite scene scoring
- Whisper
- on-device LLM inference

The MVP does not require them.

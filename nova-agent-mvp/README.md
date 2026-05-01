# Nova Agent MVP

An open-source Android prototype for an on-device phone agent.

This project is focused on the two core behaviors you asked for:
- keep listening locally on-device and switch the phone to silent mode when it detects an active conversation
- watch the camera periodically, score scenic frames locally, compare them against gallery hashes, and auto-save only scenes that look good and do not resemble photos already in the gallery

## What Works In This MVP

- Foreground service with a persistent notification
- Local microphone loop with speech detection
- Automatic silent-mode switching during sustained speech
- Local camera scene checks using CameraX
- Scenic-frame scoring with a built-in heuristic scorer
- Gallery dedup seeding from existing phone photos
- Automatic photo save to `Pictures/NovaAgent`
- Local event and photo logging

## What Is Still Optional

- Porcupine wake word
- ONNX Silero VAD
- NIMA/TFLite scene model
- On-device LLM replies
- Whisper transcription

The app runs without those extras. They are enhancements, not requirements.

## Important Platform Reality

This is the best stock-Android version of the idea, not a full system-level controller.
- It must run as a foreground service, so Android will show a persistent notification.
- Microphone and camera use remain subject to Android privacy indicators and permission controls.
- Boot restart is best-effort. Recent Android versions can restrict microphone/camera service startup after reboot.

## Project Structure

```text
app/src/main/java/com/nova/agent/
|- MainActivity.kt
|- NovaApp.kt
|- actions/
|  |- CapturePhotoAction.kt
|  |- SilentModeAction.kt
|  `- SpeakReplyAction.kt
|- memory/
|  |- GalleryHashStore.kt
|  |- LifeLogger.kt
|  `- MoodHistory.kt
|- perception/
|  |- EmotionDetector.kt
|  |- SceneQualityScorer.kt
|  |- VoiceActivityDetector.kt
|  `- WakeWordDetector.kt
`- service/
   |- AgentService.kt
   |- AudioRecordHelper.kt
   `- BootReceiver.kt
```

## Build Notes

- Open the folder in Android Studio.
- Let Gradle sync the project.
- Grant microphone, camera, gallery, and notification permissions.
- Grant Do Not Disturb access from the app UI so Nova can control the ringer.

This workspace copy does not include `gradlew` / `gradlew.bat`, so I was not able to run a full local Gradle build from the terminal here.

## Suggested Next Upgrades

- Replace the heuristic speech detector with Silero VAD
- Replace the heuristic scene scorer with NIMA or a lightweight MobileNet aesthetic model
- Add speaker diarization so conversation detection is closer to "talking to someone" instead of "sustained speech near the phone"
- Add a better boot-resume UX for Android 15+

## License

MIT

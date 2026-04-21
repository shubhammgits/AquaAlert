# AquaAlert Mobile App

This is a native Android WebView wrapper for the AquaAlert web application.

## What it does

- Opens the deployed AquaAlert web app inside an Android app shell
- Keeps the same backend, auth, reports, clusters, and dashboards
- Supports file upload, geolocation, and back navigation

## Setup

1. Open `android-app/` in Android Studio.
2. Update `WEB_URL` in `app/build.gradle`.
   ```gradle
   buildConfigField "String", "WEB_URL", '"https://YOUR_DEPLOYED_DOMAIN/"'
   ```
3. Sync Gradle.
4. Run on a device or emulator.

## Build APK

From Android Studio:
- `Build` -> `Build Bundle(s) / APK(s)` -> `Build APK(s)`

From command line after adding a Gradle wrapper:
- `./gradlew assembleDebug`
- `./gradlew assembleRelease`

## Production Notes

- The mobile app still uses the same FastAPI backend.
- MongoDB is still required behind the backend.
- The mobile app should point to the deployed HTTPS site, not to localhost.
- For client delivery, use your deployed Render domain or a custom domain.

## Files to edit for your client deployment

- `app/build.gradle` for the web URL
- `app/src/main/java/com/aquaalert/mobile/MainActivity.java` for WebView behavior
- `app/src/main/res/values/themes.xml` for Android theme colors

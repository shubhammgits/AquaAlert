# AquaAlert Android App Build Guide

This guide provides two methods to convert the AquaAlert webapp into an Android app.

## Prerequisites

- Your webapp must be deployed and accessible via HTTPS (required for PWA)
- Node.js 14+ installed
- Java JDK 11+ installed (for Android builds)
- Android SDK (or Android Studio)

---

## Method 1: Bubblewrap (Recommended - Easiest)

Bubblewrap is Google's official tool to wrap PWAs into Android apps using Trusted Web Activity (TWA).

### Step 1: Install Bubblewrap

```bash
npm install -g @anthropic/bubblewrap-cli
```

Or use npx directly:

```bash
npx @anthropic/bubblewrap-cli init
```

### Step 2: Initialize the Project

Navigate to your project directory and run:

```bash
cd android-app
npx @anthropic/bubblewrap-cli init --manifest https://YOUR_DOMAIN/static/manifest.json
```

Replace `YOUR_DOMAIN` with your deployed webapp URL (e.g., `aquaalert.example.com`)

### Step 3: Configure the App

When prompted, configure:
- **Package ID**: `com.aquaalert.app`
- **App name**: AquaAlert
- **Launcher name**: AquaAlert
- **Theme color**: #00d4ff
- **Background color**: #0b1220
- **Start URL**: /
- **Icon path**: Use the generated icons from `/static/icons/`

### Step 4: Build the APK

```bash
npx @anthropic/bubblewrap-cli build
```

This generates:
- `app-release-signed.apk` - Ready to install APK
- `app-release-bundle.aab` - For Google Play Store upload

### Step 5: Install on Device

```bash
adb install app-release-signed.apk
```

Or transfer the APK to your phone and install it.

---

## Method 2: PWABuilder (No Code - Web Based)

### Step 1: Deploy Your Webapp

Deploy your app to a hosting service with HTTPS:
- Vercel
- Netlify
- Railway
- Render
- Or any hosting with HTTPS

### Step 2: Use PWABuilder

1. Go to [https://www.pwabuilder.com/](https://www.pwabuilder.com/)
2. Enter your webapp URL
3. Click "Start"
4. Review the PWA score and manifest
5. Click "Package for stores"
6. Select "Android"
7. Download the generated APK/AAB

---

## Method 3: Android Studio WebView (Full Control)

For more customization, create a native Android project.

### Project Structure

Create this structure in the `android-app/` folder:

```
android-app/
├── app/
│   ├── src/
│   │   └── main/
│   │       ├── java/com/aquaalert/app/
│   │       │   └── MainActivity.java
│   │       ├── res/
│   │       │   ├── layout/
│   │       │   │   └── activity_main.xml
│   │       │   ├── values/
│   │       │   │   ├── strings.xml
│   │       │   │   ├── colors.xml
│   │       │   │   └── themes.xml
│   │       │   ├── mipmap-hdpi/
│   │       │   ├── mipmap-mdpi/
│   │       │   ├── mipmap-xhdpi/
│   │       │   ├── mipmap-xxhdpi/
│   │       │   └── mipmap-xxxhdpi/
│   │       └── AndroidManifest.xml
│   └── build.gradle
├── build.gradle
├── settings.gradle
└── gradle.properties
```

See the `android-app/` folder for the complete implementation.

### Build Commands

```bash
cd android-app
./gradlew assembleRelease
```

The APK will be in `android-app/app/build/outputs/apk/release/`

---

## Configuration

### Update the Webapp URL

In the Android project, update `MainActivity.java`:

```java
private static final String WEB_URL = "https://YOUR_DOMAIN";
```

Replace with your deployed webapp URL.

### For Local Testing

You can use your local IP for testing:

```java
private static final String WEB_URL = "http://192.168.x.x:8000";
```

Note: Local testing requires `android:usesCleartextTraffic="true"` in AndroidManifest.xml

---

## Digital Asset Links (Required for TWA)

For Trusted Web Activity to work, you need to verify domain ownership:

### Step 1: Generate SHA-256 Fingerprint

```bash
keytool -list -v -keystore your-keystore.jks -alias your-alias
```

### Step 2: Create assetlinks.json

Create `/.well-known/assetlinks.json` on your server:

```json
[{
  "relation": ["delegate_permission/common.handle_all_urls"],
  "target": {
    "namespace": "android_app",
    "package_name": "com.aquaalert.app",
    "sha256_cert_fingerprints": ["YOUR_SHA256_FINGERPRINT"]
  }
}]
```

### Step 3: Host the File

Add this route to your FastAPI backend (`main.py`):

```python
@app.get("/.well-known/assetlinks.json")
async def asset_links():
    return [
        {
            "relation": ["delegate_permission/common.handle_all_urls"],
            "target": {
                "namespace": "android_app",
                "package_name": "com.aquaalert.app",
                "sha256_cert_fingerprints": ["YOUR_SHA256_FINGERPRINT"]
            }
        }
    ]
```

---

## Troubleshooting

### PWA Not Installing

- Ensure HTTPS is configured
- Verify manifest.json is accessible at `/static/manifest.json`
- Check service worker is registered
- Icons must be correctly sized (at least 192x192 and 512x512)

### WebView Issues

- Enable JavaScript: `webView.settings.javaScriptEnabled = true`
- Enable DOM Storage: `webView.settings.domStorageEnabled = true`
- Handle mixed content if needed

### Build Failures

- Ensure Java JDK 11+ is installed
- Set JAVA_HOME environment variable
- Update Android SDK via Android Studio

---

## Publishing to Google Play

1. Create a Google Play Developer account ($25 one-time fee)
2. Generate a signed AAB (Android App Bundle)
3. Create app listing with screenshots and description
4. Upload the AAB
5. Submit for review

---

## Quick Start Commands

```bash
# 1. Deploy webapp (example with Vercel)
vercel deploy

# 2. Generate Android app with Bubblewrap
npm install -g @anthropic/bubblewrap-cli
npx @anthropic/bubblewrap-cli init --manifest https://your-domain/static/manifest.json
npx @anthropic/bubblewrap-cli build

# 3. Install on device
adb install app-release-signed.apk
```

---

## Files Added for PWA Support

- `/static/manifest.json` - PWA manifest with app metadata
- `/static/sw.js` - Service worker for offline support
- `/static/icons/` - App icons in various sizes
- Updated `landing.html` with PWA meta tags

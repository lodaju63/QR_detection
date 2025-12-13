[app]

# (str) Title of your application
title = QR Scanner (REST API)

# (str) Package name
package.name = qrscannerrest

# (str) Package domain (needed for android/ios packaging)
package.domain = com.qrscanner.rest

# (str) Source code where the main.py live
source.dir = .

# (str) Main entry point
source.main = android_qr_scanner_rest.py

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,txt

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements
# ✅ Dynamsoft REST API 버전: 순수 Python만 사용 (빌드 문제 없음!)
# ✅ opencv-python-headless는 pip install용 (GitHub Actions)
# ✅ buildozer에서는 opencv 레시피 사용
requirements = python3,kivy==2.2.1,camera4kivy,opencv,numpy==1.24.3,pillow,android,jnius

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

#
# Android specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Presplash background color (for android toolkit)
android.presplash_color = #FFFFFF

# (list) Permissions
# ✅ INTERNET 권한 추가 (REST API 사용)
android.permissions = CAMERA,INTERNET,FLASHLIGHT,WRITE_EXTERNAL_STORAGE,RECORD_AUDIO

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 24

# (str) Android NDK version to use
android.ndk = 25b

# (int) Android SDK version to use
android.sdk = 33

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a, armeabi-v7a

# (bool) enable AndroidX support. Enable when 'android.gradle_dependencies'
# contains an 'androidx' package.
android.enable_androidx = True

# (list) Android Gradle dependencies
android.gradle_dependencies = androidx.camera:camera-camera2:1.1.0, androidx.camera:camera-lifecycle:1.1.0, androidx.camera:camera-view:1.1.0

# (bool) Enable android auto backup feature (Android API >=23)
android.allow_backup = True

# (str) The format used to package the app for release mode (aab or apk).
android.release_artifact = apk

# (str) The format used to package the app for debug mode (apk or aab).
android.debug_artifact = apk

#
# Python for android (p4a) specific
#

# p4a 옵션 추가: 최신 빌드 도구 사용 강제
p4a.branch = develop
p4a.bootstrap = sdl2

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

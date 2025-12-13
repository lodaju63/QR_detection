[app]

# (str) Title of your application
title = QR Scanner

# (str) Package name
package.name = qrscanner

# (str) Package domain (needed for android/ios packaging)
package.domain = com.qrscanner

# (str) Source code where the main.py live
source.dir = .

# (str) Main entry point
source.main = android_qr_scanner.py

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,txt

# (list) List of inclusions using pattern matching
#source.include_patterns = assets/*,images/*.png

# (list) Source files to exclude (let empty to not exclude anything)
#source.exclude_exts = spec

# (list) List of directory to exclude (let empty to not exclude anything)
#source.exclude_dirs = tests, bin

# (list) List of exclusions using pattern matching
#source.exclude_patterns = license,images/*/*.jpg

# (str) Application versioning (method 1)
version = 0.1

# (str) Application versioning (method 2)
# version.regex = __version__ = ['"](.*)['"]
# version.filename = %(source.dir)s/main.py

# (list) Application requirements
# ✅ 중요: opencv-python-headless 대신 opencv 레시피 사용
# ✅ 중요: android, jnius 추가
requirements = python3,kivy==2.2.1,camera4kivy,opencv,numpy,pillow,pyzbar,dynamsoft-barcode-reader-bundle,android,jnius

# (str) Custom source folders for requirements
#requirements.source.kivy = ../../kivy

# (list) Garden requirements
#garden_requirements =

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (list) List of service to declare
#services = NAME:ENTRYPOINT_TO_PY,NAME2:ENTRYPOINT_TO_PY2

#
# OSX Specific
#

#
# author = © Copyright Info

# change the major version of python used by the app
osx.python_version = 3

# Kivy version to use
osx.kivy_version = 1.9.1

#
# Android specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Presplash background color (for android toolkit)
# Supported formats are: #RRGGBB #AARRGGBB or one of the following names:
# red, blue, green, black, white, gray, cyan, magenta, yellow, lightgray,
# darkgray, grey, lightgrey, darkgrey, aqua, fuchsia, lime, maroon, navy,
# olive, purple, silver, teal.
android.presplash_color = #FFFFFF

# (list) Permissions
android.permissions = CAMERA,INTERNET,FLASHLIGHT,WRITE_EXTERNAL_STORAGE,RECORD_AUDIO

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (int) Android SDK version to use
android.sdk = 33

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a, armeabi-v7a

# (bool) enable AndroidX support. Enable when 'android.gradle_dependencies'
# contains an 'androidx' package.
# ✅ 중요: Camera4Kivy를 위해 반드시 True여야 함
android.enable_androidx = True

# (list) Android Gradle dependencies
# ✅ 중요: Camera4Kivy 구동을 위한 필수 의존성
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

# (str) The directory in which python-for-android should look for your own build recipes (if any)
#p4a.local_recipes =

# (str) The directory in which python-for-android should look for your own build modules (if any)
#p4a.local_modules =

# p4a 옵션 추가: 최신 빌드 도구 사용 강제
p4a.branch = develop
p4a.bootstrap = sdl2

#
# iOS specific
#

# (str) Path to a custom kivy-ios folder
#ios.kivy_ios_dir = ../kivy-ios
# Alternately, specify the URL and branch of a git checkout:
ios.kivy_ios_dir = https://github.com/kivy/kivy-ios.git
ios.kivy_ios_branch = master

# Another platform dependency: ios-deploy
# Uncomment to use a custom checkout
#ios.ios_deploy_dir = ../ios_deploy
# Or specify URL and branch
ios.ios_deploy_dir = https://github.com/phonegap/ios-deploy.git
ios.ios_deploy_branch = 1.7.0

# (bool) Whether or not to sign the code
ios.codesign.allowed = false

# (str) Name of the certificate to use for signing the debug version
# Get a list of available identities: buildozer ios list_identities
#ios.codesign.debug = "iPhone Developer: <lastname> <firstname> (<hexstring>)"

# (str) The development team to use for signing the debug version
#ios.codesign.development_team.debug = <hexstring>

# (str) Name of the certificate to use for signing the release version
#ios.codesign.release = %(ios.codesign.debug)s

# (str) The development team to use for signing the release version
#ios.codesign.development_team.release = <hexstring>

# (str) URL pointing to .ipa file to be installed
# This option should be defined along with `display-image` and `full-size-image` options.
#ios.manifest.app_url =

# (str) URL pointing to an app icon for display on the home screen
#ios.manifest.display_image =

# (str) URL pointing to a full-size image for the app icon
#ios.manifest.full_size_image =

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage, absolute or relative to spec file
# buildozer_cache_dir = ./.buildozer_cache

# (str) Path to build output (i.e. .apk, .ipa) storage
# bin_dir = ./bin

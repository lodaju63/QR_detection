# Chaquopy 프로젝트 파일 생성 가이드

이 파일은 Chaquopy 프로젝트에 필요한 모든 파일을 생성하는 스크립트입니다.

## 📁 생성할 파일 구조

```
chaquopy_qr_scanner/
├── build.gradle.kts
├── settings.gradle.kts
├── gradle.properties
├── app/
│   ├── build.gradle.kts
│   ├── proguard-rules.pro
│   └── src/
│       └── main/
│           ├── AndroidManifest.xml
│           ├── java/com/qrscanner/
│           │   ├── MainActivity.kt
│           │   └── QRCodeAnalyzer.kt
│           ├── python/
│           │   └── qr_utils.py
│           └── res/
│               ├── layout/
│               │   └── activity_main.xml
│               └── values/
│                   └── strings.xml
└── README.md
```

## 🚀 빠른 시작 명령어

Android Studio에서:
1. File → New → New Project
2. Empty Activity 선택
3. 위의 build.gradle.kts 설정 적용
4. 파일들 복사

또는 이 디렉토리에 파일들을 생성하여 Android Studio로 열기

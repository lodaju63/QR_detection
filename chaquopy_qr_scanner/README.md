# QR Scanner - Chaquopy 버전

Buildozer 대신 Chaquopy를 사용한 Android QR 스캐너 앱입니다.

<!-- Build trigger: 2024-12-13 -->

## 🚀 시작하기

### 1. Android Studio에서 프로젝트 열기

1. Android Studio 실행
2. "Open" 선택
3. `chaquopy_qr_scanner` 폴더 선택

### 2. Dynamsoft 라이선스 키 설정

`app/src/main/java/com/qrscanner/MainActivity.kt` 파일에서:

```kotlin
barcodeReader?.license = "YOUR_DYNAMSOFT_LICENSE_KEY"
```

실제 라이선스 키로 교체하세요.

### 3. 빌드 및 실행

1. Android Studio에서 "Sync Project with Gradle Files" 클릭
2. 기기 또는 에뮬레이터 연결
3. "Run" 버튼 클릭

## 📦 주요 기능

- ✅ CameraX를 사용한 하드웨어 가속 카메라
- ✅ Dynamsoft Barcode Reader로 QR 코드 인식
- ✅ Python (OpenCV, NumPy) 지원
- ✅ 실시간 QR 코드 스캔

## 🔧 설정

### Python 패키지

`app/build.gradle.kts`의 `python` 섹션에서 Python 패키지를 관리합니다:

```kotlin
python {
    version("3.10")
    pip {
        install("opencv-python-headless==4.9.0.80")
        install("numpy")
        install("pillow")
    }
}
```

### 카메라 설정

`MainActivity.kt`에서 카메라 설정을 변경할 수 있습니다:

- 전면/후면 카메라: `CameraSelector.DEFAULT_FRONT_CAMERA` 또는 `DEFAULT_BACK_CAMERA`
- 해상도: `ImageAnalysis.Builder().setTargetResolution(...)`

## 📚 참고 자료

- [Chaquopy 문서](https://chaquo.com/chaquopy/doc/current/)
- [CameraX 가이드](https://developer.android.com/training/camerax)
- [Dynamsoft Android SDK](https://www.dynamsoft.com/barcode-reader/docs/mobile/programming/android/user-guide.html)

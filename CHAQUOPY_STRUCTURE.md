# Chaquopy 프로젝트 구조 설명

## 📁 안드로이드 앱 코드 구조

### 1. **메인 앱 코드 (Kotlin)** - 실제 Android 앱
```
app/src/main/java/com/qrscanner/
├── MainActivity.kt          # ✅ 메인 액티비티 (앱 시작점)
└── QRCodeAnalyzer.kt        # ✅ QR 코드 분석기 (카메라 프레임 처리)
```

**역할:**
- Android 네이티브 코드 (Kotlin)
- 카메라 제어 (CameraX)
- Dynamsoft SDK 호출
- Python 모듈 호출

### 2. **Python 유틸리티 (Python)** - 보조 기능
```
app/src/main/python/
└── qr_utils.py              # ✅ Python 유틸리티 함수들
```

**역할:**
- OpenCV로 QR 코드 해독 (fallback)
- 이미지 전처리 (밝기, 대비)
- ROI 추출

## 🔄 동작 방식

### Kotlin → Python 호출
```kotlin
// MainActivity.kt 또는 QRCodeAnalyzer.kt에서
val python = Python.getInstance()
val qrUtils = python.getModule("qr_utils")
val result = qrUtils.callAttr("decode_qr_opencv", imageArray)
```

### 우선순위
1. **Dynamsoft SDK** (Kotlin) - 메인
2. **Python (OpenCV)** (qr_utils.py) - 보조/fallback

## 📝 요약

- **안드로이드 앱의 메인 코드**: `MainActivity.kt`, `QRCodeAnalyzer.kt` (Kotlin)
- **Python 코드**: `qr_utils.py` (보조 기능, Kotlin에서 호출)

Python은 보조적으로 사용되며, 메인 로직은 Kotlin에 있습니다.


# Chaquopy 마이그레이션 가이드

## 📋 개요

Buildozer로 `camera4kivy` 빌드가 계속 실패할 경우, Chaquopy로 전환하는 가이드입니다.

## 🎯 Chaquopy란?

Chaquopy는 Android Studio에서 Python 코드를 직접 실행할 수 있게 해주는 플러그인입니다.
- Python 코드는 그대로 사용 가능
- Android 네이티브 기능 (CameraX, Dynamsoft SDK) 완벽 지원
- Gradle 빌드 시스템 사용 (빌드 안정성 향상)

## 📦 필요한 도구

1. **Android Studio** (최신 버전)
2. **JDK 11 이상**
3. **Python 3.8+**

## 🚀 마이그레이션 단계

### 1단계: Android Studio 프로젝트 생성

```bash
# 새 Android 프로젝트 생성
# - Template: Empty Activity
# - Language: Kotlin
# - Minimum SDK: API 24
```

### 2단계: Chaquopy 플러그인 추가

`app/build.gradle.kts` (또는 `app/build.gradle`):

```kotlin
plugins {
    id("com.chaquo.python") version "15.0.1"
}

android {
    // ... 기존 설정
}

dependencies {
    // Python 패키지
    implementation("com.chaquo.python:gradle:15.0.1")
}
```

### 3단계: Python 패키지 설정

`app/build.gradle.kts`:

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

### 4단계: Python 코드 이동

1. `app/src/main/python/` 디렉토리 생성
2. `android_qr_scanner_rest.py`를 해당 디렉토리로 복사
3. 필요한 경우 수정:
   - Kivy 대신 Android 네이티브 UI 사용
   - 또는 Kivy Android 지원 사용

### 5단계: Kotlin에서 Python 호출

`MainActivity.kt`:

```kotlin
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Python 초기화
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }
        
        val python = Python.getInstance()
        val module = python.getModule("android_qr_scanner_rest")
        
        // Python 함수 호출
        // module.callAttr("function_name", args...)
    }
}
```

### 6단계: Dynamsoft SDK 추가

`app/build.gradle.kts`:

```kotlin
dependencies {
    // Dynamsoft Barcode Reader
    implementation("com.dynamsoft:dbr:9.6.30")
}
```

### 7단계: CameraX 설정

`app/build.gradle.kts`:

```kotlin
dependencies {
    // CameraX
    implementation("androidx.camera:camera-camera2:1.3.0")
    implementation("androidx.camera:camera-lifecycle:1.3.0")
    implementation("androidx.camera:camera-view:1.3.0")
}
```

## 🔄 코드 수정 사항

### Python 코드에서 Kivy 제거

```python
# 제거
from kivy.app import App
from kivy.uix.camera import Camera

# 대신 Android 네이티브 사용
# 또는 Pyjnius로 Android API 직접 호출
```

### CameraX 사용 (Python에서)

```python
from jnius import autoclass

CameraX = autoclass('androidx.camera.core.CameraX')
# ... CameraX API 사용
```

## 📝 장점

1. ✅ **빌드 안정성**: Gradle 빌드 시스템 사용
2. ✅ **성능**: 네이티브 Android API 직접 사용
3. ✅ **Dynamsoft**: SDK 직접 통합 가능
4. ✅ **CameraX**: 하드웨어 가속 100% 활용
5. ✅ **디버깅**: Android Studio 통합 디버깅

## ⚠️ 주의사항

1. **프로젝트 구조 변경**: 완전히 새로운 프로젝트 구조 필요
2. **학습 곡선**: Android Studio, Kotlin 기본 지식 필요
3. **코드 수정**: Kivy UI를 Android 네이티브로 변경 필요

## 🔗 참고 자료

- [Chaquopy 공식 문서](https://chaquo.com/chaquopy/)
- [CameraX 가이드](https://developer.android.com/training/camerax)
- [Dynamsoft Android SDK](https://www.dynamsoft.com/barcode-reader/docs/mobile/programming/android/user-guide.html)

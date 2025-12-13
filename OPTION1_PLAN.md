# 옵션 1 실행 계획: camera4kivy 빌드 문제 해결

## 📋 현재 상태

- ✅ `camera4kivy` 제거하여 기본 Kivy Camera로 빌드 시도 중
- ✅ `android.enable_androidx = False`로 변경
- ✅ `android.gradle_dependencies` 주석 처리

## 🎯 단계별 계획

### 1단계: 기본 빌드 성공 확인
- [ ] 현재 빌드 결과 확인
- [ ] APK 생성 성공 여부 확인
- [ ] 기본 기능 테스트

### 2단계: camera4kivy 다시 추가 (빌드 문제 해결)

#### 2-1. camera4kivy 빌드 문제 원인 분석
가능한 원인:
1. **C/C++ 컴파일 오류**: NDK 버전 호환성
2. **의존성 충돌**: 다른 패키지와의 충돌
3. **메모리 부족**: 빌드 중 메모리 부족
4. **타임아웃**: 빌드 시간 초과

#### 2-2. 해결 방법 시도

**방법 A: camera4kivy 버전 변경**
```ini
# buildozer_rest.spec
requirements = python3,kivy==2.2.1,camera4kivy==0.1.0,opencv,numpy,pillow,android,jnius
```

**방법 B: NDK 버전 조정**
```ini
# buildozer_rest.spec
android.ndk = 23c  # 25b 대신 더 낮은 버전 시도
```

**방법 C: 단일 아키텍처 빌드**
```ini
# buildozer_rest.spec
android.archs = arm64-v8a  # 하나만 빌드하여 메모리 절약
```

**방법 D: 빌드 타임아웃 증가**
```yaml
# .github/workflows/build-android.yml
timeout-minutes: 180  # 120에서 180으로 증가
```

**방법 E: 메모리 최적화**
```yaml
# .github/workflows/build-android.yml
jobs:
  build-android:
    runs-on: ubuntu-latest
    # 또는 ubuntu-latest-4-cores (더 많은 리소스)
```

#### 2-3. AndroidX 설정 복원
```ini
# buildozer_rest.spec
android.enable_androidx = True
android.gradle_dependencies = androidx.camera:camera-camera2:1.1.0, androidx.camera:camera-lifecycle:1.1.0, androidx.camera:camera-view:1.1.0
```

### 3단계: 성능 테스트
- [ ] 기본 Kivy Camera 성능 측정
- [ ] camera4kivy 성능 측정 (성공 시)
- [ ] 비교 분석

## 🔄 옵션 2 전환 조건

다음 경우 옵션 2 (Chaquopy)로 전환:
1. ❌ camera4kivy 빌드가 3회 이상 실패
2. ❌ 빌드 시간이 2시간 이상 소요
3. ❌ 근본적인 해결 방법이 없음
4. ✅ 사용자가 명시적으로 전환 요청

## 📝 체크리스트

### 빌드 성공 후
- [ ] APK 다운로드 및 설치 테스트
- [ ] 기본 카메라 기능 확인
- [ ] QR 스캔 기능 확인
- [ ] 성능 측정 (FPS, 메모리 사용량)

### camera4kivy 추가 시도
- [ ] requirements에 camera4kivy 추가
- [ ] AndroidX 설정 복원
- [ ] 빌드 실행
- [ ] 오류 로그 분석
- [ ] 해결 방법 적용

## 🚨 문제 발생 시

### 빌드 실패
1. 로그 확인 (`log_level = 2`로 상세 로그)
2. 오류 메시지 분석
3. 해당 오류에 맞는 해결 방법 적용

### 성능 문제
1. 기본 Kivy Camera로도 충분한지 확인
2. 최적화 기법 적용
3. 필요 시 옵션 2 전환

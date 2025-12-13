# 안드로이드 QR 스캐너 앱

가벼운 안드로이드용 QR 코드 스캐너 앱입니다.

## 기능

- ✅ 후면/앞면 카메라 지원
- ✅ ROI (Region of Interest) 설정 - 특정 영역만 스캔
- ✅ 카메라 하드웨어 옵션 조정 (밝기, 대비, 노출)
- ✅ 실시간 QR 코드 해독
- ✅ Dynamsoft, pyzbar, OpenCV QRCodeDetector 지원

## 빌드 방법

### 1. 환경 설정

```bash
# Buildozer 설치
pip install buildozer

# Cython 설치
pip install cython
```

### 2. Android SDK/NDK 설정

Android SDK와 NDK를 설치하고 환경 변수를 설정하세요.

### 3. APK 빌드

```bash
# 초기화 (처음 한 번만)
buildozer init

# 디버그 APK 빌드
buildozer android debug

# 릴리즈 APK 빌드
buildozer android release
```

빌드된 APK는 `bin/` 디렉토리에 생성됩니다.

## 사용 방법

1. 앱 실행
2. "스캔 시작" 버튼 클릭
3. ROI 슬라이더로 스캔 영역 조정
4. 카메라 설정 슬라이더로 밝기/대비/노출 조정
5. QR 코드를 ROI 영역에 맞추면 자동으로 해독됩니다

## 주의사항

- 카메라 권한이 필요합니다
- Dynamsoft 라이선스 키가 필요할 수 있습니다
- 안드로이드 5.0 (API 21) 이상 필요

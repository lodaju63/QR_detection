# Dynamsoft REST API 버전 사용 가이드

## 🎯 왜 REST API 버전인가?

Buildozer로 Dynamsoft SDK를 빌드할 때 C 확장 라이브러리 컴파일 문제가 계속 발생합니다. 이를 해결하기 위해 **Dynamsoft REST API**를 사용하는 버전을 만들었습니다.

### 장점
- ✅ **빌드 문제 없음**: 순수 Python + HTTP 요청만 사용
- ✅ **Dynamsoft 기능 사용 가능**: 클라우드 API로 모든 기능 활용
- ✅ **OpenCV fallback**: 네트워크 오류 시 자동으로 로컬 OpenCV 사용

### 단점
- ⚠️ **인터넷 연결 필요**: REST API 사용 시 네트워크 필요
- ⚠️ **API 키 필요**: Dynamsoft 계정에서 API 키 발급 필요
- ⚠️ **약간의 지연**: 네트워크 요청으로 인한 약간의 지연 (보통 100-300ms)

## 📋 사용 방법

### 1. Dynamsoft API 키 발급

1. [Dynamsoft 공식 사이트](https://www.dynamsoft.com/)에서 계정 생성
2. Barcode Reader API 키 발급
3. API 키를 환경 변수 또는 코드에 설정

### 2. API 키 설정

**방법 1: 환경 변수 (권장)**
```bash
export DYNAMSOFT_API_KEY="your-api-key-here"
```

**방법 2: 코드 수정**
`android_qr_scanner_rest.py` 파일에서:
```python
self.dynamsoft_api_key = os.environ.get(
    'DYNAMSOFT_API_KEY',
    'your-api-key-here'  # 여기에 직접 입력
)
```

### 3. 빌드

**GitHub Actions 사용:**
```yaml
# .github/workflows/build-android.yml에서
# buildozer.spec 대신 buildozer_rest.spec 사용
buildozer -s buildozer_rest.spec android debug
```

**로컬 빌드:**
```bash
buildozer -s buildozer_rest.spec android debug
```

## 🔄 동작 방식

1. **우선순위 1**: Dynamsoft REST API 사용
   - 이미지를 base64로 인코딩
   - HTTP POST 요청으로 전송
   - 결과 받아서 표시

2. **우선순위 2**: OpenCV QRCodeDetector (로컬)
   - 네트워크 오류 시 자동 전환
   - 인터넷 없이도 작동
   - 성능은 Dynamsoft보다 약간 낮음

## 📝 빌드 설정 차이점

### buildozer.spec (기존)
```ini
requirements = python3,kivy==2.2.1,camera4kivy,opencv,numpy==1.24.3,pillow,android,jnius,pyzbar,dynamsoft-barcode-reader-bundle
```
- ❌ `dynamsoft-barcode-reader-bundle` 빌드 실패

### buildozer_rest.spec (새 버전)
```ini
requirements = python3,kivy==2.2.1,camera4kivy,opencv,numpy==1.24.3,pillow,android,jnius
```
- ✅ C 확장 라이브러리 없음 → 빌드 성공!

## 🚀 성능 최적화 팁

1. **이미지 품질 조정**: `cv2.IMWRITE_JPEG_QUALITY` 값 조정 (기본 85)
2. **요청 빈도 제한**: 너무 빠른 요청은 API 제한에 걸릴 수 있음
3. **캐싱**: 같은 QR 코드는 캐시하여 중복 요청 방지

## 🔧 문제 해결

### API 키 오류
```
Dynamsoft REST API error: 401 Unauthorized
```
→ API 키가 올바른지 확인

### 네트워크 오류
```
Dynamsoft REST API error: URLError
```
→ 자동으로 OpenCV 모드로 전환됨 (정상 동작)

### 타임아웃
```python
response = urlopen(req, timeout=5)  # 기본 5초
```
→ `timeout` 값을 조정

## 📚 참고 자료

- [Dynamsoft Barcode Reader REST API 문서](https://www.dynamsoft.com/barcode-reader/docs/web/programming/javascript/api-reference/BarcodeReader.html)
- [OpenCV QRCodeDetector 문서](https://docs.opencv.org/4.x/de/dc3/classcv_1_1QRCodeDetector.html)

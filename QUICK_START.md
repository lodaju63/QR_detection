# 🚀 QR Analyzer - 빠른 시작 가이드

## 📋 **현재 상태**

✅ **완료된 작업:**
- Git 초기화 완료
- 필요한 파일 커밋 완료
- GitHub Actions 설정 완료
- Windows & Mac 빌드 스크립트 준비 완료

---

## 🎯 **다음 3단계만 하면 끝!**

### **1️⃣ GitHub 리포지토리 생성 (2분)**

```
1. 브라우저에서 접속:
   https://github.com/new

2. 설정:
   Repository name: qr_analyzer
   Public 선택 ⭐ (무료 무제한 빌드!)
   ❌ "Initialize this repository with a README" 체크 해제!

3. "Create repository" 버튼 클릭!
```

### **2️⃣ GitHub에 코드 업로드 (1분)**

#### **방법 1: 자동 스크립트 (추천!) ⭐**

```cmd
PUSH_TO_GITHUB.bat 더블클릭!
```

이 스크립트가 자동으로:
- GitHub 연결
- 코드 업로드
- Actions 링크 제공

#### **방법 2: 수동 입력**

```bash
cd c:\Users\Administrator\qr_sh

# YOUR_USERNAME을 본인 GitHub 사용자명으로 변경!
git remote add origin https://github.com/YOUR_USERNAME/qr_analyzer.git
git branch -M main
git push -u origin main
```

### **3️⃣ 빌드 확인 및 다운로드 (15-20분 대기)**

```
1. GitHub 리포지토리 페이지 접속
2. "Actions" 탭 클릭
3. "Build All Platforms" 워크플로우 확인
4. 15-20분 후 완료!
5. Artifacts 다운로드:
   - QR_Analyzer_Windows.zip (595 MB)
   - QR_Analyzer_Mac.zip (600 MB)
```

---

## 🎊 **완료!**

### **받을 수 있는 것:**
- ✅ `QR_Analyzer.exe` (Windows 단일 파일)
- ✅ `QR_Analyzer.app` (Mac 단일 앱)
- ✅ `QR_Analyzer.dmg` (Mac 설치 파일)

### **비밀번호:**
```
2017112166
```

---

## 📊 **GitHub Actions가 자동으로 해주는 것**

```
1. macOS 가상 머신 시작
2. Windows 가상 머신 시작
3. Python 및 의존성 설치
4. PyInstaller 빌드
5. Artifact 자동 업로드
→ Mac 장비 없이도 Mac 앱 빌드 완료!
```

---

## 🔄 **업데이트 방법**

### **코드 수정 후:**

```bash
git add .
git commit -m "Update features"
git push

# 자동으로 새 버전 빌드!
```

---

## 📦 **Release 만들기 (선택사항)**

### **버전 태그로 공식 릴리즈:**

```bash
git tag v1.0.0
git push origin v1.0.0

# 자동으로:
# 1. Windows + Mac 빌드
# 2. GitHub Release 페이지 생성
# 3. 파일 자동 첨부!
```

### **사용자 다운로드:**
```
Repository → Releases → v1.0.0
→ .exe, .dmg 다운로드 가능!
```

---

## ⚠️ **주의사항**

### **Public vs Private 리포지토리**
- **Public (추천!):**
  - ✅ 무제한 빌드
  - ✅ GitHub Actions 무료
  - ⚠️ 코드가 공개됨

- **Private:**
  - ✅ 코드 비공개
  - ⚠️ 월 2000분 제한
  - ⚠️ 빌드당 15-20분 소요

### **비밀번호 보안**
- 현재 `main.py`에 하드코딩: `2017112166`
- Public 리포지토리 사용 시 노출됨
- 필요시 GitHub Secrets 사용 가능

---

## 🐛 **문제 해결**

### **"authentication failed" 에러**
```
1. GitHub 로그인 확인
2. Git Credential Manager 설치:
   winget install Microsoft.GitCredentialManager
3. 다시 push 시도
```

### **"remote origin already exists" 에러**
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/qr_analyzer.git
git push -u origin main
```

### **빌드 실패 시**
```
1. GitHub → Actions → 실패한 워크플로우 클릭
2. 로그 확인
3. 주로 의존성 문제:
   - requirements_pyqt.txt 확인
   - build_requirements.txt 확인
```

---

## 📝 **파일 구조**

```
qr_sh/
├── main.py                          ✅ 메인 앱
├── runtime_hook_ultralytics.py      ✅ PyInstaller 훅
│
├── .github/workflows/
│   ├── build-mac.yml                ✅ Mac 빌드
│   └── build-all.yml                ✅ 전체 빌드
│
├── qr_analyzer_onefile.spec         ✅ Windows 설정
├── qr_analyzer_onefile_mac.spec     ✅ Mac 설정
│
├── requirements_pyqt.txt            ✅ Python 패키지
├── build_requirements.txt           ✅ 빌드 도구
│
├── PUSH_TO_GITHUB.bat               ⭐ Push 자동화!
├── QUICK_START.md                   ⭐ 이 파일!
├── GITHUB_ACTIONS_GUIDE.md          📖 상세 가이드
└── README_FINAL.md                  📖 최종 문서
```

---

## 🎯 **지금 바로 시작!**

### **3단계 체크리스트:**

- [ ] 1. GitHub에서 리포지토리 생성 (https://github.com/new)
- [ ] 2. `PUSH_TO_GITHUB.bat` 실행
- [ ] 3. Actions 탭에서 빌드 확인

---

## 📧 **추가 도움말**

### **상세 가이드:**
- `GITHUB_ACTIONS_GUIDE.md` - GitHub Actions 완전 가이드
- `BUILD_GUIDE_MAC.md` - Mac 빌드 가이드
- `README_FINAL.md` - 전체 프로젝트 문서

### **빌드 스크립트:**
- `build_onefile.bat` - Windows 로컬 빌드
- `build_mac_onefile.command` - Mac 로컬 빌드

---

**🚀 3단계만 거치면 Mac 앱도 자동으로 빌드됩니다! 🎊**


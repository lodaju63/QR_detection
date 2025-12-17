"""
PyInstaller 런타임 훅 - ultralytics 경로 설정
단일 exe 파일에서 ultralytics가 정상 작동하도록 경로 설정
"""
import sys
import os

# PyInstaller 환경 감지
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # 임시 압축 해제 폴더
    bundle_dir = sys._MEIPASS
    
    # DLL 경로를 PATH에 추가 (Windows에서 DLL 로드용)
    if sys.platform == 'win32':
        dll_path = bundle_dir
        if dll_path not in os.environ.get('PATH', ''):
            os.environ['PATH'] = dll_path + os.pathsep + os.environ.get('PATH', '')
    
    # 환경 변수 설정
    os.environ['TORCH_HOME'] = os.path.join(bundle_dir, 'torch')
    os.environ['YOLO_CONFIG_DIR'] = os.path.join(bundle_dir, 'ultralytics', 'cfg')
    os.environ['ULTRALYTICS_CONFIG_DIR'] = os.path.join(bundle_dir, 'ultralytics', 'cfg')
    
    # HOME 디렉토리 설정 (ultralytics가 설정 파일 저장용으로 사용)
    if 'HOME' not in os.environ:
        os.environ['HOME'] = os.path.expanduser('~')
    
    # PyTorch DLL 경로 설정
    torch_lib_path = os.path.join(bundle_dir, 'torch', 'lib')
    if os.path.exists(torch_lib_path) and sys.platform == 'win32':
        if torch_lib_path not in os.environ.get('PATH', ''):
            os.environ['PATH'] = torch_lib_path + os.pathsep + os.environ.get('PATH', '')
    
    print(f"[Runtime Hook] Bundle dir: {bundle_dir}")
    print(f"[Runtime Hook] TORCH_HOME: {os.environ.get('TORCH_HOME')}")
    print(f"[Runtime Hook] YOLO_CONFIG_DIR: {os.environ.get('YOLO_CONFIG_DIR')}")
    print(f"[Runtime Hook] PATH updated for DLL loading")




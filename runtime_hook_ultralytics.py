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
    
    # Windows에서 DLL 로드를 위한 PATH 설정 (가장 먼저 실행)
    if sys.platform == 'win32':
        # bundle_dir 자체를 PATH에 추가 (루트 레벨 DLL)
        if bundle_dir not in os.environ.get('PATH', ''):
            os.environ['PATH'] = bundle_dir + os.pathsep + os.environ.get('PATH', '')
        
        # torch/lib 경로 추가
        torch_lib_path = os.path.join(bundle_dir, 'torch', 'lib')
        if os.path.exists(torch_lib_path):
            if torch_lib_path not in os.environ.get('PATH', ''):
                os.environ['PATH'] = torch_lib_path + os.pathsep + os.environ.get('PATH', '')
        
        # torch/bin 경로도 추가 (일부 DLL이 여기에 있을 수 있음)
        torch_bin_path = os.path.join(bundle_dir, 'torch', 'bin')
        if os.path.exists(torch_bin_path):
            if torch_bin_path not in os.environ.get('PATH', ''):
                os.environ['PATH'] = torch_bin_path + os.pathsep + os.environ.get('PATH', '')
        
        # torch 루트도 추가
        torch_root = os.path.join(bundle_dir, 'torch')
        if os.path.exists(torch_root):
            if torch_root not in os.environ.get('PATH', ''):
                os.environ['PATH'] = torch_root + os.pathsep + os.environ.get('PATH', '')
    
    # 환경 변수 설정
    os.environ['TORCH_HOME'] = os.path.join(bundle_dir, 'torch')
    os.environ['YOLO_CONFIG_DIR'] = os.path.join(bundle_dir, 'ultralytics', 'cfg')
    os.environ['ULTRALYTICS_CONFIG_DIR'] = os.path.join(bundle_dir, 'ultralytics', 'cfg')
    
    # HOME 디렉토리 설정 (ultralytics가 설정 파일 저장용으로 사용)
    if 'HOME' not in os.environ:
        os.environ['HOME'] = os.path.expanduser('~')
    
    # 디버그 출력 (개발 환경에서만)
    if os.environ.get('DEBUG', '').lower() == 'true':
        print(f"[Runtime Hook] Bundle dir: {bundle_dir}")
        print(f"[Runtime Hook] TORCH_HOME: {os.environ.get('TORCH_HOME')}")
        print(f"[Runtime Hook] YOLO_CONFIG_DIR: {os.environ.get('YOLO_CONFIG_DIR')}")
        print(f"[Runtime Hook] PATH: {os.environ.get('PATH', '')[:200]}...")




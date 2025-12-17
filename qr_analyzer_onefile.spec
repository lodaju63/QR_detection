# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

# Fix RecursionError: increase recursion limit
sys.setrecursionlimit(sys.getrecursionlimit() * 5)

block_cipher = None

# Get ultralytics data files
ultralytics_path = None
try:
    import ultralytics
    ultralytics_path = Path(ultralytics.__file__).parent
except:
    pass

# Get torch binary files
torch_path = None
torchvision_path = None
try:
    import torch
    torch_path = Path(torch.__file__).parent
except:
    pass

try:
    import torchvision
    torchvision_path = Path(torchvision.__file__).parent
except:
    pass

# Get dynamsoft data files
dynamsoft_path = None
try:
    import dynamsoft_barcode_reader_bundle
    dynamsoft_path = Path(dynamsoft_barcode_reader_bundle.__file__).parent
except:
    pass

# Collect binaries (DLL files)
binaries = []
if torch_path:
    # PyTorch DLL files - 재귀적으로 모든 DLL/PYD 파일 찾기
    def collect_torch_binaries(directory, target_dir='.'):
        """재귀적으로 torch 디렉토리에서 모든 DLL/PYD 파일 수집"""
        collected = []
        if not directory.exists():
            return collected
        
        # 현재 디렉토리의 DLL/PYD 파일
        for dll_file in directory.glob('*.dll'):
            collected.append((str(dll_file), target_dir))
        for pyd_file in directory.glob('*.pyd'):
            collected.append((str(pyd_file), target_dir))
        
        # 하위 디렉토리도 검색 (lib, bin 등)
        for subdir in directory.iterdir():
            if subdir.is_dir() and not subdir.name.startswith('__'):
                # lib, bin 폴더는 루트에 배치
                if subdir.name in ['lib', 'bin']:
                    collected.extend(collect_torch_binaries(subdir, '.'))
                else:
                    collected.extend(collect_torch_binaries(subdir, target_dir))
        
        return collected
    
    # torch 폴더 전체에서 바이너리 수집
    binaries.extend(collect_torch_binaries(torch_path))
    
    # torchvision DLL도 포함
    if torchvision_path:
        torchvision_binaries = collect_torch_binaries(torchvision_path)
        binaries.extend(torchvision_binaries)
    
    # 중복 제거
    seen = set()
    unique_binaries = []
    for item in binaries:
        if item not in seen:
            seen.add(item)
            unique_binaries.append(item)
    binaries = unique_binaries
    
    print(f"[Spec] Collected {len(binaries)} PyTorch binary files")

# Collect datas
datas = []
if ultralytics_path:
    datas.append((str(ultralytics_path / 'cfg'), 'ultralytics/cfg'))
    datas.append((str(ultralytics_path / 'models'), 'ultralytics/models'))

if dynamsoft_path:
    # Dynamsoft DLL files
    for dll_file in dynamsoft_path.glob('*.dll'):
        datas.append((str(dll_file), 'dynamsoft_barcode_reader_bundle'))
    
    # Dynamsoft PYD files (Python extensions)
    for pyd_file in dynamsoft_path.glob('*.pyd'):
        datas.append((str(pyd_file), 'dynamsoft_barcode_reader_bundle'))
    
    # Dynamsoft license files
    for lic_file in dynamsoft_path.glob('*.lic'):
        datas.append((str(lic_file), 'dynamsoft_barcode_reader_bundle'))
    
    # Dynamsoft Models folder (??! QR ??? ??)
    models_dir = dynamsoft_path / 'Models'
    if models_dir.exists():
        datas.append((str(models_dir), 'dynamsoft_barcode_reader_bundle/Models'))
    
    # Dynamsoft Templates folder (??! ??? ?????
    templates_dir = dynamsoft_path / 'Templates'
    if templates_dir.exists():
        datas.append((str(templates_dir), 'dynamsoft_barcode_reader_bundle/Templates'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'pyqtgraph',
        'numpy',
        'cv2',
        'PIL',
        'PIL.Image',
        'dynamsoft_barcode_reader_bundle',
        'dynamsoft_barcode_reader_bundle.DynamsoftBarcodeReader',
        'dynamsoft_barcode_reader_bundle.DynamsoftCore',
        'dynamsoft_barcode_reader_bundle.DynamsoftLicense',
        'dynamsoft_barcode_reader_bundle.DynamsoftCaptureVisionRouter',
        'dynamsoft_barcode_reader_bundle.DynamsoftImageProcessing',
        'dynamsoft_barcode_reader_bundle.DynamsoftUtility',
        'dynamsoft_barcode_reader_bundle.cvr',
        'dynamsoft_barcode_reader_bundle.dbr',
        'dynamsoft_barcode_reader_bundle.core',
        'dynamsoft_barcode_reader_bundle.dip',
        'dynamsoft_barcode_reader_bundle.dnn',
        'dynamsoft_barcode_reader_bundle.license',
        'dynamsoft_barcode_reader_bundle.utility',
        'ultralytics',
        'ultralytics.nn',
        'ultralytics.nn.modules',
        'ultralytics.nn.tasks',
        'ultralytics.models',
        'ultralytics.models.yolo',
        'ultralytics.models.yolo.detect',
        'ultralytics.models.yolo.detect.predict',
        'ultralytics.engine',
        'ultralytics.engine.predictor',
        'ultralytics.engine.trainer',
        'ultralytics.utils',
        'ultralytics.utils.checks',
        'ultralytics.utils.downloads',
        'ultralytics.utils.torch_utils',
        'ultralytics.data',
        'torch',
        'torch._C',
        'torch._dynamo',
        'torch.nn',
        'torch.nn.functional',
        'torchvision',
        'torchvision.models',
        'torchvision.transforms',
        'torchvision.transforms.functional',
        'yaml',
        'tqdm',
        'pandas',
        'scipy',
        'scipy.ndimage',
        'scipy.spatial',
        'scipy.spatial.distance',
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.backends',
        'matplotlib.backends.backend_agg',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook_ultralytics.py'],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ===== ??? EXE ??? ??? =====
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,      # ?? ????? ???!
    a.zipfiles,      # ?? ZIP ??? ???!
    a.datas,         # ?? ???????? ???!
    [],
    name='QR_Analyzer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

# COLLECT ??? ??? - ??? exe????????? ???




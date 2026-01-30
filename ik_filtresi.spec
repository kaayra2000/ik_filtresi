# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

# Proje kök dizini
project_root = Path(SPECPATH)

# Veri dosyaları (QSS stil dosyası dahil)
datas = [
    (str(project_root / 'style.qss'), '.'),
]

# Gizli importlar (PyQt6 ve pandas için gerekli)
hiddenimports = [
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'pandas',
    'pandas._libs',
    'pandas._libs.tslibs',
    'pandas._libs.tslibs.timedeltas',
    'pandas._libs.tslibs.nattype',
    'pandas._libs.tslibs.np_datetime',
    'numpy',
    'openpyxl',
    'xlrd',
    'app',
    'app.models',
    'app.models.column_info',
    'app.models.filter_model',
    'app.services',
    'app.services.file_reader',
    'app.services.data_analyzer',
    'app.services.filter_engine',
    'app.ui',
    'app.ui.main_window',
    'app.ui.column_info_widget',
    'app.ui.filter_widget',
    'app.ui.data_table_widget',
]

a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'PIL',
        'cv2',
        'torch',
        'tensorflow',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='IK_Filtresi',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI uygulaması, konsol gizli
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='IK_Filtresi',
)

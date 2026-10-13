# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

# Incluimos los modelos pre-entrenados de MediaPipe dentro del ejecutable
added_files = [
    ('../tracking-vision/models/*.task', 'models'),
]

a = Analysis(
    ['main_gui.py'],
    pathex=['.', '../tracking-vision', '../communication'],
    binaries=[],
    datas=added_files,
    hiddenimports=['mediapipe', 'cv2', 'PySide6', 'bleak', 'dispatcher', 'ble_sender'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SOFIA_Control_Station',
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
    icon=None
)

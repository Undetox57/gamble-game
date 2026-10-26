# -*- mode: python ; coding: utf-8 -*-
# Klasor (onedir) surumu:  python -m PyInstaller --noconfirm --clean gamble_gui_onedir.spec
# Cikti: dist\GambleGame\GambleGame.exe (+ _internal\ klasoru).
# AV tarayicilari tek dosya (onefile) paketleyicileri klasmaz; bu surum normal bir klasorde
# durdugu icin cok daha az yanlis alarm cikarir. Ayni metadata eklenmis, UPX kapali.

a = Analysis(
    ['gamble_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'pydoc_data'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GambleGame',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='GambleGame',
)

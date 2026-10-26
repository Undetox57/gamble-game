# -*- mode: python ; coding: utf-8 -*-
# One-file windowed build:  python -m PyInstaller --noconfirm --clean gamble_gui.spec
# Output: dist\GambleGame.exe  (the saves - savegame.txt, gamble_meta.txt, gamble_settings.txt -
# are read and written next to that exe, see gamble.config._base_dir).

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
    a.binaries,
    a.datas,
    [],
    name='GambleGame',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                      # UPX-packed binaries are a classic heuristic flag (and not installed here)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                   # a game: no black console window next to it
    version='version_info.txt',      # real product name / file version / copyright in the properties
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

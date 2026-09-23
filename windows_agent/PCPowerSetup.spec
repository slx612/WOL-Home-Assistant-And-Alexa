# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['setup_wizard_gui.py'],
    pathex=['..'],
    binaries=[],
    datas=[('assets/wakelink.ico', 'assets'), ('install-task.ps1', '.')],
    hiddenimports=['agent_core.common'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='PCPowerSetup',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='assets\\PCPowerSetup.version.txt',
    icon=['assets/wakelink.ico'],
)

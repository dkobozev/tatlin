# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ["tatlin.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=["OpenGL.platform.egl"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas
    + [
        ("tatlin/tatlin.png", "tatlin/tatlin.png", "DATA"),
        ("tests/data/gcode/slic3r.gcode", "tests/data/gcode/slic3r.gcode", "DATA"),
        ("tests/data/gcode/top.gcode", "tests/data/gcode/top.gcode", "DATA"),
        ("tests/data/stl/top.stl", "tests/data/stl/top.stl", "DATA"),
    ],
    [],
    name="tatlin",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

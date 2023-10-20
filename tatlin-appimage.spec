# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ["tatlin.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=["OpenGL.platform.egl", "gi.repository.GdkPixbuf"],
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
    [],
    exclude_binaries=True,
    name="tatlin",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas
    + [
        ("tatlin/tatlin.png", "tatlin/tatlin.png", "DATA"),
        ("tests/data/gcode/slic3r.gcode", "tests/data/gcode/slic3r.gcode", "DATA"),
        ("tests/data/gcode/top.gcode", "tests/data/gcode/top.gcode", "DATA"),
        ("tests/data/stl/top.stl", "tests/data/stl/top.stl", "DATA"),
    ],
    strip=False,
    upx=False,
    upx_exclude=[],
    name="tatlin",
)

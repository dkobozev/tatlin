# -*- mode: python -*-
a = Analysis(
    ["tatlin.py"], pathex=["."], hiddenimports=[], hookspath=None, runtime_hooks=None
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="tatlin",
    debug=False,
    strip=None,
    upx=True,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas
    + [
        ("tatlin/tatlin.png", "tatlin/tatlin.png", "DATA"),
        ("tests/data/gcode/slic3r.gcode", "tests/data/gcode/slic3r.gcode", "DATA"),
        ("tests/data/gcode/top.gcode", "tests/data/gcode/top.gcode", "DATA"),
        ("tests/data/stl/top.stl", "tests/data/stl/top.stl", "DATA"),
    ],
    strip=None,
    upx=True,
    name="tatlin",
)
app = BUNDLE(coll, name="tatlin.app")

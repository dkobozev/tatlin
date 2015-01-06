# -*- mode: python -*-
a = Analysis(['tatlin.py'],
             pathex=['.'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='tatlin.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False,
          icon='tatlin.ico' )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas + [ ('tatlin-logo.png',          'tatlin-logo.png',  'DATA')

                         , ('tests/data/gcode/min.gcode',           'tests/data/gcode/min.gcode',           'DATA')
                         , ('tests/data/gcode/slic3r.gcode',        'tests/data/gcode/slic3r.gcode',        'DATA')
                         , ('tests/data/gcode/top.gcode',           'tests/data/gcode/top.gcode',           'DATA')
                         , ('tests/data/gcode/wfu_cbi_skull.gcode', 'tests/data/gcode/wfu_cbi_skull.gcode', 'DATA')
                         , ('tests/data/gcode/wheel-left.gcode',    'tests/data/gcode/wheel-left.gcode',    'DATA')

                         , ('tests/data/stl/top.stl',           'tests/data/stl/top.stl',           'DATA')
                         , ('tests/data/stl/wfu_cbi_skull.stl', 'tests/data/stl/wfu_cbi_skull.stl', 'DATA')
                         , ('tests/data/stl/wheel-left.stl',    'tests/data/stl/wheel-left.stl',    'DATA')
                         ],
               strip=None,
               upx=True,
               name='tatlin')

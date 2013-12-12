# -*- mode: python -*-
a = Analysis(['C:\\Users\\Ryan\\Documents\\GitHub\\post_laser_schedule\\__init__.py'],
             pathex=['C:\\Users\\Ryan\\Documents\\GitHub\\post_laser_schedule'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='Post_Laser_Schedule.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False , icon='C:\\Users\\Ryan\\Documents\\GitHub\\post_laser_schedule\\post_laser_schedule.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='Post_Laser_Schedule')

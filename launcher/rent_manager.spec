# -*- mode: python ; coding: utf-8 -*-

from sys import platform

block_cipher = None

if platform.startswith('darwin'):
    miniconda =  '/tmp/miniconda.sh'
    icon = '../logo.icns'
else:
    miniconda = 'miniconda.exe'
    icon = '..\\logo.ico'

a = Analysis(['bootstrap.py'],
             binaries=[],
             datas=[('launcher.py', '.'), ('simple_ipc.py', '.'), ('venv_management.py', '.'), ('../launcher_requirements.txt', '.'), (miniconda, '.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='rent_manager',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False , icon=icon)

if platform.startswith('darwin'):
    type_identifier = 'com.github.olisolomons.rent_manager'
    info_plist = {
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'Rent Manager File',
                'CFBundleTypeIconFile': 'logo.icns',
                'LSItemContentTypes': [type_identifier],
                'LSHandlerRank': 'Owner',
                'CFBundleTypeRole': 'Editor'
            }
        ],
        'UTExportedTypeDeclarations': [
            {
                'UTTypeIdentifier': type_identifier,
                'UTTypeTagSpecification': {
                    'public.filename-extension': 'rman'
                },
                'UTTypeIconFile': 'icon.icns',
                'UTTypeDescription': 'Rent Manager File',
                'UTTypeConformsTo': ['public.json']
            }
        ]
    }
    app = BUNDLE(exe,
                 name='rent_manager.app',
                 icon=icon,
                 bundle_identifier=None,
                 info_plist=info_plist)
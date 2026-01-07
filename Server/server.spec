# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['start_server.py'],
    pathex=[r'E:\Project\PermissionManagementSys\Server', r'E:\Project\PermissionManagementSys'],
    binaries=[],
    datas=[
        (r'E:\Project\PermissionManagementSys\config.json', '.'),
        (r'E:\Project\PermissionManagementSys\config_manager.py', '.'),
    ],
    hiddenimports=[
        'win32security',
        'win32api',
        'win32con',
        'ntsecuritycon',
        'pywintypes',
        'flask',
        'flask_cors',
        'watchdog',
        'sqlite3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyd_a = Analysis(
    ['start_server.py'],
    pathex=['E:\Project\PermissionManagementSys\Server', 'E:\Project\PermissionManagementSys'],
    binaries=[],
    datas=[],
    hiddenimports=[],
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
    name='PermissionServer',
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
    icon=None,
    uac_admin=True,
)

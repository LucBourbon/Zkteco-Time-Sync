# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Incluye el hook de pywin32 si lo tienes en la carpeta hooks/
# Si no, elimina la línea 'hookspath' o ajusta la ruta.

a = Analysis(
    ['sincronizar manual version.py'],
    pathex=['.'],
    binaries=[],
    datas=[('dispositivos.json', '.')],
    hiddenimports=[],
    hookspath=['hooks'],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SincronizarManual',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Cambia a True si quieres ventana de consola
    icon=None  # Puedes poner un icono si tienes uno, ej: 'icon.ico'
)

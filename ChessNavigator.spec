# ChessNavigator - Copyright (c) 2025 David Hodge
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License v2 as published
# by the Free Software Foundation.
# Non-commercial use only. See LICENSE file for full details.



# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# Force PyInstaller to find uv's Tcl/Tk libs before the system ones
# Resolve symlink from .venv/bin/python to actual uv Python, then find its lib/
_uv_python = os.path.realpath(sys.executable)
_uv_lib = os.path.normpath(os.path.join(os.path.dirname(_uv_python), '..', 'lib'))
os.environ['LD_LIBRARY_PATH'] = _uv_lib + ':' + os.environ.get('LD_LIBRARY_PATH', '')
print(f"Tcl lib path: {_uv_lib}")  # temporary - confirm it resolves correctly

a = Analysis(
    ['ChessNavigator.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('images', 'images'),
    ],
    hiddenimports=['multiprocessing', 'multiprocessing.synchronize', 'multiprocessing.heap'],
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
    [],
    exclude_binaries=True,
    name='ChessNavigator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    icon=['images/icon.ico'] if sys.platform == 'win32' else ['images/icon.png'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='ChessNavigator',
)

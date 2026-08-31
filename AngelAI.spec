# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path
project=Path(os.environ.get("ANGEL_PROJECT_ROOT",Path.cwd())).resolve()
a=Analysis(
    [str(project/"AngelAI_direct.py")],
    pathex=[str(project)],
    binaries=[],
    datas=[(str(project/"Angel_AI.ico"),"."),(str(project/"Angel_AI.png"),".")],
    hiddenimports=["pyttsx3.drivers.sapi5"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz=PYZ(a.pure)
exe=EXE(
    pyz,a.scripts,a.binaries,a.datas,[],
    name="AngelAI",debug=False,bootloader_ignore_signals=False,strip=False,
    upx=False,console=False,disable_windowed_traceback=True,argv_emulation=False,
    target_arch=None,codesign_identity=None,entitlements_file=None,
    icon=str(project/"Angel_AI.ico"),
)

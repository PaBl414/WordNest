# Run on Windows: .venv/Scripts/python.exe -m PyInstaller WordNest.spec
from pathlib import Path

root = Path(SPECPATH)
frontend = root / 'frontend' / 'dist'
if not (frontend / 'index.html').is_file():
    raise SystemExit('Build the frontend first: run setup.ps1.')

a = Analysis(
    [str(root / 'desktop.py')],
    pathex=[str(root)],
    binaries=[],
    datas=[(str(frontend), 'frontend/dist'), (str(root / 'LICENSE'), '.')],
    hiddenimports=['uvicorn.logging', 'uvicorn.loops.asyncio', 'uvicorn.protocols.http.h11_impl'],
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['pytest', 'tkinter'], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name='WordNest', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=False, console=True, disable_windowed_traceback=False,
)

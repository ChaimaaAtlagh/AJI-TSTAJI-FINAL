# PyInstaller onedir: exe séparé de ses bibliothèques pour une distribution plus simple.
from pathlib import Path
import os
import sys

from PyInstaller.utils.hooks import collect_data_files


ROOT = Path(SPECPATH).resolve()
datas = [
    (str(ROOT / "data" / "cleaned" / "data_nettoyee.xlsx"), "data/cleaned"),
]
api_config_file = os.environ.get("AJI_API_CONFIG_FILE")
if api_config_file:
    config_path = Path(api_config_file).resolve()
    if not config_path.is_file():
        raise SystemExit(f"Configuration API de build introuvable : {config_path}")
    datas.append((str(config_path), "config"))
assets_root = ROOT / "app" / "assets"
for asset in assets_root.rglob("*"):
    if asset.is_file():
        destination = Path("app/assets") / asset.relative_to(assets_root).parent
        datas.append((str(asset), str(destination)))

# CTk et Matplotlib chargent des thèmes, polices et ressources à l'exécution.
datas += collect_data_files("customtkinter")
datas += collect_data_files("matplotlib")

# L'installation Python de construction peut ne pas exposer TclTkInfo à
# PyInstaller. Les scripts Tcl/Tk officiels restent alors ajoutés explicitement.
python_tcl_root = Path(sys.base_prefix) / "tcl"
for source_root, destination_root in (
    (python_tcl_root / "tcl8.6", "_tcl_data"),
    (python_tcl_root / "tk8.6", "_tk_data"),
):
    if not source_root.is_dir():
        raise SystemExit(f"Répertoire Tcl/Tk manquant : {source_root}")
    for resource in source_root.rglob("*"):
        if resource.is_file():
            destination = Path(destination_root) / resource.relative_to(source_root).parent
            datas.append((str(resource), str(destination)))

a = Analysis(
    [str(ROOT / "app" / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "_tkinter",
        "tkinter",
        "tkinter.constants",
        "tkinter.filedialog",
        "tkinter.font",
        "tkinter.messagebox",
        "tkinter.simpledialog",
        "tkinter.ttk",
        "matplotlib.backends.backend_tkagg",
        "matplotlib.backends.backend_agg",
        "PIL._tkinter_finder",
    ],
    hookspath=[str(ROOT / "deployment" / "pyinstaller_hooks")],
    hooksconfig={},
    runtime_hooks=[
        str(ROOT / "deployment" / "pyinstaller_hooks" / "runtime" / "aji_tcltk.py"),
    ],
    excludes=[],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AJI_TSTAJI",
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="AJI_TSTAJI",
)

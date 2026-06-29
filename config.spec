# -*- mode: python ; coding: utf-8 -*-
# VrmAiFriend 設定 UI を macOS .app にビルドする PyInstaller 設定。
#
# 構成:
#   VrmAiFriendConfig        … 即終了するランチャー（.app の本体）
#   VrmAiFriendConfigServer  … バックグラウンド Gradio サーバー
#
# ビルド手順:
#   pip install -r requirements-build.txt
#   ./build_mac.sh

from PyInstaller.building.build_main import Analysis, COLLECT, EXE, MERGE, PYZ, BUNDLE
from PyInstaller.utils.hooks import collect_all, collect_submodules

from pathlib import Path

ICON_FILE = str(Path(SPECPATH) / "VrmAiFriend_Config.icns")

block_cipher = None

server_datas = []
server_binaries = []
server_hiddenimports = collect_submodules("gradio") + [
    "yaml",
    "dotenv",
    "google",
    "google.genai",
    "safehttpx",
    "pydantic",
    "anyio",
    "httpx",
    "uvicorn",
    "fastapi",
    "starlette",
    "orjson",
    "PIL",
    "PIL.Image",
    "groovy",
    "app_instance",
    "config",
]

for package_name in ("gradio", "gradio_client", "safehttpx", "groovy"):
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(package_name)
    server_datas += pkg_datas
    server_binaries += pkg_binaries
    server_hiddenimports += pkg_hiddenimports

server_hiddenimports = list(dict.fromkeys(server_hiddenimports))

launcher_a = Analysis(
    ["launcher.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=["app_instance"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

server_a = Analysis(
    ["server.py"],
    pathex=[],
    binaries=server_binaries,
    datas=server_datas,
    hiddenimports=server_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

MERGE((server_a, "server", "server"), (launcher_a, "launcher", "launcher"))

launcher_pyz = PYZ(launcher_a.pure, launcher_a.zipped_data, cipher=block_cipher)
server_pyz = PYZ(server_a.pure, server_a.zipped_data, cipher=block_cipher)

launcher_exe = EXE(
    launcher_pyz,
    launcher_a.scripts,
    [],
    exclude_binaries=True,
    name="VrmAiFriendConfig",
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

server_exe = EXE(
    server_pyz,
    server_a.scripts,
    [],
    exclude_binaries=True,
    name="VrmAiFriendConfigServer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    launcher_exe,
    server_exe,
    server_a.binaries,
    server_a.zipfiles,
    server_a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="VrmAiFriendConfig",
)

app = BUNDLE(
    coll,
    name="VrmAiFriendConfig.app",
    icon=ICON_FILE,
    bundle_identifier="com.vrmaifriend.config",
    info_plist={
        "CFBundleName": "VRM AI Friend 設定",
        "CFBundleDisplayName": "VRM AI Friend 設定",
        "NSHighResolutionCapable": True,
    },
)

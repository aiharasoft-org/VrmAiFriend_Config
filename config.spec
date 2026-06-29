# -*- mode: python ; coding: utf-8 -*-
# VrmAiFriend 設定 UI（config.py）を macOS .app にビルドする PyInstaller 設定。
#
# ビルド手順:
#   pip install -r requirements-build.txt
#   ./build_mac.sh
#   または:
#     ./scripts/build_icon.sh
#     pyinstaller config.spec
#     ./scripts/build_dmg.sh
#
# アイコン:
#   VrmAiFriend_Config.png から VrmAiFriend_Config.icns を生成して .app / DMG に使用する。
#
# 注意:
#   setuptools 82 以降は pkg_resources が同梱されず PyInstaller が失敗するため、
#   requirements-build.txt では setuptools<81 を指定している。
#
# 出力:
#   dist/VrmAiFriendConfig.app
#   dist/VrmAiFriendConfig-Installer.dmg
#
# Unity からの起動例（macOS）:
#   open -a "/path/to/dist/VrmAiFriendConfig.app"

from PyInstaller.utils.hooks import collect_all, collect_submodules

from pathlib import Path

ICON_FILE = str(Path(SPECPATH) / "VrmAiFriend_Config.icns")

block_cipher = None

datas = []
binaries = []
hiddenimports = collect_submodules("gradio") + [
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
]

# Gradio 周辺は静的ファイル欠落で起動失敗しやすいため明示的に収集する
for package_name in ("gradio", "gradio_client", "safehttpx", "groovy"):
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(package_name)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

hiddenimports = list(dict.fromkeys(hiddenimports))

a = Analysis(
    ["config.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
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

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
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

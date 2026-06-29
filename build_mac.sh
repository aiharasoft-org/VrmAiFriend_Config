#!/bin/bash
# macOS 向け .app と DMG インストーラをまとめてビルドする。

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

"$ROOT_DIR/scripts/build_icon.sh"
"$ROOT_DIR/venv/bin/pyinstaller" config.spec --noconfirm
"$ROOT_DIR/scripts/build_dmg.sh"

echo "完了:"
echo "  dist/VrmAiFriendConfig.app"
echo "  dist/VrmAiFriendConfig-Installer.dmg"

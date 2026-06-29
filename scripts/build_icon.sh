#!/bin/bash
# VrmAiFriend_Config.png から macOS 用 .icns を生成する。

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PNG="$ROOT_DIR/VrmAiFriend_Config.png"
ICONSET="$ROOT_DIR/VrmAiFriend_Config.iconset"
ICNS="$ROOT_DIR/VrmAiFriend_Config.icns"

if [[ ! -f "$PNG" ]]; then
  echo "エラー: $PNG が見つかりません。" >&2
  exit 1
fi

rm -rf "$ICONSET"
mkdir -p "$ICONSET"

sips -z 16 16     "$PNG" --out "$ICONSET/icon_16x16.png" >/dev/null
sips -z 32 32     "$PNG" --out "$ICONSET/icon_16x16@2x.png" >/dev/null
sips -z 32 32     "$PNG" --out "$ICONSET/icon_32x32.png" >/dev/null
sips -z 64 64     "$PNG" --out "$ICONSET/icon_32x32@2x.png" >/dev/null
sips -z 128 128   "$PNG" --out "$ICONSET/icon_128x128.png" >/dev/null
sips -z 256 256   "$PNG" --out "$ICONSET/icon_128x128@2x.png" >/dev/null
sips -z 256 256   "$PNG" --out "$ICONSET/icon_256x256.png" >/dev/null
sips -z 512 512   "$PNG" --out "$ICONSET/icon_256x256@2x.png" >/dev/null
sips -z 512 512   "$PNG" --out "$ICONSET/icon_512x512.png" >/dev/null
sips -z 1024 1024 "$PNG" --out "$ICONSET/icon_512x512@2x.png" >/dev/null

iconutil -c icns "$ICONSET" -o "$ICNS"
rm -rf "$ICONSET"

echo "アイコンを生成しました: $ICNS"

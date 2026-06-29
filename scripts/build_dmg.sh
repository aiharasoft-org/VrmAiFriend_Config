#!/bin/bash
# VrmAiFriendConfig.app をアイコン付き DMG インストーラにまとめる。

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP_NAME="VrmAiFriendConfig"
APP_PATH="$ROOT_DIR/dist/${APP_NAME}.app"
DMG_PATH="$ROOT_DIR/dist/${APP_NAME}-Installer.dmg"
ICNS="$ROOT_DIR/VrmAiFriend_Config.icns"
VOLUME_NAME="VRM AI Friend 設定"
STAGING="$ROOT_DIR/dist/dmg-staging"
RW_DMG="$ROOT_DIR/dist/${APP_NAME}-Installer-rw.dmg"
MOUNT_DIR=""

cleanup() {
  if [[ -n "$MOUNT_DIR" && -d "$MOUNT_DIR" ]]; then
    hdiutil detach "$MOUNT_DIR" -quiet || true
  fi
  rm -f "$RW_DMG"
  rm -rf "$STAGING"
}
trap cleanup EXIT

if [[ ! -d "$APP_PATH" ]]; then
  echo "エラー: $APP_PATH が見つかりません。先に pyinstaller config.spec を実行してください。" >&2
  exit 1
fi

if [[ ! -f "$ICNS" ]]; then
  "$ROOT_DIR/scripts/build_icon.sh"
fi

rm -rf "$STAGING" "$DMG_PATH" "$RW_DMG"
mkdir -p "$STAGING"
cp -R "$APP_PATH" "$STAGING/"
ln -s /Applications "$STAGING/Applications"

hdiutil create -size 512m -fs HFS+ -volname "$VOLUME_NAME" -ov "$RW_DMG" >/dev/null
ATTACH_OUTPUT="$(hdiutil attach -readwrite -noverify -noautoopen "$RW_DMG")"
MOUNT_DIR="$(printf '%s\n' "$ATTACH_OUTPUT" | tail -1 | awk -F '\t' '{print $NF}')"

if [[ ! -d "$MOUNT_DIR" ]]; then
  echo "エラー: DMG のマウントに失敗しました。" >&2
  echo "$ATTACH_OUTPUT" >&2
  exit 1
fi

ditto "$STAGING/" "$MOUNT_DIR/"
cp "$ICNS" "$MOUNT_DIR/.VolumeIcon.icns"
if command -v SetFile >/dev/null 2>&1; then
  SetFile -a C "$MOUNT_DIR"
  SetFile -a V "$MOUNT_DIR/.VolumeIcon.icns"
else
  echo "警告: SetFile が見つからないため DMG のボリュームアイコンは未設定です。" >&2
fi

hdiutil detach "$MOUNT_DIR" -quiet
MOUNT_DIR=""
hdiutil convert "$RW_DMG" -format UDZO -imagekey zlib-level=9 -o "$DMG_PATH" >/dev/null

echo "インストーラを生成しました: $DMG_PATH"

# VrmAiFriend Config

VRM AI Friend 用のキャラクター設定ツール。Web UI で性格パラメータを編集し、システムプロンプトを生成・保存します。

## 機能

- 基本情報（名前・性別・年齢・その他指示）の編集
- 性格パラメータ（0〜10）の調整
- Gemini API によるシステムプロンプトの自動生成
- 設定の保存（次回起動時に復元）

## 必要環境

- Python 3.12+
- macOS（.app / .dmg ビルド時）

## セットアップ

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

AI 自動生成を使う場合は、API キーを設定します。

```bash
cp .env.example ~/.env
# ~/.env の GEMINI_API_KEY を編集
```

## 起動

```bash
source venv/bin/activate
python config.py
```

ブラウザで設定画面が開きます（`http://127.0.0.1:7860` 付近）。

## 設定の保存先

| ファイル | 内容 |
|----------|------|
| `~/.config/VrmAiFriend/config.yaml` | 基本情報・性格パラメータ |
| `~/.config/VrmAiFriend/system_instruction.txt` | システムプロンプト |

## macOS アプリのビルド（任意）

```bash
pip install -r requirements-build.txt
./build_mac.sh
```

出力:

- `dist/VrmAiFriendConfig.app`
- `dist/VrmAiFriendConfig-Installer.dmg`

## ライセンス

[GNU General Public License v3.0](LICENSE)（GPL-3.0）

このソフトウェアを改変・配布する場合、GPL-3.0 の条件に従いソースコードを公開する必要があります。

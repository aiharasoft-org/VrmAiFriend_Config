# VrmAiFriend Config

**Version V0.1.0**

VRM AI Friend 用のキャラクター設定ツール。Web UI で性格パラメータを編集し、システムプロンプトを生成・保存します。

> **VrmAiFriend v0.6 以降:** 本ツールと同等の人格設定は、メインアプリのメニュー **人格** タブから行えます。本リポジトリ（Config）は v0.6 向けの機能追加はありません。

## 機能

- 基本情報（名前・性別・年齢・その他指示）の編集
- 性格パラメータ（0〜10）の調整
- Gemini API によるシステムプロンプトの自動生成
- 設定の保存（次回起動時に復元）

## 必要環境

- Python 3.12+
- macOS（.app / .dmg ビルド時）
- Gemini API キー（必須）

## セットアップ

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

システムプロンプトの AI 自動生成を行うため、**Gemini API キーの設定が必須**です。

ホームディレクトリの `~/.env` に、次の行を**追加**してください。  
既に `~/.env` がある場合は、上書きせず追記のみ行ってください。

```bash
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

- 設定ファイルの場所: `~/.env`
- API キーの取得: [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)
- `AIzaSy...` の部分は、ご自身の API キーに置き換えてください



## 起動

```bash
source venv/bin/activate
python config.py
```

ブラウザで設定画面が開きます（`http://127.0.0.1:7860` 付近）。

macOS の `.app` を起動した場合も同様に、バックグラウンドで Gradio サーバー（`VrmAiFriendConfigServer`）が立ち上がり、ブラウザが自動で開きます。

### 再起動について

すでにバックグラウンドサーバーが動いている状態でアプリ（または `python config.py`）を再度起動すると、**既存のサーバーを終了してから新しく起動**します。

> **注意:** ブラウザ上で「設定を保存」していない編集内容は、再起動時に失われます。ディスクに保存済みの設定（`~/.config/VrmAiFriend/`）はそのまま読み込まれます。



## 設定の保存先


| ファイル                                           | 内容           |
| ---------------------------------------------- | ------------ |
| `~/.config/VrmAiFriend/config.yaml`            | 基本情報・性格パラメータ |
| `~/.config/VrmAiFriend/system_instruction.txt` | システムプロンプト    |




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

## リリース情報

- [V0.1.0 リリースノート](RELEASE_v0.1.0.md)
- [変更履歴](CHANGELOG.md)


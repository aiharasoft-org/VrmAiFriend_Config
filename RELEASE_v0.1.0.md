# リリースノート V0.1.0

**リリース日:** 2026-06-29  
**リポジトリ:** [https://github.com/aiharasoft-org/VrmAiFriend_Config](https://github.com/aiharasoft-org/VrmAiFriend_Config)

## 概要

VRM AI Friend 用キャラクター設定ツールの初回リリースです。

## 同梱物（GitHub Release）


| ファイル                              | 説明               |
| --------------------------------- | ---------------- |
| `VrmAiFriendConfig-Installer.dmg` | macOS インストーラ（推奨） |
| ソースコード（zip）                       | 開発者向け            |


## インストール（macOS）

1. `VrmAiFriendConfig-Installer.dmg` をダブルクリック
2. `VrmAiFriendConfig.app` を **Applications** にドラッグ
3. アプリを起動

## 起動の挙動

- 起動時にバックグラウンドサーバー（`VrmAiFriendConfigServer`）が立ち上がり、ブラウザで設定画面（`http://127.0.0.1:7860` 付近）が開きます。
- すでにサーバーが動いている場合は、**既存プロセスを終了してから再起動**します（2 回目以降の起動でも常に新しいサーバーで開きます）。
- ブラウザで未保存の編集がある場合は、再起動前に「設定を保存」を押してください。



## 初回設定

システムプロンプトの AI 自動生成を行うため、**Gemini API キーの設定が必須**です。

ホームディレクトリの `~/.env` に、次の行を**追加**してください。  
既に `~/.env` がある場合は、上書きせず追記のみ行ってください。

```bash
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

- 設定ファイルの場所: `~/.env`
- API キーの取得: [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)
- `AIzaSy...` の部分は、ご自身の API キーに置き換えてください



## 設定の保存先


| パス                                             | 内容           |
| ---------------------------------------------- | ------------ |
| `~/.config/VrmAiFriend/config.yaml`            | 基本情報・性格パラメータ |
| `~/.config/VrmAiFriend/system_instruction.txt` | システムプロンプト    |




## 動作環境

- macOS（`.dmg` / `.app`）
- Python 3.12+（ソースから実行する場合）
- Gemini API キー（必須）



## ライセンス

GPL-3.0 — 改変・配布時はソース公開が必要です。詳細は [LICENSE](LICENSE) を参照してください。


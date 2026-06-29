# VrmAiFriendConfig リリースビルド・公証（ノータライズ）手順書

Mac環境でアプリを一般配布するために、証明書の取得からPyInstallerでのビルド、Appleへの公証（Notarization）申請、およびチケットのホチキス留め（Staple）を行うための公式手順です。

## 前提条件・環境情報
- **開発用Apple ID**: `aiharasoft@gmail.com`
- **正式チームID (Team ID)**: `K484F59UH3`
- **配布用コード署名証明書**: `Developer ID Application: Uda Toyokazu (K484F59UH3)`
- **認証方法**: Apple ID管理ページで発行した「16桁のApp用パスワード」を使用します。

---

## 準備編：配布用証明書の初回取得手順
Macに `Developer ID Application` 証明書が存在しない、または `no identity found` エラーが発生した場合は、以下の手順でWebから手動取得してインストールします。

### 1. MacでCSRファイル（鍵の素）の生成
1. Macの **「キーチェーンアクセス」** アプリを開きます。
2. メニューバーの **「キーチェーンアクセス」 ＞ 「証明書アシスタント」 ＞ 「認証局に証明書を要求...」** を選択します。
3. ユーザーのメールアドレスに `aiharasoft@gmail.com`、通称に `Uda Toyokazu` を入力します。
4. 要求の処理で **「ディスクに保存」** にチェックを入れ、デスクトップ等に保存します（`CertificateSigningRequest.certSigningRequest` が生成されます）。

### 2. Apple Developerサイトでの証明書発行と登録
1. ブラウザで [Apple Developer サインインページ](https://developer.apple.com/account/) を開き、`aiharasoft@gmail.com` でサインインします。
2. **「Certificates, Identifiers & Profiles」** を開き、左上の **「＋（プラス）」ボタン** をクリックします。
3. **「Developer ID Application」** にチェックを入れて「Continue」を押します。
4. Profile Typeは **「G2 Sub-CA (Xcode 11.4.1 or later)」**（デフォルト）を選択します。
5. **「Choose File」** から先ほど保存したCSRファイルを選択してアップロードし、「Continue」を押します。
6. 発行された証明書（`.cer` ファイル）をダウンロードし、ファイルを**ダブルクリック**してMacのキーチェーンに登録します。

### 3. コマンドラインでの証明書確認確認
以下のbashコマンドを実行し、証明書がMacに正しく認識されているか確認します。

```bash
security find-identity -p basic -v

出力に Developer ID Application: Uda Toyokazu (K484F59UH3) があれば準備完了です。

リリースビルド・公証の全工程（5ステップ）
プログラムの修正完了後、以下のbashコマンドを順番に実行します。

ステップ1: PyInstallerによるアプリのビルド
まずは通常通りプログラムをビルドし、.app パッケージを生成します。

Bash
pyinstaller VrmAiFriendConfig.spec --clean
注意: これにより dist/VrmAiFriendConfig.app が新しく生成され、古い署名はリセットされます。

ステップ2: 正式な配布用証明書で「内側から」再署名
Pythonアプリ（PyInstaller構造）を公証に通すため、内部のライブラリ（.so/.dylib）を先に署名し、最後にアプリ全体を署名します。以下のコマンドをすべて実行してください。

Bash
# 1. 内部のすべての .so と .dylib ファイルを配布用証明書で一括署名
find "dist/VrmAiFriendConfig.app" -name "*.so" -or -name "*.dylib" | xargs codesign --force --options=runtime --timestamp --sign "Developer ID Application: Uda Toyokazu (K484F59UH3)"

# 2. MacOSフォルダ内にある実行バイナリを署名
codesign --force --options=runtime --timestamp --sign "Developer ID Application: Uda Toyokazu (K484F59UH3)" "dist/VrmAiFriendConfig.app/Contents/MacOS/VrmAiFriendConfigServer"

# 3. 最後に、アプリ本体（entitlements.plistを適用）を署名
codesign --force --options=runtime --entitlements ./entitlements.plist --timestamp --sign "Developer ID Application: Uda Toyokazu (K484F59UH3)" "dist/VrmAiFriendConfig.app"
🔍 署名の検証（確認用）
正しく署名が完了したか、以下のコマンドでエラーが出ないか確認します。

Bash
codesign --verify --verbose dist/VrmAiFriendConfig.app
ステップ3: 署名情報を保持したままZIP圧縮
Mac標準の圧縮機能では署名が壊れる可能性があるため、必ず ditto コマンドを使用します。

Bash
ditto -c -k --sequesterRsrc --keepParent dist/VrmAiFriendConfig.app dist/VrmAiFriendConfig.zip
ステップ4: Appleノータライズサーバーへの提出
有料開発者アカウントのチームIDを指定してZIPファイルを送信し、Appleの自動バリデーションを待ちます。

Bash
xcrun notarytool submit dist/VrmAiFriendConfig.zip --apple-id "aiharasoft@gmail.com" --team-id "K484F59UH3" --wait
※パスワードを求められたら、16桁のApp用パスワードを入力します。
※最終ステータスが status: Accepted となれば公証成功です。

ステップ5: 仕上げのホチキス留め（Staple）
オフライン環境でもユーザーが一発でスムーズに起動できるよう、Appleの合格証（チケット）をアプリ本体に直接焼き付けます。

Bash
xcrun stapler staple "dist/VrmAiFriendConfig.app"
※ The staple and validate action worked! と表示されれば完了です。

最終配布物の確認
すべてが完璧に完了したか、以下のコマンドで最終テストを行います。

Bash
spctl --assess --verbose --type execute "dist/VrmAiFriendConfig.app"
【成功時の出力結果】

Plaintext
dist/VrmAiFriendConfig.app: accepted
source=Notarized Developer ID
この状態になった dist/VrmAiFriendConfig.zip が、一般ユーザーへそのまま配布可能な最終成果物（リリース物）となります。
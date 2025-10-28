# Render.com 手動デプロイ手順書
## AI Avatar Futaba - 京友禅チャットボットシステム

**最終更新日**: 2025年10月27日  
**対象リポジトリ**: https://github.com/IVipcy/Futaba_ver1.0

---

## 📋 目次

1. [事前準備](#事前準備)
2. [Renderアカウント作成・ログイン](#renderアカウント作成ログイン)
3. [Web Service作成](#web-service作成)
4. [基本設定](#基本設定)
5. [環境変数設定](#環境変数設定)
6. [デプロイ実行](#デプロイ実行)
7. [永続ディスク追加](#永続ディスク追加)
8. [動作確認](#動作確認)
9. [トラブルシューティング](#トラブルシューティング)

---

## 事前準備

### 必要なもの

✅ GitHubアカウント  
✅ OpenAI APIキー  
✅ Azure Speech Serviceキー  
✅ Supabaseプロジェクト（URL & Key）  
✅ クレジットカード（Render Starterプラン: $7/月）

### 確認事項

- [ ] GitHubリポジトリにコードがプッシュ済み
- [ ] `.gitignore`に`venv/`と`.env`が含まれている
- [ ] `requirements.txt`が最新
- [ ] `build.sh`が実行可能
- [ ] `application.py`が動作確認済み

---

## Renderアカウント作成・ログイン

### 手順

1. **Render公式サイトにアクセス**
   ```
   https://render.com
   ```

2. **Sign Upをクリック**
   - 画面右上の「Get Started」または「Sign Up」

3. **GitHubアカウントで登録**
   - 「Sign up with GitHub」を選択
   - GitHubの認証画面で「Authorize Render」をクリック
   - 必要な権限を付与

4. **ダッシュボードにアクセス**
   - 登録完了後、自動的にダッシュボードに遷移

---

## Web Service作成

### 手順

1. **新規サービス作成**
   - Dashboard画面で「**New +**」ボタンをクリック
   - メニューから「**Web Service**」を選択

2. **リポジトリ接続**
   
   **初回の場合（リポジトリが表示されない）:**
   - 「**Configure account**」をクリック
   - GitHubの設定画面に遷移
   - 「Repository access」で以下のいずれかを選択：
     - `All repositories` （すべてのリポジトリ）
     - `Only select repositories` → `Futaba_ver1.0` を選択
   - 「Save」をクリック
   - Renderの画面に戻る

   **リポジトリが表示されている場合:**
   - `IVipcy/Futaba_ver1.0` を探してクリック
   - または検索ボックスで「Futaba」と入力

3. **「Connect」をクリック**

---

## 基本設定

次の画面で以下の項目を設定します。

### 1. Name（名前）
```
ai-avatar-futaba
```
※この名前がURLの一部になります（例: `https://ai-avatar-futaba.onrender.com`）

### 2. Region（リージョン）
```
Singapore
```
※日本から最も近く、レイテンシが低い

### 3. Branch（ブランチ）
```
main
```

### 4. Root Directory（ルートディレクトリ）
```
（空白のまま）
```

### 5. Runtime（ランタイム）
```
Python 3
```
⚠️ **重要**: 必ず「Python 3」を選択してください。Dockerは使用しません。

### 6. Build Command（ビルドコマンド）
```
bash build.sh
```

### 7. Start Command（起動コマンド）
```
gunicorn application:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 --preload --log-level info
```

### 8. Instance Type（インスタンスタイプ）
```
Starter
```
- 月額: **$7**
- RAM: 512MB
- 永続ディスク対応

---

## 環境変数設定

「**Environment Variables**」セクションで、「**Add Environment Variable**」をクリックし、以下をすべて追加します。

### 必須環境変数

| Key | Value |
|-----|-------|
| `OPENAI_API_KEY` | `your-openai-api-key-here` |
| `AZURE_SPEECH_KEY` | `your-azure-speech-key-here` |
| `AZURE_SPEECH_REGION` | `japaneast` |
| `AZURE_VOICE_NAME` | `ja-JP-MayuNeural` |
| `SUPABASE_URL` | `your-supabase-url-here` |
| `SUPABASE_KEY` | `your-supabase-key-here` |

### オプション環境変数

| Key | Value |
|-----|-------|
| `COEFONT_ENABLED` | `false` |
| `CHROMA_DB_PATH` | `data/chroma_db` |
| `FLASK_ENV` | `production` |
| `PYTHON_VERSION` | `3.11.0` |

### 入力方法

1. 「**Add Environment Variable**」をクリック
2. **Key**: 左の列に変数名を入力（例: `OPENAI_API_KEY`）
3. **Value**: 右の列に値を入力
4. もう一度「**Add Environment Variable**」をクリックして次の変数を追加
5. すべての変数を入力するまで繰り返す

⚠️ **注意**: 
- コピー＆ペースト時に余計なスペースが入らないように注意
- 値は引用符（`"`）なしで入力

---

## デプロイ実行

### 手順

1. **設定内容を確認**
   - すべての項目が正しく入力されているか確認
   - 特に環境変数の数（合計10個）を確認

2. **「Create Web Service」をクリック**
   - 青色の大きなボタンです

3. **ビルド開始**
   - 自動的にビルドプロセスが開始されます
   - ログがリアルタイムで表示されます

4. **ビルド完了を待つ**
   - 初回ビルドは **5〜10分** かかります
   - ログに以下が表示されれば成功：
     ```
     ==> Build successful 🎉
     ==> Deploying...
     ==> Starting service with 'gunicorn application:app...'
     ```

### ログで確認すべきポイント

✅ Pythonバージョンが3.11であること  
✅ `requirements.txt`のインストールが成功していること  
✅ ChromaDB関連パッケージがインストールされていること  
✅ Gunicornが起動していること  

---

## 永続ディスク追加

**重要**: データ（ChromaDB、アップロードファイル）を永続化するために必須です。

### 手順

1. **デプロイ完了を確認**
   - サービスが「Live」状態になっていることを確認

2. **Settings タブをクリック**
   - 画面上部のタブから「Settings」を選択

3. **Disks セクションまでスクロール**
   - 左メニューまたはページ内の「Disks」セクションを探す

4. **「Add Disk」をクリック**

5. **ディスク設定を入力**
   
   | 項目 | 値 |
   |------|-----|
   | **Name** | `futaba-data` |
   | **Mount Path** | `/opt/render/project/src/data` |
   | **Size** | `1` GB |

6. **「Save」をクリック**

7. **自動再起動**
   - ディスク追加後、サービスが自動的に再起動します
   - 再起動完了まで1〜2分待ちます

### 確認方法

- Logsタブで以下のようなメッセージを確認：
  ```
  ==> Mounting disk futaba-data to /opt/render/project/src/data
  ```

---

## 動作確認

### 1. デプロイURLを確認

サービス名の下に表示されているURLをクリック：
```
https://ai-avatar-futaba.onrender.com
```

### 2. ヘルスチェック

ブラウザで以下にアクセス：
```
https://ai-avatar-futaba.onrender.com/health
```

**期待される応答**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-27T12:00:00"
}
```

### 3. アプリケーション動作確認

1. メインページにアクセス
2. ログインできるか確認
3. チャット機能が動作するか確認
4. 音声再生が動作するか確認
5. Live2Dアバターが表示されるか確認

### 4. ログ確認

「**Logs**」タブでエラーがないか確認：
```
✅ No critical errors
✅ Gunicorn workers running
✅ Socket.IO connected
```

---

## トラブルシューティング

### ❌ ビルドエラー: "failed to read dockerfile"

**原因**: RuntimeがDockerに設定されている  
**解決**: Settings → Runtimeを「Python 3」に変更

### ❌ ビルドエラー: "requirements.txt not found"

**原因**: Root Directoryの設定が間違っている  
**解決**: Settings → Root Directoryを空白にする

### ❌ 起動エラー: "Module 'application' not found"

**原因**: Start Commandが間違っている  
**解決**: Settings → Start Commandを確認：
```
gunicorn application:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 --preload --log-level info
```

### ❌ 実行時エラー: "OpenAI API key not found"

**原因**: 環境変数が設定されていない  
**解決**: 
1. Settings → Environment Variables
2. `OPENAI_API_KEY` が正しく設定されているか確認
3. 変更後、「Manual Deploy」で再デプロイ

### ❌ データが消える

**原因**: 永続ディスクが設定されていない  
**解決**: [永続ディスク追加](#永続ディスク追加)を参照

### ❌ 503 Service Unavailable

**原因**: サービスがまだ起動中、またはクラッシュ  
**解決**:
1. Logsタブでエラーを確認
2. 必要に応じて「Manual Deploy」で再デプロイ
3. それでも解決しない場合は環境変数を再確認

### ❌ 音声が再生されない

**原因**: Azure Speech Serviceの設定エラー  
**解決**:
1. `AZURE_SPEECH_KEY` が正しいか確認
2. `AZURE_SPEECH_REGION` が `japaneast` になっているか確認
3. `AZURE_VOICE_NAME` が `ja-JP-MayuNeural` になっているか確認

---

## 再デプロイ方法

コードを更新した場合の再デプロイ手順：

### 自動デプロイ（推奨）

1. ローカルでコードを修正
2. Gitにコミット＆プッシュ
   ```bash
   git add .
   git commit -m "Update message"
   git push
   ```
3. Renderが自動的にビルド＆デプロイ

### 手動デプロイ

1. Render Dashboard → 対象サービスをクリック
2. 「**Manual Deploy**」ボタンをクリック
3. 「Deploy latest commit」を選択

---

## 環境変数の更新方法

1. Settings → Environment Variables
2. 変更したい変数の「Edit」をクリック
3. 新しい値を入力
4. 「Save Changes」をクリック
5. サービスが自動的に再起動

---

## コスト管理

### Starter プラン: $7/月

- 512MB RAM
- 永続ディスク 1GB
- 自動スリープなし（常時稼働）

### 無料期間

- 初回サインアップ時に $5 のクレジット付与
- クレジット期間中は実質無料

### 支払い方法

1. Dashboard → Account Settings
2. Billing タブ
3. クレジットカード情報を登録

---

## セキュリティ推奨事項

### ✅ 必須対応

- [ ] 環境変数に機密情報を保存（ハードコードしない）
- [ ] `.env`ファイルを`.gitignore`に追加
- [ ] 定期的にAPIキーをローテーション

### ✅ 推奨対応

- [ ] カスタムドメインの設定（オプション）
- [ ] HTTPSの使用（Renderはデフォルトで有効）
- [ ] ログの定期確認

---

## サポート・問い合わせ

### Render公式サポート

- ドキュメント: https://render.com/docs
- コミュニティ: https://community.render.com

### プロジェクト担当者

- Email: suguru.fukushima@congen-ai.com
- GitHub: https://github.com/IVipcy/Futaba_ver1.0

---

## チェックリスト（完了確認用）

デプロイ完了後、以下をすべてチェック：

- [ ] サービスが「Live」状態
- [ ] URLにアクセスできる
- [ ] `/health`エンドポイントが正常応答
- [ ] ログインできる
- [ ] チャット機能が動作
- [ ] 音声再生が動作
- [ ] Live2Dアバターが表示
- [ ] 永続ディスクが追加済み
- [ ] 環境変数が10個すべて設定済み
- [ ] エラーログがない

---

**デプロイ成功おめでとうございます！🎉**


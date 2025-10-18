# 🚀 Render.com 移行ガイド - AI Avatar REI

**AWSからRenderへの完全移行手順**

---

## 📊 コスト比較

| プラットフォーム | 月額コスト | 年間コスト | 備考 |
|---|---|---|---|
| **AWS（現在）** | **¥24,000** | **¥288,000** | t3.medium使用時 |
| **Render Starter** | **¥1,050** ($7) | **¥12,600** | 推奨プラン |

**年間削減額: ¥275,400（約96%削減！）** 🎉

---

## 🎯 Renderの特徴

### ✅ メリット
- **シンプルな設定**: AWSより圧倒的に簡単
- **自動デプロイ**: GitHubにpushするだけ
- **永続ディスク**: データが消えない（$7プラン以上）
- **無料SSL証明書**: 自動で付与
- **簡単スケーリング**: ダッシュボードでワンクリック

### ⚠️ 注意点
- **無料プランは永続化なし**: ファイルが消える
- **15分スリープ**: アクセスがないとスリープ（Starterプラン）
- **起動時間**: スリープから起動に10〜30秒

---

## 📋 移行手順（完全版）

### **ステップ1: GitHubリポジトリの準備**

#### 1-1. GitHubアカウント作成
1. https://github.com にアクセス
2. "Sign up" をクリック
3. メールアドレス・パスワードを設定

#### 1-2. 新しいリポジトリを作成
1. GitHubにログイン
2. 右上の「+」→「New repository」
3. リポジトリ名: `ai-avatar-rei`
4. プライバシー: **Private**（推奨）
5. 「Create repository」をクリック

#### 1-3. コードをプッシュ

**Windows PowerShellで実行:**

```powershell
# AI_DEPLOY_CLEANディレクトリに移動
cd "C:\Users\sugur\OneDrive\デスクトップ\REI\AI_Avator_REI_ver1.1_バックアップ最新\AI_DEPLOY_CLEAN"

# Gitの初期化（初回のみ）
git init

# 全ファイルを追加
git add .

# コミット
git commit -m "Initial commit for Render deployment"

# GitHubリポジトリと接続（<USERNAME>を自分のGitHubユーザー名に変更）
git remote add origin https://github.com/<USERNAME>/ai-avatar-rei.git

# メインブランチに変更
git branch -M main

# プッシュ
git push -u origin main
```

**⚠️ 注意:** 
- `<USERNAME>` を自分のGitHubユーザー名に変更してください
- GitHubのユーザー名とパスワード（またはPersonal Access Token）が必要です

---

### **ステップ2: Renderアカウント作成**

#### 2-1. アカウント登録
1. https://render.com にアクセス
2. 「Get Started」をクリック
3. **GitHub経由でサインアップ**（推奨）
   - 「Sign up with GitHub」をクリック
   - GitHubの認証を許可

#### 2-2. クレジットカード登録
1. ダッシュボードの「Account Settings」
2. 「Billing」タブ
3. クレジットカード情報を入力
   - **Starterプラン（$7/月）が必要**
   - 永続ディスクを使用するため

---

### **ステップ3: Web Serviceの作成**

#### 3-1. 新しいWeb Serviceを作成
1. Renderダッシュボード: https://dashboard.render.com
2. 「New +」→「Web Service」をクリック
3. GitHubリポジトリから選択:
   - リポジトリ: `ai-avatar-rei`
   - 「Connect」をクリック

#### 3-2. サービス設定

| 設定項目 | 値 |
|---|---|
| **Name** | `ai-avatar-rei` |
| **Region** | `Singapore` （日本に最も近い） |
| **Branch** | `main` |
| **Root Directory** | （空白のまま） |
| **Runtime** | `Python 3` |
| **Build Command** | `bash build.sh` |
| **Start Command** | `gunicorn application:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 --preload --log-level info` |

#### 3-3. プラン選択
- **Starter ($7/月)** を選択
- 理由: 永続ディスク（Persistent Disk）が必要

---

### **ステップ4: 環境変数の設定**

#### 4-1. Environmentタブを開く
1. Web Serviceの設定画面
2. 「Environment」タブをクリック

#### 4-2. 環境変数を追加

**必須の環境変数:**

| Key | Value | 備考 |
|---|---|---|
| `OPENAI_API_KEY` | `sk-proj-...` | OpenAI APIキー |
| `AZURE_SPEECH_KEY` | `your_azure_key` | Azure Speech APIキー |
| `AZURE_SPEECH_REGION` | `japaneast` | リージョン（日本東部） |
| `AZURE_VOICE_NAME` | `ja-JP-NanamiNeural` | 音声の種類 |

**追加方法:**
1. 「Add Environment Variable」をクリック
2. KeyとValueを入力
3. 「Save Changes」をクリック

**⚠️ 重要:**
- APIキーは絶対に公開しない
- GitHubにpushしない（.gitignoreで除外済み）

---

### **ステップ5: 永続ディスクの設定**

#### 5-1. Diskタブを開く
1. Web Serviceの設定画面
2. 「Disks」タブをクリック

#### 5-2. ディスクを追加
1. 「Add Disk」をクリック
2. 設定:
   - **Name**: `rei-persistent-storage`
   - **Mount Path**: `/opt/render/project/src/data`
   - **Size**: `1 GB`
3. 「Create Disk」をクリック

**💡 説明:**
- ChromaDBのデータベースとアップロードファイルが保存される
- アプリが再起動してもデータが保持される

---

### **ステップ6: デプロイ実行**

#### 6-1. 手動デプロイ
1. Web Serviceの画面に戻る
2. 「Manual Deploy」→「Deploy latest commit」

#### 6-2. ビルドログの確認
- ビルドプロセスが開始される
- ログをリアルタイムで確認できる
- **成功時**: 緑色で「Live」と表示

**ビルド時間: 約3〜5分**

---

### **ステップ7: 動作確認**

#### 7-1. URLを取得
- Renderが自動的にURLを生成
- 例: `https://ai-avatar-rei.onrender.com`

#### 7-2. ヘルスチェック
ブラウザで以下にアクセス:
```
https://ai-avatar-rei.onrender.com/health
```

**成功時の表示例:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-18T12:34:56.789Z",
  "active_sessions": 0,
  "visitors": 0,
  "services": {
    "openai": true,
    "rag": true,
    "coefont": false
  }
}
```

#### 7-3. アプリケーションテスト
1. トップページにアクセス
2. REIが挨拶するか確認
3. 音声が正常に再生されるか確認
4. チャット機能をテスト

---

### **ステップ8: カスタムドメインの設定（オプション）**

#### 8-1. ドメインを追加
1. Web Serviceの「Settings」
2. 「Custom Domains」セクション
3. 「Add Custom Domain」

#### 8-2. DNS設定
1. ドメイン管理サービス（お名前.comなど）にログイン
2. CNAMEレコードを追加:
   - **Name**: `www`
   - **Value**: `ai-avatar-rei.onrender.com`
3. 反映を待つ（最大48時間）

---

### **ステップ9: AWS環境の停止**

#### ⚠️ 重要: Renderで完全に動作確認してから実行

#### 9-1. Elastic Beanstalkの停止
1. AWS Management Consoleにログイン
2. Elastic Beanstalkダッシュボード
3. 環境を選択
4. 「Actions」→「Terminate Environment」

#### 9-2. 関連リソースの削除
- RDSデータベース（使用している場合）
- S3バケット（不要な場合）
- CloudWatch Logs

#### 9-3. コスト確認
- AWS Billing Dashboardで確認
- 完全に停止されているか確認

---

## 🔧 トラブルシューティング

### ❌ ビルドエラー: `chromadb` インストール失敗

**原因:** メモリ不足

**解決策:**
1. `build.sh` の ChromaDB バージョンを確認
2. Renderのプランを Standard ($25/月) にアップグレード

---

### ❌ 音声が再生されない

**原因:** Azure Speech APIキーが間違っている

**解決策:**
1. Renderダッシュボードで環境変数を確認
2. `AZURE_SPEECH_KEY` が正しいか確認
3. Azure Portalでキーを再生成

---

### ❌ アプリが起動しない

**原因:** 環境変数の設定ミス

**解決策:**
1. Renderのログを確認:
   - 「Logs」タブ
   - エラーメッセージを確認
2. 必須の環境変数が全て設定されているか確認
3. 再デプロイを実行

---

### ❌ データが消える

**原因:** 永続ディスクが設定されていない

**解決策:**
1. 「Disks」タブを確認
2. ディスクが正しくマウントされているか確認
3. Mount Path: `/opt/render/project/src/data`

---

### ❌ スリープから起動が遅い

**原因:** Starterプランの仕様

**解決策:**
- Standard プラン ($25/月) にアップグレード
- または、定期的にアクセスするスクリプトを設置

---

## 📊 監視とメンテナンス

### ログの確認
1. Renderダッシュボード
2. 「Logs」タブ
3. リアルタイムログを確認

### パフォーマンス監視
1. 「Metrics」タブ
2. CPU使用率、メモリ使用率を確認
3. レスポンス時間をモニタリング

### 自動デプロイ
- GitHubに `git push` するだけで自動デプロイ
- `main` ブランチへのpushで自動実行

---

## 🎓 よくある質問

### Q1: 無料プランは使えないの？

**A:** 
無料プランでも動きますが、以下の制限があります:
- データが消える（永続化なし）
- 15分間アクセスがないとスリープ
- ユーザーがアップロードしたファイルが消える

**→ 実用には Starter プラン ($7/月) が必須**

---

### Q2: データのバックアップは必要？

**A:**
はい、推奨します。
- Renderは自動バックアップを提供していません
- 定期的に以下をダウンロード:
  - `data/chroma_db/`
  - `uploads/`

---

### Q3: スケールアップは可能？

**A:**
可能です。
- ダッシュボードでプランを変更
- Standard ($25/月): 2GB RAM
- Pro ($85/月): 4GB RAM

---

### Q4: 複数の環境（本番・テスト）を作れる？

**A:**
可能です。
- GitHubの別ブランチ（`develop` など）を作成
- 別のWeb Serviceを作成
- 各環境に異なる環境変数を設定

---

## 📞 サポート情報

### Render公式ドキュメント
- https://render.com/docs

### Renderサポート
- https://render.com/support
- ダッシュボードから直接チャット可能

### コミュニティフォーラム
- https://community.render.com

---

## ✅ 移行チェックリスト

移行が完了したら、以下をチェック:

- [ ] GitHubリポジトリが作成されている
- [ ] Renderアカウントが作成されている
- [ ] Web Serviceが作成されている
- [ ] 環境変数が全て設定されている
- [ ] 永続ディスクが設定されている
- [ ] デプロイが成功している（「Live」表示）
- [ ] ヘルスチェックが成功している
- [ ] チャット機能が動作している
- [ ] 音声が再生されている
- [ ] 画像・動画が表示されている
- [ ] クイズ機能が動作している
- [ ] AWS環境を停止している
- [ ] AWS請求が停止されていることを確認

---

## 🎉 移行完了！

お疲れ様でした！これで年間 **¥275,400** の節約が実現しました！

**次のステップ:**
1. カスタムドメインの設定（オプション）
2. 定期的なバックアップの設定
3. 監視・アラートの設定

何か問題があれば、Renderのサポートに問い合わせてください。

---

**作成日**: 2025年10月18日  
**バージョン**: 1.0  
**対象プロジェクト**: AI Avatar REI - Kyo-Yuzen Chatbot


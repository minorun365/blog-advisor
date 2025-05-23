# Streamlit Cloud デプロイガイド

## 前提条件
- GitHubアカウント
- このプロジェクトがGitHubリポジトリにプッシュされていること

## デプロイ手順

### 1. GitHubへのコードのプッシュ
```bash
git add .
git commit -m "Ready for Streamlit Cloud deployment"
git push origin main
```

### 2. Streamlit Cloudアカウントの作成
1. [Streamlit Cloud](https://streamlit.io/cloud)にアクセス
2. "Sign up"をクリック
3. GitHubアカウントでサインイン

### 3. 新しいアプリのデプロイ
1. Streamlit Cloudダッシュボードで"New app"をクリック
2. リポジトリを選択：
   - Repository: `your-username/tech-blog-suggester`
   - Branch: `main`
   - Main file path: `app.py`
3. "Deploy!"をクリック

### 4. 環境変数の設定
デプロイが開始されたら、Secretsの設定が必要です：

1. アプリの設定画面で"Settings"タブを開く
2. "Secrets"セクションで以下の環境変数を追加：

```toml
# Google Search API
GOOGLE_API_KEY = "your_actual_google_api_key"
GOOGLE_CSE_ID = "your_actual_custom_search_engine_id"

# AWS Credentials
AWS_ACCESS_KEY_ID = "your_actual_aws_access_key"
AWS_SECRET_ACCESS_KEY = "your_actual_aws_secret_key"
AWS_REGION = "us-west-2"
```

### 5. アプリの再起動
Secretsを設定したら、アプリを再起動：
1. "Manage app"から"Reboot app"をクリック
2. 数分待つとアプリが起動します

## トラブルシューティング

### よくある問題

1. **デプロイが失敗する場合**
   - requirements.txtが正しいか確認
   - Pythonバージョンが3.11以上か確認

2. **環境変数エラー**
   - Secretsが正しく設定されているか確認
   - 変数名が.envファイルと一致しているか確認

3. **モジュールインポートエラー**
   - requirements.txtにすべての依存関係が含まれているか確認

## デプロイ後の確認

デプロイが成功したら：
- アプリのURLが表示されます（例：`https://your-app-name.streamlit.app`）
- アプリにアクセスして動作を確認
- Qiitaトレンドが正しく取得されているか確認
- ブログネタ生成機能が動作するか確認

## 注意事項

- AWS認証情報は安全に管理してください
- Streamlit CloudのSecretsは暗号化されて保存されます
- 無料プランでは月間のリソース制限があります

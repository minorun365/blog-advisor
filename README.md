# ブログネタ検討くん

エンジニア向けのブログネタを提案するAIアシスタントアプリケーションです。

## 概要

このアプリケーションは、AWS Strands AgentsとStreamlitを使用して構築されており、以下の機能を提供します：

- Qiitaの最新トレンドを分析して技術分野を動的生成
- Google Search APIとQiita APIを使用した最新トレンドの調査
- Bedrock Claude 3.7 Sonnetによる高度な分析とブログネタの提案
- ストリーミングレスポンスによるリアルタイムな結果表示

## 主な機能

- **動的カテゴリ生成**: アプリ起動時にQiitaの人気タグから最新の技術分野を自動生成
- **シャッフル機能**: 新しい技術分野をランダムに生成（Qiitaトレンドベース）
- **カスタム検索**: 自由に技術分野を入力して検索可能
- **複数の情報源**: Google検索とQiita記事の両方を参考にブログネタを提案

## セットアップ

### 1. 前提条件

- Python 3.11以上
- Google Cloud Platformアカウント（Custom Search API用）
- AWSアカウント（Bedrock用）

### 2. インストール

```bash
# リポジトリのクローン
git clone <repository-url>
cd tech-blog-suggester

# 依存関係のインストール
pip install -r requirements.txt
```

### 3. 環境変数の設定

`.env.example`を`.env`にコピーして、必要な認証情報を設定します：

```bash
cp .env.example .env
```

以下の環境変数を設定してください：

- `GOOGLE_API_KEY`: Google Cloud PlatformのAPIキー
- `GOOGLE_CSE_ID`: Custom Search EngineのID
- `AWS_ACCESS_KEY_ID`: AWSアクセスキーID
- `AWS_SECRET_ACCESS_KEY`: AWSシークレットアクセスキー
- `AWS_REGION`: AWSリージョン（デフォルト: us-west-2）

### 4. Google Custom Search APIの設定

1. [Google Cloud Console](https://console.cloud.google.com/)でプロジェクトを作成
2. Custom Search APIを有効化
3. APIキーを作成
4. [Custom Search Engine](https://cse.google.com/cse/all)で検索エンジンを作成
   - 「ウェブ全体を検索」をオンにする
   - 検索エンジンIDを取得

### 5. AWS Bedrockの設定

1. AWS Bedrockコンソールでモデルアクセスを有効化
2. Claude 3.7 Sonnet (`us.anthropic.claude-3-7-sonnet-20250219-v1:0`)へのアクセスを許可
3. IAMユーザーに必要な権限を付与

## ローカルでの実行

```bash
# Streamlitアプリケーションの起動
streamlit run app.py
```

## Streamlit Cloudへのデプロイ

### 1. GitHubへのプッシュ

```bash
git add .
git commit -m "Deploy to Streamlit Cloud"
git push origin main
```

### 2. Streamlit Cloudの設定

1. [Streamlit Cloud](https://streamlit.io/cloud)にログイン
2. 新しいアプリケーションを作成
3. GitHubリポジトリを接続
4. 環境変数をSecretsに設定

## 使い方

1. アプリケーションを起動
2. 自動生成された技術分野から選択、または自由に入力
3. AIがQiitaとWeb検索から最新トレンドを調査
4. 3つのブログネタを提案（概要、想定読者、キーポイント付き）

## 技術スタック

- **フロントエンド**: Streamlit
- **AIエージェント**: AWS Strands Agents
- **LLMモデル**: Bedrock Claude 3.7 Sonnet
- **検索API**: Google Custom Search API, Qiita API
- **パッケージ管理**: pip

## ファイル構成

```
tech-blog-suggester/
├── app.py                 # メインアプリケーション
├── utils/                 # ユーティリティモジュール
│   ├── agent_setup.py     # Strands Agentの設定
│   ├── category_generator.py  # カテゴリ生成
│   ├── qiita_trends.py    # Qiitaトレンド取得
│   └── search_tools.py    # 検索ツール
├── requirements.txt       # 依存関係
├── .env.example          # 環境変数のテンプレート
└── README.md             # このファイル
```

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

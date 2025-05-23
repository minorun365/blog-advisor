"""技術分野を動的に生成するユーティリティ"""

import random
from strands import Agent
from strands.models import BedrockModel
import boto3
import os
from dotenv import load_dotenv
from .qiita_trends import get_qiita_trending_categories

# 環境変数を読み込む
load_dotenv()


def generate_tech_categories(num_categories: int = 8):
    """LLMを使用してQiitaのトレンドを参考に技術分野を動的に生成"""
    
    # Qiitaのトレンド情報を取得
    qiita_trends = get_qiita_trending_categories()
    
    # Bedrockセッションの作成
    session = boto3.Session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION", "us-west-2")
    )
    
    # Bedrockモデルを初期化
    bedrock_model = BedrockModel(
        model_id="us.anthropic.claude-3-haiku-20240307-v1:0",
        boto_session=session,
        temperature=0.9,  # 多様性のために高めに設定
        max_tokens=1000
    )
    
    # エージェントの作成
    agent = Agent(
        model=bedrock_model,
        callback_handler=None,
        system_prompt="あなたはIT技術のトレンドに詳しい専門家です。"
    )
    
    # 現在のトレンドを考慮したプロンプト
    current_trends = random.choice([
        "Qiitaで現在人気の技術",
        "Qiitaで話題になっている技術",
        "エンジニアが今注目している技術",
        "Qiitaのトレンドから見る最新技術",
        "今月Qiitaで盛り上がっている技術"
    ])
    
    # Qiitaの人気タグを文字列として整形
    popular_tags_str = ", ".join(qiita_trends.get("all_popular_tags", [])[:15])
    
    # カテゴリ別のタグ情報を整形
    categorized_info = qiita_trends.get("categorized", {})
    
    prompt = f"""
    {current_trends}を考慮して、エンジニア向けのブログネタとして面白そうな技術分野を{num_categories}個生成してください。

    【Qiitaで現在人気のタグ】
    {popular_tags_str}

    【カテゴリ別の人気タグ】
    - フロントエンド: {", ".join(categorized_info.get("frontend", [])[:5])}
    - バックエンド: {", ".join(categorized_info.get("backend", [])[:5])}
    - AI/機械学習: {", ".join(categorized_info.get("ai_ml", [])[:5])}
    - クラウド/インフラ: {", ".join(categorized_info.get("cloud", [])[:5])}
    - モバイル: {", ".join(categorized_info.get("mobile", [])[:5])}
    - その他: {", ".join(categorized_info.get("other", [])[:5])}

    以下の条件を満たしてください：
    1. 各分野は具体的で、ブログネタとして書きやすいもの
    2. 初心者から上級者まで興味を持てる分野
    3. Qiitaの人気タグを参考にしつつ、新しい切り口も含める
    4. 各分野に適切な絵文字を付ける
    5. 上記のQiitaの人気タグから少なくとも半分は関連するカテゴリを含める

    以下の形式で出力してください（JSONフォーマット）：
    {{
        "分野名1": {{
            "keywords": ["キーワード1", "キーワード2", ...],
            "emoji": "🔧"
        }},
        "分野名2": {{
            "keywords": ["キーワード1", "キーワード2", ...],
            "emoji": "🌟"
        }}
    }}

    注意：
    - 分野名は日本語で15文字以内
    - キーワードは3〜6個
    - 絵文字は必ず1つ
    """
    
    try:
        result = agent(prompt)
        
        # レスポンスからJSONを抽出
        import json
        import re
        
        # レスポンステキストを取得
        # content[0]が辞書型の場合と、直接textプロパティがある場合の両方に対応
        content = result.message['content'][0]
        if isinstance(content, dict) and 'text' in content:
            response_text = content['text']
        elif hasattr(content, 'text'):
            response_text = content.text
        else:
            # フォールバック
            response_text = str(content)
        
        # JSON部分を抽出（```jsonブロックがある場合も考慮）
        json_match = re.search(r'(\{[\s\S]*\})', response_text)
        if json_match:
            json_str = json_match.group(1)
            categories = json.loads(json_str)
            return categories
        else:
            # フォールバックとして固定のカテゴリを返す
            return get_fallback_categories()
            
    except Exception as e:
        print(f"カテゴリ生成エラー: {str(e)}")
        # エラー時はフォールバックを返す
        return get_fallback_categories()


def get_fallback_categories():
    """エラー時のフォールバックカテゴリ"""
    return {
        "AI/機械学習": {
            "keywords": ["LLM", "深層学習", "自然言語処理", "画像認識"],
            "emoji": "🤖"
        },
        "Web開発": {
            "keywords": ["React", "Next.js", "Vue.js", "TypeScript"],
            "emoji": "🌐"
        },
        "クラウド/インフラ": {
            "keywords": ["AWS", "GCP", "Kubernetes", "Docker"],
            "emoji": "☁️"
        },
        "セキュリティ": {
            "keywords": ["ゼロトラスト", "脆弱性診断", "暗号化"],
            "emoji": "🔒"
        }
    }

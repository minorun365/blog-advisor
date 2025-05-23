"""Strands Agentの設定"""

import os
import boto3
from strands import Agent
from strands.models import BedrockModel
from utils.search_tools import google_search, qiita_search, format_qiita_results_for_blog
from utils.langfuse_setup import setup_langfuse_tracing, get_trace_attributes
from dotenv import load_dotenv

# 環境変数を読み込む
load_dotenv()

# Langfuseトレーシングを設定
LANGFUSE_ENABLED = setup_langfuse_tracing()


def create_blog_suggester_agent(session_id: str | None = None, user_id: str | None = None, tags: list | None = None, trace_id: str | None = None):
    """ブログネタ提案用のエージェントを作成
    
    Args:
        session_id: Langfuse用のセッションID（オプション）
        user_id: Langfuse用のユーザーID（オプション）
        tags: Langfuse用のタグリスト（オプション）
        trace_id: Langfuse用のトレースID（一連の操作をまとめるため）
    
    Returns:
        Agent: 設定されたStrands Agent
    """
    
    # boto3セッションの作成
    session = boto3.Session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION", "us-west-2")
    )
    
    # Bedrock Claude 3.7 Sonnetの設定（USクロスリージョン）
    bedrock_model = BedrockModel(
        model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",  # Claude 3.7 Sonnet (US cross-region)
        boto_session=session,
        temperature=0.7,  # クリエイティブな提案のために少し高めに設定
        max_tokens=1500  # タイムアウト対策のため、少し短めに設定
    )
    
    # Langfuseのトレース属性を準備（Langfuseが有効な場合のみ）
    trace_attributes = None
    if LANGFUSE_ENABLED:
        trace_attributes = get_trace_attributes(
            session_id=session_id,
            user_id=user_id,
            tags=tags,
            trace_id=trace_id
        )
    
    # エージェントの作成
    agent = Agent(
        model=bedrock_model,
        tools=[google_search, qiita_search, format_qiita_results_for_blog],  # Qiita検索ツールを追加
        callback_handler=None,  # Streamlitで独自に処理するため無効化
        trace_attributes=trace_attributes,  # Langfuseトレース属性を追加
        system_prompt="""あなたはエンジニア向けのブログネタを提案する専門家です。
        
        以下の役割を持っています：
        1. 選択された技術分野の最新トレンドを調査
        2. エンジニアが興味を持ちそうなトピックを発見
        3. 実践的で価値のあるブログネタを提案
        
        提案する際は以下を心がけてください：
        - 技術的に正確で最新の情報に基づく提案
        - 初心者から上級者まで幅広い読者を想定
        - 実装例やコードサンプルを含められるような具体的なネタ
        - トレンドを踏まえつつ、長期的に価値のある内容
        
        必ず日本語で回答してください。"""
    )
    
    return agent

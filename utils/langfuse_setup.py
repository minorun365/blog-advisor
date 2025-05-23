"""Langfuseの設定とトレース属性の準備"""

import os
import base64
from dotenv import load_dotenv

# 環境変数を読み込む
load_dotenv()


def setup_langfuse_tracing():
    """
    Langfuseのトレーシングを設定
    
    Returns:
        bool: Langfuseが有効化されているかどうか
    """
    # Langfuseの認証情報を確認
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    langfuse_host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    
    if not public_key or not secret_key:
        print("Langfuse credentials not found. Tracing will be disabled.")
        return False
    
    # OpenTelemetryのエンドポイントを設定
    otel_endpoint = f"{langfuse_host}/api/public/otel/v1/traces"
    
    # Basic認証トークンを作成
    auth_token = base64.b64encode(
        f"{public_key}:{secret_key}".encode()
    ).decode()
    
    # OpenTelemetry環境変数を設定
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = otel_endpoint
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {auth_token}"
    
    print(f"Langfuse tracing enabled. Endpoint: {langfuse_host}")
    return True


def get_trace_attributes(session_id: str | None = None, user_id: str | None = None, tags: list | None = None, trace_id: str | None = None):
    """
    Langfuse用のトレース属性を生成
    
    Args:
        session_id: セッションID（チャットスレッドなど）
        user_id: ユーザーID
        tags: タグのリスト
        trace_id: トレースID（一連の操作をまとめるため）
    
    Returns:
        dict: トレース属性の辞書
    """
    attributes = {}
    
    # トレースIDを追加（重要：一連の操作を同じトレースにまとめる）
    if trace_id:
        attributes["trace.id"] = trace_id
    
    # セッションIDを追加
    if session_id:
        attributes["session.id"] = session_id
    
    # ユーザーIDを追加
    if user_id:
        attributes["user.id"] = user_id
    
    # タグを追加
    if tags:
        attributes["langfuse.tags"] = tags
    else:
        # デフォルトタグ
        attributes["langfuse.tags"] = ["tech-blog-suggester", "strands-agent"]
    
    # アプリケーション情報を追加
    attributes["app.name"] = "Tech Blog Suggester"
    attributes["app.version"] = "1.0.0"
    
    return attributes

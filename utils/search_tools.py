"""検索APIを使用するカスタムツール"""

import os
from typing import List, Dict, Any
from strands import tool
from googleapiclient.discovery import build
from dotenv import load_dotenv
from .qiita_trends import search_qiita_articles

# 環境変数を読み込む
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")


@tool
def google_search(query: str, num_results: int = 10) -> List[Dict[str, Any]]:
    """
    Google Custom Search APIを使用してWeb検索を実行
    
    Args:
        query: 検索クエリ
        num_results: 取得する結果数（最大10）
    
    Returns:
        検索結果のリスト（各結果は辞書形式）
    """
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        return [{
            "error": "Google API credentials not configured. Please set GOOGLE_API_KEY and GOOGLE_CSE_ID."
        }]
    
    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        
        result = service.cse().list(
            q=query,
            cx=GOOGLE_CSE_ID,
            lr='lang_ja',  # 日本語の結果を優先
            num=min(num_results, 10),  # 最大10件
            dateRestrict='m1'  # 過去1ヶ月以内の結果を優先
        ).execute()
        
        items = result.get('items', [])
        
        # 結果を整形して返す
        formatted_results = []
        for item in items:
            formatted_results.append({
                'title': item.get('title', ''),
                'link': item.get('link', ''),
                'snippet': item.get('snippet', ''),
                'displayLink': item.get('displayLink', '')
            })
        
        return formatted_results
    
    except Exception as e:
        return [{
            "error": f"Search failed: {str(e)}"
        }]


@tool
def format_search_results_for_blog(search_results: List[Dict[str, Any]]) -> str:
    """
    検索結果をブログネタ提案用に整形
    
    Args:
        search_results: google_searchツールから返された検索結果
    
    Returns:
        整形された検索結果の文字列
    """
    if not search_results:
        return "検索結果が見つかりませんでした。"
    
    if len(search_results) == 1 and "error" in search_results[0]:
        return f"エラー: {search_results[0]['error']}"
    
    formatted = "## 最新の技術トレンド\n\n"
    
    for i, result in enumerate(search_results, 1):
        formatted += f"### {i}. {result.get('title', 'タイトルなし')}\n"
        formatted += f"- **URL**: {result.get('link', '')}\n"
        formatted += f"- **概要**: {result.get('snippet', '説明なし')}\n"
        formatted += f"- **サイト**: {result.get('displayLink', '')}\n\n"
    
    return formatted


@tool
def qiita_search(query: str, num_results: int = 10) -> List[Dict[str, Any]]:
    """
    Qiitaで記事を検索
    
    Args:
        query: 検索クエリ
        num_results: 取得する結果数（最大100）
    
    Returns:
        検索結果のリスト（各結果は辞書形式）
    """
    try:
        # Qiitaの検索を実行
        articles = search_qiita_articles(query, per_page=num_results)
        
        if not articles:
            return [{
                "error": "Qiitaの検索結果が見つかりませんでした。"
            }]
        
        return articles
    
    except Exception as e:
        return [{
            "error": f"Qiita検索に失敗しました: {str(e)}"
        }]


@tool
def format_qiita_results_for_blog(qiita_results: List[Dict[str, Any]]) -> str:
    """
    Qiitaの検索結果をブログネタ提案用に整形
    
    Args:
        qiita_results: qiita_searchツールから返された検索結果
    
    Returns:
        整形された検索結果の文字列
    """
    if not qiita_results:
        return "Qiitaの検索結果が見つかりませんでした。"
    
    if len(qiita_results) == 1 and "error" in qiita_results[0]:
        return f"エラー: {qiita_results[0]['error']}"
    
    formatted = "## Qiitaの関連記事\n\n"
    
    for i, result in enumerate(qiita_results, 1):
        formatted += f"### {i}. {result.get('title', 'タイトルなし')}\n"
        formatted += f"- **URL**: {result.get('url', '')}\n"
        formatted += f"- **タグ**: {', '.join(result.get('tags', []))}\n"
        formatted += f"- **いいね数**: {result.get('likes_count', 0)}\n"
        formatted += f"- **投稿者**: {result.get('user', '不明')}\n\n"
    
    return formatted

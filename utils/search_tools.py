"""検索APIを使用するカスタムツール"""

import os
import requests
from typing import List, Dict, Any
from strands import tool
from googleapiclient.discovery import build
from dotenv import load_dotenv
from .qiita_trends import search_qiita_articles

# 環境変数を読み込む
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


def tavily_search_api(query: str, num_results: int = 10) -> List[Dict[str, Any]]:
    """
    Tavily Search APIを使用してWeb検索を実行（内部関数）
    
    Args:
        query: 検索クエリ
        num_results: 取得する結果数（最大20）
    
    Returns:
        検索結果のリスト（各結果は辞書形式）
    """
    try:
        response = requests.post(
            "https://api.tavily.com/search",
            headers={
                "Authorization": f"Bearer {TAVILY_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "query": query,
                "topic": "general",
                "search_depth": "basic",
                "max_results": min(num_results, 20),
                "include_answer": False
            },
            timeout=10
        )
        
        response.raise_for_status()
        data = response.json()
        
        # 結果を整形して返す
        formatted_results = []
        for result in data.get('results', []):
            formatted_results.append({
                'title': result.get('title', ''),
                'link': result.get('url', ''),
                'snippet': result.get('content', ''),
                'displayLink': result.get('url', '').split('/')[2] if result.get('url') else ''
            })
        
        return formatted_results
        
    except Exception as e:
        return [{
            "error": f"Tavily search failed: {str(e)}"
        }]


@tool
def google_search(query: str, num_results: int = 10) -> List[Dict[str, Any]]:
    """
    Google Custom Search APIを使用してWeb検索を実行。
    クォータ制限に達した場合はTavily検索をフォールバックとして使用。
    
    Args:
        query: 検索クエリ
        num_results: 取得する結果数（最大10）
    
    Returns:
        検索結果のリスト（各結果は辞書形式）
    """
    # まずGoogle検索を試す
    if GOOGLE_API_KEY and GOOGLE_CSE_ID:
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
            error_msg = str(e)
            # クォータ制限エラーをチェック
            if "quota" in error_msg.lower() or "limit" in error_msg.lower():
                print(f"Google検索のクォータ制限に達しました。Tavily検索にフォールバックします。")
                # Tavily検索にフォールバック
                if TAVILY_API_KEY:
                    return tavily_search_api(query, num_results)
            
            # その他のエラーの場合もTavily検索を試す
            if TAVILY_API_KEY:
                print(f"Google検索エラー: {error_msg}. Tavily検索にフォールバックします。")
                return tavily_search_api(query, num_results)
            
            return [{
                "error": f"Google search failed: {error_msg}"
            }]
    
    # Google APIが設定されていない場合、Tavily検索を使用
    elif TAVILY_API_KEY:
        return tavily_search_api(query, num_results)
    
    # どちらのAPIも設定されていない場合
    else:
        return [{
            "error": "No search API configured. Please set either Google API (GOOGLE_API_KEY and GOOGLE_CSE_ID) or TAVILY_API_KEY."
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


@tool
def tavily_search(query: str, num_results: int = 10, search_depth: str = "basic") -> List[Dict[str, Any]]:
    """
    Tavily Search APIを使用してWeb検索を実行（独立したツール）。
    Google検索のクォータ制限を回避したい場合に直接使用可能。
    
    Args:
        query: 検索クエリ
        num_results: 取得する結果数（最大20）
        search_depth: 検索深度（"basic"または"advanced"）
    
    Returns:
        検索結果のリスト（各結果は辞書形式）
    """
    if not TAVILY_API_KEY:
        return [{
            "error": "TAVILY_API_KEY is not configured. Please set it in .env file."
        }]
    
    try:
        response = requests.post(
            "https://api.tavily.com/search",
            headers={
                "Authorization": f"Bearer {TAVILY_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "query": query,
                "topic": "general",
                "search_depth": search_depth,
                "max_results": min(num_results, 20),
                "include_answer": True,  # AIによる回答も含める
                "include_images": False,
                "time_range": "month"  # 過去1ヶ月以内の結果を優先
            },
            timeout=10
        )
        
        response.raise_for_status()
        data = response.json()
        
        # 結果を整形して返す
        formatted_results = []
        
        # AIの回答があれば最初に追加
        if data.get('answer'):
            formatted_results.append({
                'title': '📝 AI Summary',
                'link': '',
                'snippet': data['answer'],
                'displayLink': 'Tavily AI'
            })
        
        # 検索結果を追加
        for result in data.get('results', []):
            formatted_results.append({
                'title': result.get('title', ''),
                'link': result.get('url', ''),
                'snippet': result.get('content', ''),
                'displayLink': result.get('url', '').split('/')[2] if result.get('url') else '',
                'score': result.get('score', 0)  # 関連性スコア
            })
        
        return formatted_results
        
    except requests.exceptions.Timeout:
        return [{
            "error": "Tavily search timeout. Please try again."
        }]
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            return [{
                "error": "Tavily API rate limit exceeded. Please try again later."
            }]
        elif e.response.status_code == 401:
            return [{
                "error": "Invalid Tavily API key. Please check your configuration."
            }]
        else:
            return [{
                "error": f"Tavily HTTP error: {e.response.status_code}"
            }]
    except Exception as e:
        return [{
            "error": f"Tavily search failed: {str(e)}"
        }]

"""Qiitaのトレンドを取得するユーティリティ"""

import requests
from typing import List, Dict, Any, Union
import json


def get_qiita_popular_articles(page: int = 1, per_page: int = 100) -> List[Dict]:
    """
    Qiitaの人気記事を取得
    
    Args:
        page: ページ番号
        per_page: 1ページあたりの記事数（最大100）
        
    Returns:
        記事のリスト
    """
    
    # Qiita API v2のエンドポイント
    url = "https://qiita.com/api/v2/items"
    
    # パラメータの設定
    # ストック数順でソート（人気記事として）
    params = {
        "page": page,
        "per_page": per_page,
        "query": "stocks:>50"  # ストック数が50以上の記事を取得
    }
    
    # ヘッダーの設定
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        articles = response.json()
        return articles
        
    except requests.exceptions.RequestException as e:
        print(f"Qiita API エラー: {str(e)}")
        return []


def extract_popular_tags_from_articles(articles: List[Dict], top_n: int = 20) -> List[Dict[str, int]]:
    """
    記事からタグを抽出して、出現頻度順に並べる
    
    Args:
        articles: Qiitaの記事リスト
        top_n: 上位何個のタグを返すか
        
    Returns:
        タグと出現回数のリスト
    """
    tag_count = {}
    
    for article in articles:
        # 各記事のタグを取得
        for tag in article.get("tags", []):
            tag_name = tag.get("name", "")
            if tag_name:
                tag_count[tag_name] = tag_count.get(tag_name, 0) + 1
    
    # 出現頻度順にソート
    sorted_tags = sorted(tag_count.items(), key=lambda x: x[1], reverse=True)
    
    # 上位N個を返す
    return [{"name": tag[0], "count": tag[1]} for tag in sorted_tags[:top_n]]


def search_qiita_articles(query: str, per_page: int = 10) -> List[Dict]:
    """
    Qiitaで特定のキーワードで記事を検索
    
    Args:
        query: 検索クエリ
        per_page: 取得する記事数
        
    Returns:
        検索結果の記事リスト
    """
    url = "https://qiita.com/api/v2/items"
    
    params = {
        "page": 1,
        "per_page": per_page,
        "query": query
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        articles = response.json()
        
        # 記事情報を整形
        formatted_articles = []
        for article in articles:
            formatted_articles.append({
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "tags": [tag.get("name", "") for tag in article.get("tags", [])],
                "likes_count": article.get("likes_count", 0),
                "created_at": article.get("created_at", ""),
                "user": article.get("user", {}).get("id", "")
            })
        
        return formatted_articles
        
    except requests.exceptions.RequestException as e:
        print(f"Qiita検索エラー: {str(e)}")
        return []


def get_qiita_trending_categories() -> Dict[str, Any]:
    """
    Qiitaのトレンドからカテゴリを生成するための情報を取得
    
    Returns:
        カテゴリ生成に使用する情報の辞書
    """
    # 人気記事を取得（最新の100件）
    articles = get_qiita_popular_articles(page=1, per_page=100)
    
    if not articles:
        # エラー時はデフォルトのトレンドを返す
        return {
            "popular_tags": ["React", "Python", "Docker", "AWS", "TypeScript"],
            "trending_topics": ["生成AI", "LLM", "Next.js", "Rust", "Kubernetes"]
        }
    
    # 人気タグを抽出
    popular_tags = extract_popular_tags_from_articles(articles, top_n=30)
    
    # タグ名のリストを作成
    tag_names = [tag["name"] for tag in popular_tags]
    
    # カテゴリ化しやすいようにグループ分け
    # （これはヒューリスティックな分類）
    categories_hints = {
        "frontend": [],
        "backend": [],
        "ai_ml": [],
        "cloud": [],
        "mobile": [],
        "other": []
    }
    
    # タグを簡単に分類
    for tag in tag_names:
        # tagがstring型であることを確認
        if not isinstance(tag, str):
            continue
        tag_lower = tag.lower()
        
        if any(keyword in tag_lower for keyword in ["react", "vue", "angular", "typescript", "javascript", "css", "html", "nextjs", "nuxt"]):
            categories_hints["frontend"].append(tag)
        elif any(keyword in tag_lower for keyword in ["python", "ruby", "go", "rust", "java", "node", "django", "rails", "fastapi"]):
            categories_hints["backend"].append(tag)
        elif any(keyword in tag_lower for keyword in ["ai", "ml", "機械学習", "深層学習", "llm", "chatgpt", "gpt", "claude"]):
            categories_hints["ai_ml"].append(tag)
        elif any(keyword in tag_lower for keyword in ["aws", "gcp", "azure", "docker", "kubernetes", "terraform", "cloud"]):
            categories_hints["cloud"].append(tag)
        elif any(keyword in tag_lower for keyword in ["ios", "android", "flutter", "react native", "swift", "kotlin"]):
            categories_hints["mobile"].append(tag)
        else:
            categories_hints["other"].append(tag)
    
    # 最終的な返却値
    return {
        "all_popular_tags": tag_names[:20],  # 上位20個の人気タグ
        "categorized": categories_hints,
        "raw_tags": popular_tags[:10]  # 生のタグ情報（上位10個）
    }


if __name__ == "__main__":
    # テスト実行
    trends = get_qiita_trending_categories()
    print(json.dumps(trends, ensure_ascii=False, indent=2))

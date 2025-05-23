"""
Tech Blog Suggester - エンジニア向けブログネタ提案アプリ
"""

import asyncio
import streamlit as st
import nest_asyncio
from utils.agent_setup import create_blog_suggester_agent
from utils.category_generator import generate_tech_categories

# 非同期処理の設定
nest_asyncio.apply()

# ページ設定
st.set_page_config(
    page_title="#ブログネタ検討くん",
    page_icon="📝",
    layout="wide"
)

# タイトルと説明
st.title("# ブログネタ検討くん")
st.markdown("""
エンジニア向けのブログネタを提案するAIエージェントです。  
AWS発のOSS「Strands Agents」フレームワークと、BedrockのClaude 3.7 Sonnetを使っています。
""")

# セッション状態の初期化
if "selected_category" not in st.session_state:
    st.session_state.selected_category = None
if "agent_response" not in st.session_state:
    st.session_state.agent_response = None
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False
if "tech_categories" not in st.session_state:
    st.session_state.tech_categories = None
if "is_generating_categories" not in st.session_state:
    st.session_state.is_generating_categories = False


async def process_with_agent(category: str, keywords: list):
    """エージェントを使用してブログネタを生成"""
    # エージェントの作成
    agent = create_blog_suggester_agent()
    
    # プロンプトの作成
    prompt = f"""
    技術分野「{category}」に関する最新のトレンドを調査して、ブログネタを提案してください。
    
    関連キーワード: {', '.join(keywords)}
    
    以下の手順で実行してください：
    1. まず、関連キーワードを使って以下の検索を実行：
       - Qiitaで記事を検索（qiita_searchツールを使用、5件程度）
       - 必要に応じてWeb検索も実行（google_searchツールを使用、3件程度）
    2. Qiitaの人気記事の傾向を分析し、どのような切り口が注目されているか把握
    3. 検索結果から、エンジニアが興味を持ちそうなトピックを特定
    4. 具体的なブログネタを3つ提案
    
    各ブログネタは以下の形式で簡潔に：
    ## タイトル案
    - 概要: 2-3文で説明
    - 想定読者: 初心者/中級者/上級者
    - キーポイント: 3つまで
    
    重要：
    - Qiitaの記事を優先的に参考にしてください（エンジニアコミュニティの関心事を反映）
    - 検索結果を分析した上で、実践的で価値のあるネタを提案してください
    - すでに多く書かれているテーマでも、新しい切り口があれば提案してください
    """
    
    # ストリーミングで結果を取得
    agent_stream = agent.stream_async(prompt=prompt)
    
    full_response = ""
    placeholder = st.empty()
    tool_status_placeholder = st.empty()
    
    async for event in agent_stream:
        if "data" in event:
            # テキストデータを追加
            full_response += event["data"]
            # Markdownで表示を更新
            placeholder.markdown(full_response)
            # ツール実行ステータスをクリア
            tool_status_placeholder.empty()
            
        elif "current_tool_use" in event and event["current_tool_use"].get("name"):
            # ツール使用情報を取得
            tool_name = event["current_tool_use"]["name"]
            
            # ツールごとのメッセージを設定
            tool_messages = {
                "google_search": "🔍 Web検索中...",
                "qiita_search": "🔍 Qiitaで関連記事を検索中...",
                "format_search_results_for_blog": "📝 検索結果を分析中...",
                "format_qiita_results_for_blog": "📝 Qiitaの記事を分析中...",
            }
            
            message = tool_messages.get(tool_name, f"🔧 {tool_name}を実行中...")
            
            # ツール実行中のステータスを表示
            tool_status_placeholder.info(message)
    
    # 最後にステータスをクリア
    tool_status_placeholder.empty()
    
    return full_response


def main():
    """メイン処理"""
    
    # 初回起動時もQiitaトレンドから生成
    if st.session_state.tech_categories is None:
        st.session_state.is_generating_categories = True
    
    # カテゴリ生成処理（初回起動時とシャッフル時）
    if st.session_state.is_generating_categories:
        with st.spinner("🎲 Qiitaの最新トレンドからカテゴリを生成中..."):
            try:
                st.session_state.tech_categories = generate_tech_categories()
                st.session_state.is_generating_categories = False
                st.rerun()
            except Exception as e:
                st.error(f"カテゴリ生成エラー: {str(e)}")
                st.session_state.is_generating_categories = False
    
    # 技術分野の選択
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("🎯 興味のある技術分野を選択してください")
    with col2:
        if st.button("🎲 シャッフル", 
                    disabled=st.session_state.is_processing,
                    help="新しい技術分野を生成します"):
            st.session_state.is_generating_categories = True
            st.session_state.selected_category = None
            st.session_state.agent_response = None
            st.rerun()
    
    # カテゴリが存在する場合のみ表示
    if st.session_state.tech_categories:
        # ボタンを2列に配置
        cols = st.columns(2)
        
        for idx, (category, info) in enumerate(st.session_state.tech_categories.items()):
            col = cols[idx % 2]
            with col:
                if st.button(
                    f"{info['emoji']} {category}", 
                    key=f"cat_{category}",
                    use_container_width=True,
                    disabled=st.session_state.is_processing
                ):
                    st.session_state.selected_category = category
                    st.session_state.agent_response = None
        
        # 自由記入フィールド
        st.divider()
        col1, col2 = st.columns([3, 1])
        with col1:
            custom_category = st.text_input(
                "または、技術分野を自由に入力してください",
                placeholder="例: WebAssembly、量子コンピューティング、AWS など",
                disabled=st.session_state.is_processing,
                key="custom_category_input"
            )
        with col2:
            if st.button("🚀 検索", 
                        disabled=st.session_state.is_processing or not custom_category,
                        use_container_width=True):
                st.session_state.selected_category = custom_category
                st.session_state.agent_response = None
                # カスタムカテゴリをセッションに追加（再利用可能にする）
                if custom_category not in st.session_state.tech_categories:
                    st.session_state.tech_categories[custom_category] = {
                        "keywords": [custom_category],  # カテゴリ名をキーワードとして使用
                        "emoji": "🔍"
                    }
        
        # 選択された分野がある場合
        if st.session_state.selected_category and not st.session_state.agent_response:
            category = st.session_state.selected_category
            keywords = st.session_state.tech_categories[category]["keywords"]
            
            st.divider()
            st.subheader(f"🔍 「{category}」のブログネタを生成中...")
            
            # 処理中フラグを設定
            st.session_state.is_processing = True
            
            # 非同期処理を実行
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                response = loop.run_until_complete(
                    process_with_agent(category, keywords)
                )
                st.session_state.agent_response = response
                st.session_state.is_processing = False
                st.rerun()
            except Exception as e:
                st.error(f"エラーが発生しました: {str(e)}")
                st.session_state.is_processing = False
            finally:
                loop.close()
        
        # 結果の表示
        if st.session_state.agent_response:
            st.divider()
            st.subheader(f"✨ 「{st.session_state.selected_category}」のブログネタ提案")
            st.markdown(st.session_state.agent_response)
            
            # リセットボタン
            if st.button("🔄 別の分野を選択", type="secondary"):
                st.session_state.selected_category = None
                st.session_state.agent_response = None
                st.rerun()


if __name__ == "__main__":
    main()

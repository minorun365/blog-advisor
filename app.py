import asyncio
import re
import urllib.parse
import uuid
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
AWS発のOSS「Strands Agents」フレームワークと、Amazon BedrockのClaudeモデルを使っています。
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
if "tweet_summary" not in st.session_state:
    st.session_state.tweet_summary = None
if "session_id" not in st.session_state:
    # セッションIDを生成（Langfuseのトレース用）
    st.session_state.session_id = str(uuid.uuid4())
if "current_trace_id" not in st.session_state:
    # 現在の操作フローのトレースID
    st.session_state.current_trace_id = None


async def process_with_agent(category: str, keywords: list):
    """エージェントを使用してブログネタを生成"""
    # エージェントの作成（Langfuseトレース属性を含む）
    agent = create_blog_suggester_agent(
        session_id=st.session_state.session_id,
        tags=["blog-idea-generation", category],
        trace_id=st.session_state.current_trace_id
    )
    
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


async def summarize_blog_ideas(response: str, category: str) -> str:
    """ブログネタの提案を要約してXポスト用のテキストを生成"""
    # エージェントを作成（Langfuseトレース属性を含む）
    agent = create_blog_suggester_agent(
        session_id=st.session_state.session_id,
        tags=["tweet-summary", category],
        trace_id=st.session_state.current_trace_id  # 同じトレースIDを使用
    )
    
    # 要約プロンプト
    prompt = f"""
    以下のブログネタ提案から、主要なトピックを2-3個抽出して、Xポスト用の要約を作成してください。
    ※ この出力内容はそのままポストされるため、「分かりました。〜」といった前置きや、「〜いかがでしょうか。」などの余計な文は一切不要です。
    ポスト内容のみを出力してください。

    フォーマット：
    「#ブログネタ検討くん に技術アウトプットの題材を考えてもらいました！[トピック1]や[トピック2]についてブログを書いてみようと思います💪」

    条件：
    - 日本語120文字以内
    - トピックは具体的な技術名やテーマを使用
    - 絵文字は指定されたもののみ使用
    - ハッシュタグは「#ブログネタ検討くん」のみ

    ブログネタ提案：
    {response}

    分野：{category}

    注意：
    この出力内容はそのままポストされるため、「分かりました。〜」といった前置きや、「〜いかがでしょうか。」などの余計な文は一切不要です。
    ポスト内容のみを出力してください。
    """
    
    # 同期的に実行
    try:
        result = agent(prompt)
        # より安全な方法でテキストを取得
        content = result.message.get('content', [])
        if content and len(content) > 0:
            # 'text'属性を安全に取得
            text_content = content[0].get('text', '')
            if text_content:
                return text_content.strip()
        
        # フォールバック
        return f"#ブログネタ検討くん に技術アウトプットの題材を考えてもらいました！{category}についてブログを書いてみようと思います💪"
    except Exception as e:
        # エラーログを出力してフォールバック
        print(f"要約生成エラー: {str(e)}")
        return f"#ブログネタ検討くん に技術アウトプットの題材を考えてもらいました！{category}についてブログを書いてみようと思います💪"


def create_twitter_share_url(text: str) -> str:
    """X（Twitter）共有用のURLを生成"""
    encoded_text = urllib.parse.quote(text)
    return f"https://twitter.com/intent/tweet?text={encoded_text}"


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
                    # 新しい操作フローのためにトレースIDを生成
                    st.session_state.current_trace_id = str(uuid.uuid4())
        
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
                # 新しい操作フローのためにトレースIDを生成
                st.session_state.current_trace_id = str(uuid.uuid4())
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
            
            # アクションボタン
            st.divider()
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # リセットボタン
                if st.button("🔄 別の分野を選択", type="secondary", use_container_width=True):
                    st.session_state.selected_category = None
                    st.session_state.agent_response = None
                    st.session_state.tweet_summary = None
                    # トレースIDもリセット
                    st.session_state.current_trace_id = None
                    st.rerun()
            
            with col2:
                # Xにポストするボタン（要約生成付き）
                if st.session_state.tweet_summary is None:
                    if st.button("🐦 Xにポストする", type="primary", use_container_width=True):
                        with st.spinner("ポスト用テキストを生成中..."):
                            # 非同期処理を実行
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            
                            try:
                                summary_text = loop.run_until_complete(
                                    summarize_blog_ideas(
                                        st.session_state.agent_response, 
                                        st.session_state.selected_category
                                    )
                                )
                                st.session_state.tweet_summary = summary_text
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"エラーが発生しました: {str(e)}")
                            finally:
                                loop.close()
                else:
                    # 要約が生成済みの場合、リンクボタンを表示
                    twitter_url = create_twitter_share_url(st.session_state.tweet_summary)
                    st.markdown(
                        f'<a href="{twitter_url}" target="_blank" style="text-decoration: none;">'
                        f'<button style="background-color: #1DA1F2; color: white; border: none; '
                        f'padding: 10px 20px; border-radius: 5px; cursor: pointer; '
                        f'font-size: 16px; width: 100%;">🐦 Xで共有する</button></a>',
                        unsafe_allow_html=True
                    )
                    
                    # 要約テキストを表示
                    with st.expander("投稿内容を確認"):
                        st.text(st.session_state.tweet_summary)


if __name__ == "__main__":
    main()

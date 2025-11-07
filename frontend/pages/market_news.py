"""
Market News Page - LangChain-powered news aggregator
Displays latest equity mutual fund news with filtering and search
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from frontend.utils.api_client import APIClient

api = APIClient()


def render():
    """Render market news page"""
    
    st.markdown("# 📰 Market News")
    st.markdown("Latest news about equity mutual funds and Indian markets")
    st.markdown("---")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📰 Latest News", "🔍 Search Topics", "ℹ️ Sources"])
    
    with tab1:
        render_latest_news()
    
    with tab2:
        render_topic_search()
    
    with tab3:
        render_sources_info()


def render_latest_news():
    """Render latest news section"""
    
    st.markdown("### 📰 Latest Market News")
    
    # Settings
    col1, col2, col3 = st.columns(3)
    
    with col1:
        limit = st.slider(
            "Number of articles",
            min_value=5,
            max_value=50,
            value=20,
            key="news_limit"
        )
    
    with col2:
        refresh = st.button("🔄 Refresh News", use_container_width=True, type="primary")
    
    with col3:
        view_mode = st.selectbox(
            "View as:",
            options=["Cards", "List"],
            key="news_view_mode"
        )
    
    # Fetch news
    if refresh or 'news_data' not in st.session_state:
        with st.spinner("📡 Fetching latest news..."):
            news_data = api.get_market_news(topic="equity mutual funds", limit=limit)
            
            if news_data and news_data.get('success'):
                st.session_state['news_data'] = news_data
                st.success(f"✅ Loaded {news_data.get('total_articles', 0)} articles")
            else:
                st.error("❌ Unable to fetch news. Please check backend is running.")
                return
    
    # Display news
    if 'news_data' in st.session_state:
        news_data = st.session_state['news_data']
        articles = news_data.get('articles', [])
        
        if articles:
            if view_mode == "Cards":
                render_news_cards(articles)
            else:
                render_news_list(articles)
        else:
            st.warning("No news articles found")


def render_topic_search():
    """Render topic search section"""
    
    st.markdown("### 🔍 Search Specific Topics")
    
    # Predefined topics
    st.markdown("#### Quick Topics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📈 Market Outlook", use_container_width=True):
            search_topic("market outlook India")
    
    with col2:
        if st.button("💰 Top Mutual Funds", use_container_width=True):
            search_topic("best mutual funds India")
    
    with col3:
        if st.button("📊 Market Analysis", use_container_width=True):
            search_topic("equity market analysis India")
    
    st.markdown("---")
    
    # Custom search
    st.markdown("#### Custom Search")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        custom_topic = st.text_input(
            "Enter topic:",
            placeholder="e.g., SBI mutual funds, HDFC equity",
            key="custom_news_topic"
        )
    
    with col2:
        st.write("")
        st.write("")
        if st.button("🔍 Search", use_container_width=True, type="primary"):
            if custom_topic:
                search_topic(custom_topic)
    
    # Display search results
    if 'search_news_data' in st.session_state:
        st.markdown("---")
        st.markdown("### 📊 Search Results")
        
        news_data = st.session_state['search_news_data']
        articles = news_data.get('articles', [])
        
        if articles:
            st.success(f"✅ Found {len(articles)} articles")
            render_news_cards(articles)
        else:
            st.warning("No articles found for this topic")


def search_topic(topic: str):
    """Search news by topic"""
    with st.spinner(f"🔍 Searching for: {topic}..."):
        news_data = api.get_market_news(topic=topic, limit=15)
        
        if news_data and news_data.get('success'):
            st.session_state['search_news_data'] = news_data
            st.rerun()
        else:
            st.error("Unable to fetch news")


def render_news_cards(articles: list):
    """Render news as cards"""
    
    for i, article in enumerate(articles):
        with st.container():
            # Article card
            st.markdown(f"### {i+1}. {article.get('title', 'No title')}")
            
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.caption(f"**Source:** {article.get('source', 'Unknown')}")
            
            with col2:
                pub_date = article.get('published_at', '')
                if pub_date:
                    try:
                        date_obj = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                        st.caption(f"**Date:** {date_obj.strftime('%d %b %Y')}")
                    except:
                        st.caption(f"**Date:** {pub_date[:10]}")
            
            with col3:
                if article.get('url'):
                    st.link_button("🔗 Read More", article['url'], use_container_width=True)
            
            # Description
            description = article.get('description', '')
            if description:
                st.write(description[:300] + "..." if len(description) > 300 else description)
            
            # Image (if available)
            image_url = article.get('image_url', '')
            if image_url:
                try:
                    st.image(image_url, use_column_width=True)
                except:
                    pass
            
            st.markdown("---")


def render_news_list(articles: list):
    """Render news as a compact list"""
    
    # Create DataFrame
    df_data = []
    for article in articles:
        pub_date = article.get('published_at', '')
        try:
            date_obj = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
            date_str = date_obj.strftime('%d %b %Y')
        except:
            date_str = pub_date[:10] if pub_date else 'N/A'
        
        df_data.append({
            'Title': article.get('title', 'No title')[:60],
            'Source': article.get('source', 'Unknown')[:20],
            'Date': date_str,
            'Link': article.get('url', '')
        })
    
    df = pd.DataFrame(df_data)
    
    # Display table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Link": st.column_config.LinkColumn("Read More", display_text="🔗 Open")
        }
    )


def render_sources_info():
    """Render information about news sources"""
    
    st.markdown("### ℹ️ News Sources")
    
    with st.spinner("Loading sources..."):
        sources_data = api.get_news_sources()
        
        if sources_data and sources_data.get('success'):
            sources = sources_data.get('sources', [])
            
            st.markdown("#### Active News Sources")
            
            for source in sources:
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**{source.get('name', 'Unknown')}**")
                
                with col2:
                    st.write(f"*{source.get('type', 'Unknown')}*")
                
                with col3:
                    status = source.get('status', 'unknown')
                    if status == 'active':
                        st.success("✅ Active")
                    else:
                        st.warning("⚠️ Inactive")
            
            st.markdown("---")
            
            # Configuration info
            st.markdown("#### 📝 Configuration")
            
            st.info("""
            **How it works:**
            
            1. **NewsAPI** - Fetches news from 80,000+ sources worldwide
               - Requires API key (free tier: 100 requests/day)
               - Get key: https://newsapi.org/
            
            2. **RSS Feeds** - Direct feeds from Indian financial news sites
               - Economic Times Markets
               - MoneyControl
               - LiveMint Markets
            
            3. **LangChain Agent** (Optional)
               - AI-powered news analysis and summarization
               - Requires OpenAI API key
               - Provides intelligent filtering and insights
            
            **To enable all features:**
            - Add `NEWS_API_KEY` to your `.env` file
            - Add `OPENAI_API_KEY` for AI analysis (optional)
            """)
            
            # Check API status
            st.markdown("---")
            st.markdown("#### 🔑 API Key Status")
            
            col1, col2 = st.columns(2)
            
            with col1:
                newsapi_active = any(s.get('name') == 'NewsAPI' and s.get('status') == 'active' for s in sources)
                if newsapi_active:
                    st.success("✅ NewsAPI Key: Active")
                else:
                    st.error("❌ NewsAPI Key: Not configured")
                    st.caption("Add `NEWS_API_KEY` to `.env` file")
            
            with col2:
                st.info("📡 RSS Feeds: Always Active")
                st.caption("No API key required")
        
        else:
            st.error("Unable to fetch sources information")
    
    # Settings section
    st.markdown("---")
    st.markdown("#### ⚙️ Settings")
    
    with st.expander("🔧 Configure News Agent"):
        st.markdown("""
        **Environment Variables Needed:**
        
        Create a `.env` file in your project root:
        
        ```
        # NewsAPI (Required for best results)
        NEWS_API_KEY=your_newsapi_key_here
        
        # OpenAI (Optional - for AI analysis)
        OPENAI_API_KEY=your_openai_key_here
        ```
        
        **Get API Keys:**
        - NewsAPI: https://newsapi.org/register (Free)
        - OpenAI: https://platform.openai.com/api-keys (Paid)
        
        **After adding keys:**
        1. Restart your backend server
        2. Refresh this page
        3. All features will be enabled
        """)


def render_footer():
    """Render footer"""
    
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>📰 Market news powered by NewsAPI & RSS Feeds</p>
        <p>🤖 AI analysis by LangChain & OpenAI</p>
        <p style='font-size: 0.9em;'>⚠️ News is for informational purposes only. Not financial advice.</p>
    </div>
    """, unsafe_allow_html=True)


# Call footer at end of page
if __name__ == "__main__":
    render()
    render_footer()

"""
News Agent - LangChain-powered intelligent news analyzer
Fetches, filters, and summarizes mutual fund market news
"""

import os
from typing import List, Dict
from dotenv import load_dotenv

# ✅ FIXED IMPORTS - Removed problematic imports
from langchain_core.tools import Tool 
from langchain_openai import ChatOpenAI

from .news_fetcher import NewsFetcher

load_dotenv()


class NewsAgent:
    """LangChain-powered news agent for market intelligence"""
    
    def __init__(self):
        self.news_fetcher = NewsFetcher()
        self.llm = self._initialize_llm()
        self.agent = self._create_agent()
    
    def _initialize_llm(self):
        """Initialize OpenAI LLM"""
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            print("⚠️ OPENAI_API_KEY not found. Agent will use simple mode.")
            return None
        
        return ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.3,
            api_key=api_key
        )
    
    def _create_tools(self) -> List[Tool]:
        """Create tools for the agent"""
        
        tools = [
            Tool(
                name="FetchMutualFundNews",
                func=lambda query: self.news_fetcher.fetch_market_news(topic=query, limit=15),
                description="Fetch latest news articles about mutual funds, equity markets, and investments in India. Input should be a topic like 'equity mutual funds' or 'market outlook'."
            ),
            Tool(
                name="FetchGeneralFinanceNews",
                func=lambda query: self.news_fetcher.fetch_rss_feeds(limit=10),
                description="Fetch general financial news from RSS feeds. No input needed."
            )
        ]
        
        return tools
    
    def _create_agent(self):
        """Create LangChain agent"""
        
        if not self.llm:
            return None
        
        # ✅ SIMPLIFIED - Just return LLM for simple text generation
        try:
            print("✅ News Agent ready")
            return self.llm
        except Exception as e:
            print(f"⚠️ Agent setup failed: {e}")
            return None
    
    def get_market_news(
        self,
        topic: str = "equity mutual funds",
        limit: int = 20
    ) -> Dict:
        """
        Get market news (simple mode without LLM)
        
        Args:
            topic: News topic
            limit: Max results
        
        Returns:
            Dictionary with articles and summary
        """
        articles = self.news_fetcher.fetch_market_news(topic=topic, limit=limit)
        
        return {
            'success': True,
            'total_articles': len(articles),
            'articles': articles,
            'topic': topic,
            'mode': 'simple'
        }
    
    def get_analyzed_news(
        self,
        query: str = "What are the latest trends in Indian equity mutual funds?"
    ) -> Dict:
        """
        Get news with AI analysis (requires OpenAI API key)
        
        Args:
            query: User question about markets
        
        Returns:
            Dictionary with articles and AI analysis
        """
        if not self.agent:
            # Fallback to simple mode
            return self.get_market_news()
        
        try:
            # ✅ FIXED - Simple LLM invocation instead of complex agent
            articles = self.news_fetcher.fetch_market_news(limit=15)
            
            # Generate analysis with LLM
            if articles:
                article_titles = "\n".join([f"- {a['title']}" for a in articles[:5]])
                prompt = f"Summarize this financial news in 2-3 sentences:\n{article_titles}"
                
                response = self.agent.invoke(prompt)
                analysis = response.content if hasattr(response, 'content') else str(response)
            else:
                analysis = "No articles found"
            
            return {
                'success': True,
                'analysis': analysis,
                'articles': articles,
                'total_articles': len(articles),
                'mode': 'ai_powered'
            }
        
        except Exception as e:
            print(f"❌ Agent error: {str(e)}")
            # Fallback
            return self.get_market_news()

"""
News Agent - LangChain-powered intelligent news analyzer
Fetches, filters, and summarizes mutual fund market news
"""

import os
from typing import List, Dict
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage
from dotenv import load_dotenv

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
        
        tools = self._create_tools()
        
        # System prompt
        system_message = SystemMessage(content="""
        You are a financial news analyst specializing in Indian mutual funds and equity markets.
        
        Your role is to:
        1. Fetch relevant news articles about mutual funds, equity markets, and investments
        2. Filter out noise and focus on actionable insights
        3. Summarize key market trends
        4. Highlight important events affecting mutual fund investors
        
        Always provide sources and be factual. Focus on news from the last 7 days.
        """)
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            system_message,
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create agent
        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=tools,
            prompt=prompt
        )
        
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=3
        )
    
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
            # Run agent
            result = self.agent.invoke({"input": query})
            
            # Also fetch raw articles
            articles = self.news_fetcher.fetch_market_news(limit=15)
            
            return {
                'success': True,
                'analysis': result.get('output', ''),
                'articles': articles,
                'total_articles': len(articles),
                'mode': 'ai_powered'
            }
        
        except Exception as e:
            print(f"❌ Agent error: {str(e)}")
            # Fallback
            return self.get_market_news()

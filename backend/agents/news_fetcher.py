"""
News Fetcher - Wrapper for multiple news sources
Fetches equity mutual fund news from various APIs
"""

import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import feedparser
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class NewsFetcher:
    """Fetch news from multiple sources"""
    
    def __init__(self):
        self.news_api_key = os.getenv('NEWS_API_KEY')
        self.serpapi_key = os.getenv('SERPAPI_API_KEY')
    
    def fetch_newsapi(
        self,
        query: str = "equity mutual funds India",
        category: str = "business",
        days_ago: int = 7,
        limit: int = 20
    ) -> List[Dict]:
        """
        Fetch news from NewsAPI
        
        Args:
            query: Search query
            category: News category
            days_ago: How many days back to search
            limit: Max results
        
        Returns:
            List of news articles
        """
        if not self.news_api_key:
            print("⚠️ NEWS_API_KEY not found in environment")
            return []
        
        try:
            # Calculate date range
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days_ago)
            
            # NewsAPI endpoint
            url = "https://newsapi.org/v2/everything"
            
            params = {
                'q': query,
                'from': from_date.strftime('%Y-%m-%d'),
                'to': to_date.strftime('%Y-%m-%d'),
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': limit,
                'apiKey': self.news_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') != 'ok':
                print(f"❌ NewsAPI error: {data.get('message')}")
                return []
            
            articles = []
            for article in data.get('articles', []):
                articles.append({
                    'title': article.get('title', 'No title'),
                    'description': article.get('description', ''),
                    'url': article.get('url', ''),
                    'source': article.get('source', {}).get('name', 'Unknown'),
                    'published_at': article.get('publishedAt', ''),
                    'image_url': article.get('urlToImage', ''),
                    'content': article.get('content', '')
                })
            
            print(f"✅ Fetched {len(articles)} articles from NewsAPI")
            return articles
        
        except Exception as e:
            print(f"❌ NewsAPI fetch error: {str(e)}")
            return []
    
    def fetch_rss_feeds(self, limit: int = 10) -> List[Dict]:
        """
        Fetch news from financial RSS feeds
        
        Args:
            limit: Max results per feed
        
        Returns:
            List of news articles
        """
        # Indian financial news RSS feeds
        feeds = [
            'https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms',  # ET Markets
            'https://www.moneycontrol.com/rss/MCtopnews.xml',  # MoneyControl
            'https://www.livemint.com/rss/markets',  # Mint Markets
        ]
        
        articles = []
        
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:limit]:
                    articles.append({
                        'title': entry.get('title', 'No title'),
                        'description': entry.get('summary', ''),
                        'url': entry.get('link', ''),
                        'source': feed.feed.get('title', 'RSS Feed'),
                        'published_at': entry.get('published', ''),
                        'image_url': '',
                        'content': entry.get('description', '')
                    })
            
            except Exception as e:
                print(f"❌ RSS feed error ({feed_url}): {str(e)}")
                continue
        
        print(f"✅ Fetched {len(articles)} articles from RSS feeds")
        return articles
    
    def fetch_market_news(
        self,
        topic: str = "mutual funds",
        limit: int = 20
    ) -> List[Dict]:
        """
        Fetch market news (combines multiple sources)
        
        Args:
            topic: News topic
            limit: Max total results
        
        Returns:
            Combined list of news articles
        """
        all_articles = []
        
        # Fetch from NewsAPI
        if self.news_api_key:
            newsapi_articles = self.fetch_newsapi(
                query=f"{topic} India",
                limit=limit // 2
            )
            all_articles.extend(newsapi_articles)
        
        # Fetch from RSS feeds
        rss_articles = self.fetch_rss_feeds(limit=limit // 2)
        all_articles.extend(rss_articles)
        
        # Remove duplicates based on title
        seen_titles = set()
        unique_articles = []
        
        for article in all_articles:
            if article['title'] not in seen_titles:
                seen_titles.add(article['title'])
                unique_articles.append(article)
        
        # Sort by date (newest first)
        unique_articles.sort(
            key=lambda x: x.get('published_at', ''),
            reverse=True
        )
        
        return unique_articles[:limit]

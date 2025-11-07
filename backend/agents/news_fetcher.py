"""
News Fetcher - Wrapper for multiple news sources
Fetches ONLY equity and hybrid mutual fund news from various APIs
"""

import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import feedparser
from dotenv import load_dotenv

load_dotenv()


class NewsFetcher:
    """Fetch ONLY equity and hybrid mutual fund related news"""
    
    # ✅ Keywords to INCLUDE
    INCLUDE_KEYWORDS = [
        "equity mutual fund",
        "hybrid mutual fund",
        "mutual fund",
        "portfolio strategy",
        "portfolio building",
        "asset allocation",
        "fund manager",
        "AMFI",
        "SEBI",
        "investment strategy",
        "fund performance"
    ]
    
    # ✅ Keywords to EXCLUDE
    EXCLUDE_KEYWORDS = [
        "debt fund",
        "index fund",
        "ETF",
        "cryptocurrency",
        "crypto",
        "forex",
        "commodities",
        "penny stock",
        "IPO",
        "stock tips",
        "trading",
        "bitcoin",
        "crypto"
    ]
    
    def __init__(self):
        self.news_api_key = os.getenv('NEWS_API_KEY')
        self.serpapi_key = os.getenv('SERPAPI_API_KEY')
    
    def _is_relevant_article(self, title: str, description: str = "") -> bool:
        """Check if article is relevant to equity/hybrid mutual funds"""
        
        combined_text = (title + " " + description).lower()
        
        # ✅ MUST include at least one include keyword
        has_include = any(keyword in combined_text for keyword in self.INCLUDE_KEYWORDS)
        
        # ✅ MUST NOT have any exclude keywords
        has_exclude = any(keyword in combined_text for keyword in self.EXCLUDE_KEYWORDS)
        
        return has_include and not has_exclude
    
    def fetch_newsapi(
        self,
        days_ago: int = 7,
        limit: int = 20
    ) -> List[Dict]:
        """
        Fetch ONLY equity/hybrid mutual fund news from NewsAPI
        """
        if not self.news_api_key:
            print("⚠️ NEWS_API_KEY not found in environment")
            return []
        
        try:
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days_ago)
            
            # ✅ FIXED SEARCH QUERIES - Focus on mutual funds only
            queries = [
                "equity mutual funds India",
                "hybrid mutual funds portfolio",
                "mutual fund investment strategy"
            ]
            
            all_articles = []
            
            for query in queries:
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
                    continue
                
                for article in data.get('articles', []):
                    title = article.get('title', 'No title')
                    description = article.get('description', '')
                    
                    # ✅ Filter articles - ONLY relevant ones
                    if not self._is_relevant_article(title, description):
                        continue
                    
                    all_articles.append({
                        'title': title,
                        'description': description,
                        'url': article.get('url', ''),
                        'source': article.get('source', {}).get('name', 'Unknown'),
                        'published_at': article.get('publishedAt', ''),
                        'image_url': article.get('urlToImage', ''),
                        'content': article.get('content', '')
                    })
            
            print(f"✅ Fetched {len(all_articles)} RELEVANT articles from NewsAPI")
            return all_articles
        
        except Exception as e:
            print(f"❌ NewsAPI fetch error: {str(e)}")
            return []
    
    def fetch_rss_feeds(self, limit: int = 10) -> List[Dict]:
        """
        Fetch ONLY equity/hybrid mutual fund news from RSS feeds
        """
        # ✅ Indian financial news RSS feeds (mostly mutual fund related)
        feeds = [
            'https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms',  # ET Markets
            'https://www.moneycontrol.com/rss/mutualfunds',  # MoneyControl Mutual Funds
            'https://www.livemint.com/rss/markets',  # Mint Markets
        ]
        
        articles = []
        
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:limit]:
                    title = entry.get('title', 'No title')
                    description = entry.get('summary', '')
                    
                    # ✅ Filter articles - ONLY relevant ones
                    if not self._is_relevant_article(title, description):
                        continue
                    
                    articles.append({
                        'title': title,
                        'description': description,
                        'url': entry.get('link', ''),
                        'source': feed.feed.get('title', 'RSS Feed'),
                        'published_at': entry.get('published', ''),
                        'image_url': '',
                        'content': description
                    })
            
            except Exception as e:
                print(f"⚠️ RSS feed error ({feed_url}): {str(e)}")
                continue
        
        print(f"✅ Fetched {len(articles)} RELEVANT articles from RSS feeds")
        return articles
    
    def fetch_market_news(
        self,
        topic: str = "equity and hybrid mutual funds",
        limit: int = 20
    ) -> List[Dict]:
        """
        Fetch market news - ONLY equity/hybrid mutual fund related
        """
        all_articles = []
        
        # Fetch from NewsAPI
        if self.news_api_key:
            newsapi_articles = self.fetch_newsapi(limit=limit // 2)
            all_articles.extend(newsapi_articles)
        
        # Fetch from RSS feeds
        rss_articles = self.fetch_rss_feeds(limit=limit // 2)
        all_articles.extend(rss_articles)
        
        # Remove duplicates
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

"""
AUM Data Fetcher
Fetches Assets Under Management data from external sources
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
from pathlib import Path
import json


class AUMDataFetcher:
    """Fetch and cache AUM data"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "aum_data.csv"
        self.cache_duration = timedelta(days=7)  # Refresh weekly
    
    def fetch_aum_data_from_github(self) -> pd.DataFrame:
        """
        Fetch AUM data from GitHub dataset
        Source: https://github.com/InertExpert2911/Mutual_Fund_Data
        """
        try:
            url = "https://raw.githubusercontent.com/InertExpert2911/Mutual_Fund_Data/main/mutual_fund_data.csv"
            print(f"Fetching AUM data from GitHub...")
            
            df = pd.read_csv(url)
            
            # Save to cache
            df.to_csv(self.cache_file, index=False)
            print(f"✅ AUM data cached ({len(df)} records)")
            
            return df
        except Exception as e:
            print(f"❌ Error fetching AUM data: {e}")
            return None
    
    def load_cached_aum_data(self) -> pd.DataFrame:
        """Load AUM data from cache if available and recent"""
        if not self.cache_file.exists():
            return None
        
        # Check cache age
        cache_age = datetime.now() - datetime.fromtimestamp(self.cache_file.stat().st_mtime)
        
        if cache_age > self.cache_duration:
            print(f"Cache expired (age: {cache_age.days} days), fetching fresh data...")
            return None
        
        try:
            df = pd.read_csv(self.cache_file)
            print(f"✅ Loaded AUM data from cache ({len(df)} records)")
            return df
        except Exception as e:
            print(f"❌ Error loading cache: {e}")
            return None
    
    def get_aum_data(self, force_refresh: bool = False) -> pd.DataFrame:
        """
        Get AUM data (cached or fresh)
        
        Args:
            force_refresh: Force refresh from source
        
        Returns:
            DataFrame with AUM data or None
        """
        if not force_refresh:
            cached_data = self.load_cached_aum_data()
            if cached_data is not None:
                return cached_data
        
        # Fetch fresh data
        return self.fetch_aum_data_from_github()
    
    def get_top_amc_by_aum(self, limit: int = 10) -> pd.Series:
        """
        Get top AMCs by actual AUM
        
        Args:
            limit: Number of top AMCs to return
        
        Returns:
            Series with AMC names and total AUM
        """
        df = self.get_aum_data()
        
        if df is None or 'amc' not in df.columns or 'aum' not in df.columns:
            return None
        
        # Clean AUM column (remove non-numeric values)
        df['aum'] = pd.to_numeric(df['aum'], errors='coerce')
        df = df.dropna(subset=['aum'])
        
        # Group by AMC and sum AUM
        amc_aum = df.groupby('amc')['aum'].sum().sort_values(ascending=False)
        
        return amc_aum.head(limit)
    
    def get_total_aum(self) -> float:
        """Get total AUM across all schemes"""
        df = self.get_aum_data()
        
        if df is None or 'aum' not in df.columns:
            return None
        
        df['aum'] = pd.to_numeric(df['aum'], errors='coerce')
        return df['aum'].sum()
    
    def get_aum_for_scheme(self, scheme_code: str) -> float:
        """Get AUM for a specific scheme"""
        df = self.get_aum_data()
        
        if df is None:
            return None
        
        # Try to match by scheme code
        if 'scheme_code' in df.columns:
            scheme_data = df[df['scheme_code'] == scheme_code]
            if not scheme_data.empty:
                return scheme_data.iloc[0]['aum']
        
        return None
    
    def get_category_wise_aum(self) -> pd.Series:
        """Get AUM breakdown by category"""
        df = self.get_aum_data()
        
        if df is None or 'category' not in df.columns or 'aum' not in df.columns:
            return None
        
        df['aum'] = pd.to_numeric(df['aum'], errors='coerce')
        category_aum = df.groupby('category')['aum'].sum().sort_values(ascending=False)
        
        return category_aum


# Global instance
aum_fetcher = AUMDataFetcher()

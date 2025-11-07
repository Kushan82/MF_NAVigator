"""
FIXED AUM Data Fetcher - Real Data Only
NO FABRICATED ESTIMATES - Uses actual data sources
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
from pathlib import Path
import json


class RealAUMDataFetcher:
    """Fetch REAL AUM data from verified sources only"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "real_aum_data.csv"
        self.cache_duration = timedelta(days=7)  # Weekly refresh
        
        # Real data sources
        self.sources = {
            'github': "https://raw.githubusercontent.com/InertExpert2911/Mutual_Fund_Data/main/mutual_fund_data.csv",
            # Add more verified sources here
        }
    
    def fetch_real_aum_from_github(self) -> pd.DataFrame:
        """
        Fetch REAL AUM data from verified GitHub source
        Returns None if unavailable - NO FABRICATION
        """
        try:
            print(f"📥 Fetching REAL AUM data from GitHub...")
            
            df = pd.read_csv(self.sources['github'])
            
            # Validate data structure
            required_cols = ['amc', 'aum']
            if not all(col in df.columns for col in required_cols):
                print(f"❌ Invalid data structure. Missing columns: {required_cols}")
                return None
            
            # Clean AUM column - convert to numeric
            df['aum'] = pd.to_numeric(df['aum'], errors='coerce')
            
            # Remove rows with invalid AUM
            initial_count = len(df)
            df = df.dropna(subset=['aum'])
            df = df[df['aum'] > 0]
            
            removed = initial_count - len(df)
            if removed > 0:
                print(f"⚠️  Removed {removed} rows with invalid AUM values")
            
            # Validate AUM ranges (sanity check)
            if df['aum'].max() > 1000000:  # > 10 lakh crores (unrealistic)
                print(f"⚠️  Warning: Suspiciously high AUM values detected")
            
            # Save to cache
            df.to_csv(self.cache_file, index=False)
            print(f"✅ Fetched {len(df):,} schemes with REAL AUM data")
            
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error fetching AUM data: {e}")
            return None
        except Exception as e:
            print(f"❌ Error fetching AUM data: {e}")
            return None
    
    def load_cached_aum_data(self) -> pd.DataFrame:
        """Load AUM data from cache if recent"""
        if not self.cache_file.exists():
            return None
        
        # Check cache age
        cache_age = datetime.now() - datetime.fromtimestamp(
            self.cache_file.stat().st_mtime
        )
        
        if cache_age > self.cache_duration:
            print(f"⏰ Cache expired ({cache_age.days} days old)")
            return None
        
        try:
            df = pd.read_csv(self.cache_file)
            print(f"📂 Loaded AUM data from cache ({len(df):,} schemes)")
            return df
        except Exception as e:
            print(f"❌ Error loading cache: {e}")
            return None
    
    def get_aum_data(self, force_refresh: bool = False) -> pd.DataFrame:
        """
        Get REAL AUM data (cached or fresh)
        Returns None if no real data available - NO FABRICATION
        """
        if not force_refresh:
            cached_data = self.load_cached_aum_data()
            if cached_data is not None:
                return cached_data
        
        # Fetch fresh data
        return self.fetch_real_aum_from_github()
    
    def get_top_amc_by_real_aum(self, limit: int = 10) -> pd.Series:
        """
        Get top AMCs by ACTUAL AUM (not estimates)
        Returns None if real data unavailable
        """
        df = self.get_aum_data()
        
        if df is None:
            print("❌ No real AUM data available")
            return None
        
        # Clean data
        df['aum'] = pd.to_numeric(df['aum'], errors='coerce')
        df = df.dropna(subset=['aum', 'amc'])
        
        # Group by AMC and sum AUM
        amc_aum = df.groupby('amc')['aum'].sum().sort_values(ascending=False)
        
        return amc_aum.head(limit)
    
    def get_total_industry_aum(self) -> float:
        """
        Get total industry AUM (real data only)
        Returns None if unavailable
        """
        df = self.get_aum_data()
        
        if df is None:
            return None
        
        df['aum'] = pd.to_numeric(df['aum'], errors='coerce')
        total_aum = df['aum'].sum()
        
        return total_aum if total_aum > 0 else None
    
    def get_aum_for_scheme(self, scheme_code: str) -> float:
        """
        Get AUM for specific scheme (real data only)
        Returns None if unavailable
        """
        df = self.get_aum_data()
        
        if df is None:
            return None
        
        # Try to match by scheme code
        if 'scheme_code' in df.columns:
            scheme_data = df[df['scheme_code'].astype(str) == str(scheme_code)]
            if not scheme_data.empty:
                return float(scheme_data.iloc[0]['aum'])
        
        return None
    
    def get_category_wise_aum(self) -> pd.Series:
        """
        Get AUM breakdown by category (real data only)
        Returns None if unavailable
        """
        df = self.get_aum_data()
        
        if df is None or 'category' not in df.columns:
            return None
        
        df['aum'] = pd.to_numeric(df['aum'], errors='coerce')
        category_aum = df.groupby('category')['aum'].sum().sort_values(
            ascending=False
        )
        
        return category_aum
    
    def validate_aum_data(self, df: pd.DataFrame) -> dict:
        """
        Validate AUM data quality
        Returns validation report
        """
        report = {
            'total_schemes': len(df),
            'schemes_with_aum': df['aum'].notna().sum(),
            'coverage_pct': (df['aum'].notna().sum() / len(df) * 100),
            'aum_range': {
                'min': float(df['aum'].min()),
                'max': float(df['aum'].max()),
                'mean': float(df['aum'].mean()),
                'median': float(df['aum'].median())
            },
            'total_aum_crores': float(df['aum'].sum()),
            'issues': []
        }
        
        # Detect issues
        if report['coverage_pct'] < 50:
            report['issues'].append(
                f"Low coverage: Only {report['coverage_pct']:.1f}% schemes have AUM data"
            )
        
        if report['aum_range']['max'] > 1000000:
            report['issues'].append(
                "Suspiciously high AUM values detected (>10 lakh crores)"
            )
        
        if report['aum_range']['min'] < 0:
            report['issues'].append("Negative AUM values detected")
        
        return report


# Backward compatibility
aum_fetcher = RealAUMDataFetcher()
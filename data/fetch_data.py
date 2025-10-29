import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

import sys
sys.path.append(str(Path(__file__).parent.parent))
from backend.config import settings


class MutualFundDataFetcher:
    """Fetch mutual fund data from various sources"""
    
    def __init__(self):
        self.cache_dir = settings.DATA_DIR
        self.cache_enabled = settings.CACHE_ENABLED
        
    def fetch_amfi_daily_nav(self, save_to_cache: bool = True) -> pd.DataFrame:
        """
        Fetch latest NAV data from AMFI
        Returns DataFrame with columns: Scheme_Code, Scheme_Name, NAV, Date
        """
        print("📥 Fetching latest NAV data from AMFI...")
        
        try:
            response = requests.get(settings.AMFI_NAV_URL, timeout=30)
            response.raise_for_status()
            
            # Parse the text file
            lines = response.text.strip().split('\n')
            
            data = []
            current_amc = None
            
            for line in lines:
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                
                # AMC name lines (don't have semicolons)
                if ';' not in line:
                    current_amc = line
                    continue
                
                # Skip header lines
                if 'Scheme Code' in line:
                    continue
                
                # Parse scheme data
                parts = line.split(';')
                if len(parts) >= 6:
                    try:
                        scheme_code = parts[0].strip()
                        isin_div = parts[1].strip()
                        isin_growth = parts[2].strip()
                        scheme_name = parts[3].strip()
                        nav = parts[4].strip()
                        date = parts[5].strip()
                        
                        # Skip if NAV is N.A. or empty
                        if nav and nav != 'N.A.':
                            data.append({
                                'Scheme_Code': scheme_code,
                                'ISIN_Div': isin_div,
                                'ISIN_Growth': isin_growth,
                                'Scheme_Name': scheme_name,
                                'NAV': float(nav),
                                'Date': pd.to_datetime(date, format='%d-%b-%Y'),
                                'AMC': current_amc
                            })
                    except (ValueError, IndexError):
                        continue
            
            df = pd.DataFrame(data)
            
            print(f"✅ Fetched {len(df):,} mutual fund schemes")
            print(f"📊 Latest NAV date: {df['Date'].max().strftime('%d-%b-%Y')}")
            
            if save_to_cache and self.cache_enabled:
                cache_file = self.cache_dir / f"amfi_nav_{datetime.now().strftime('%Y%m%d')}.csv"
                df.to_csv(cache_file, index=False)
                print(f"💾 Saved to cache: {cache_file.name}")
            
            return df
            
        except Exception as e:
            print(f"❌ Error fetching AMFI data: {e}")
            raise
    
    def fetch_scheme_details_mfapi(self, scheme_code: str) -> Optional[Dict]:
        """
        Fetch scheme details from MFapi.in
        """
        try:
            url = f"{settings.MFAPI_BASE_URL}/mf/{scheme_code}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"⚠️  Error fetching scheme {scheme_code}: {e}")
            return None
    
    def fetch_historical_nav_mfapi(self, scheme_code: str) -> Optional[pd.DataFrame]:
        """
        Fetch historical NAV data from MFapi.in
        Returns DataFrame with Date and NAV columns
        """
        print(f"📥 Fetching historical data for scheme: {scheme_code}")
        
        try:
            data = self.fetch_scheme_details_mfapi(scheme_code)
            
            if not data or 'data' not in data:
                return None
            
            # Parse historical data
            nav_data = []
            for record in data['data']:
                try:
                    nav_data.append({
                        'Date': pd.to_datetime(record['date'], format='%d-%m-%Y'),
                        'NAV': float(record['nav'])
                    })
                except (ValueError, KeyError):
                    continue
            
            df = pd.DataFrame(nav_data)
            df = df.sort_values('Date').reset_index(drop=True)
            
            print(f"✅ Fetched {len(df):,} historical records")
            
            return df
            
        except Exception as e:
            print(f"❌ Error fetching historical data: {e}")
            return None
    
    def search_schemes(self, query: str, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Search schemes by name or code
        """
        if df is None:
            df = self.fetch_amfi_daily_nav(save_to_cache=False)
        
        query = query.lower()
        mask = (
            df['Scheme_Name'].str.lower().str.contains(query) |
            df['Scheme_Code'].astype(str).str.contains(query) |
            df['AMC'].str.lower().str.contains(query)
        )
        
        results = df[mask]
        print(f"🔍 Found {len(results)} schemes matching '{query}'")
        
        return results
    
    def get_scheme_categories(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Extract scheme categories from scheme names
        """
        if df is None:
            df = self.fetch_amfi_daily_nav(save_to_cache=False)
        
        # Simple category extraction from scheme names
        def extract_category(name):
            name_lower = name.lower()
            if 'equity' in name_lower or 'stock' in name_lower:
                return 'Equity'
            elif 'debt' in name_lower or 'bond' in name_lower or 'income' in name_lower:
                return 'Debt'
            elif 'hybrid' in name_lower or 'balanced' in name_lower:
                return 'Hybrid'
            elif 'liquid' in name_lower:
                return 'Liquid'
            elif 'gilt' in name_lower:
                return 'Gilt'
            elif 'index' in name_lower or 'etf' in name_lower:
                return 'Index'
            else:
                return 'Other'
        
        df['Category'] = df['Scheme_Name'].apply(extract_category)
        return df
    
    def load_cached_data(self, date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        Load cached AMFI data
        date format: YYYYMMDD
        """
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        cache_file = self.cache_dir / f"amfi_nav_{date}.csv"
        
        if cache_file.exists():
            print(f"📂 Loading cached data: {cache_file.name}")
            return pd.read_csv(cache_file, parse_dates=['Date'])
        else:
            print(f"⚠️  No cached data found for {date}")
            return None
    
    def get_scheme_info(self, scheme_code: str) -> Dict:
        """
        Get comprehensive scheme information
        """
        print(f"ℹ️  Fetching info for scheme: {scheme_code}")
        
        # Get from MFapi
        mfapi_data = self.fetch_scheme_details_mfapi(scheme_code)
        
        if mfapi_data and 'meta' in mfapi_data:
            meta = mfapi_data['meta']
            return {
                'scheme_code': meta.get('scheme_code'),
                'scheme_name': meta.get('scheme_name'),
                'fund_house': meta.get('fund_house'),
                'scheme_type': meta.get('scheme_type'),
                'scheme_category': meta.get('scheme_category'),
                'scheme_nav': meta.get('scheme_nav'),
                'nav_date': meta.get('nav_date')
            }
        
        return {}


# Convenience functions
def fetch_latest_nav() -> pd.DataFrame:
    """Quick function to fetch latest NAV data"""
    fetcher = MutualFundDataFetcher()
    return fetcher.fetch_amfi_daily_nav()


def fetch_scheme_history(scheme_code: str) -> pd.DataFrame:
    """Quick function to fetch scheme historical data"""
    fetcher = MutualFundDataFetcher()
    return fetcher.fetch_historical_nav_mfapi(scheme_code)


def search_mutual_funds(query: str) -> pd.DataFrame:
    """Quick function to search mutual funds"""
    fetcher = MutualFundDataFetcher()
    return fetcher.search_schemes(query)


if __name__ == "__main__":
    # Test the data fetcher
    print("\n" + "="*70)
    print("🧪 Testing MF_NAVigator Data Fetcher")
    print("="*70 + "\n")
    
    fetcher = MutualFundDataFetcher()
    
    # Test: Fetch latest NAV
    print("📌 Test: Fetching latest NAV data...")
    df = fetcher.fetch_amfi_daily_nav()
    print(f"\nSample data:")
    print(df.head())
    
    print("\n" + "="*70)
    print("✅ Data fetcher working successfully!")
    print("="*70)

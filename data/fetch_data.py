"""
IMPROVED Data Fetcher with Real-time Updates and Better Categorization
Fixes: 
- Accurate scheme categorization
- Better AMFI data parsing
- Data validation and anomaly detection
- Real-time data refresh
"""

import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict
import re

import sys
sys.path.append(str(Path(__file__).parent.parent))
from backend.config import settings


class ImprovedMutualFundDataFetcher:
    """Enhanced mutual fund data fetcher with accurate categorization"""
    
    def __init__(self):
        self.cache_dir = settings.DATA_DIR
        self.cache_enabled = settings.CACHE_ENABLED
        self.cache_ttl = 3600  # 1 hour cache
        
        # Comprehensive category keywords for accurate classification
        self.category_patterns = {
            'Equity': [
                'equity', 'stock', 'large cap', 'mid cap', 'small cap', 
                'multi cap', 'flexi cap', 'focused', 'sectoral', 'thematic',
                'dividend yield', 'value', 'contra', 'elss', 'tax saver'
            ],
            'Debt': [
                'debt', 'bond', 'income', 'gilt', 'corporate bond',
                'banking and psu', 'credit risk', 'dynamic bond', 
                'floater', 'medium duration', 'short duration',
                'low duration', 'ultra short', 'liquid', 'overnight',
                'money market', 'treasury'
            ],
            'Hybrid': [
                'hybrid', 'balanced', 'conservative', 'aggressive',
                'dynamic asset', 'multi asset', 'arbitrage',
                'equity savings', 'balanced advantage'
            ],
            'Solution': [
                'retirement', 'children', 'child', "children's"
            ],
            'Index': [
                'index', 'nifty', 'sensex', 'etf', 'exchange traded'
            ],
            'FoF': [
                'fund of funds', 'fof', 'gold etf', 'international'
            ]
        }
    
    def fetch_amfi_daily_nav(self, save_to_cache: bool = True, force_refresh: bool = False) -> pd.DataFrame:
        """
        Fetch latest NAV data from AMFI with improved parsing
        
        Args:
            save_to_cache: Whether to save to cache
            force_refresh: Force fetch even if cache is valid
        
        Returns:
            DataFrame with accurate scheme information
        """
        
        # Check cache first (unless force refresh)
        if not force_refresh and self.cache_enabled:
            cached_data = self._load_from_cache()
            if cached_data is not None:
                print("📂 Using cached data (use force_refresh=True to update)")
                return cached_data
        
        print("📥 Fetching latest NAV data from AMFI...")
        
        try:
            response = requests.get(settings.AMFI_NAV_URL, timeout=30)
            response.raise_for_status()
            
            # Parse the text file with improved logic
            lines = response.text.strip().split('\n')
            
            data = []
            current_amc = None
            schemes_parsed = 0
            
            for line in lines:
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                
                # AMC name lines (don't have semicolons)
                if ';' not in line:
                    # Clean AMC name
                    current_amc = self._clean_amc_name(line)
                    continue
                
                # Skip header lines
                if 'Scheme Code' in line or 'Scheme Name' in line:
                    continue
                
                # Parse scheme data
                parts = line.split(';')
                
                # AMFI format: Code;ISIN Div;ISIN Growth;Name;NAV;Date
                if len(parts) >= 6:
                    try:
                        scheme_code = parts[0].strip()
                        isin_div = parts[1].strip()
                        isin_growth = parts[2].strip()
                        scheme_name = parts[3].strip()
                        nav_str = parts[4].strip()
                        date_str = parts[5].strip()
                        
                        # Skip if essential data is missing
                        if not scheme_code or not scheme_name:
                            continue
                        
                        # Skip if NAV is N.A. or empty
                        if not nav_str or nav_str.upper() == 'N.A.':
                            continue
                        
                        # Convert NAV to float
                        try:
                            nav = float(nav_str)
                        except ValueError:
                            continue
                        
                        # Skip unrealistic NAV values
                        if nav <= 0 or nav > 100000:
                            continue
                        
                        # Parse date
                        try:
                            date = pd.to_datetime(date_str, format='%d-%b-%Y')
                        except:
                            continue
                        
                        # Skip if no AMC assigned
                        if not current_amc:
                            continue
                        
                        data.append({
                            'Scheme_Code': scheme_code,
                            'ISIN_Div': isin_div if isin_div else None,
                            'ISIN_Growth': isin_growth if isin_growth else None,
                            'Scheme_Name': scheme_name,
                            'NAV': nav,
                            'Date': date,
                            'AMC': current_amc
                        })
                        
                        schemes_parsed += 1
                        
                    except (ValueError, IndexError) as e:
                        # Skip malformed lines
                        continue
            
            # Create DataFrame
            df = pd.DataFrame(data)
            
            if len(df) == 0:
                print("❌ No valid schemes found in AMFI data")
                return pd.DataFrame()
            
            # Data validation
            df = self._validate_data(df)
            
            # Add accurate categories
            df = self.get_accurate_scheme_categories(df)
            
            print(f"✅ Fetched {len(df):,} mutual fund schemes")
            print(f"📊 Latest NAV date: {df['Date'].max().strftime('%d-%b-%Y')}")
            print(f"🏢 Total AMCs: {df['AMC'].nunique()}")
            
            # Save to cache
            if save_to_cache and self.cache_enabled:
                self._save_to_cache(df)
            
            return df
            
        except Exception as e:
            print(f"❌ Error fetching AMFI data: {e}")
            # Try to return cached data as fallback
            cached_data = self._load_from_cache(ignore_ttl=True)
            if cached_data is not None:
                print("⚠️  Using stale cached data as fallback")
                return cached_data
            raise
    
    def _clean_amc_name(self, raw_amc: str) -> str:
        """Clean and standardize AMC names"""
        
        # Remove common suffixes
        amc = raw_amc.strip()
        amc = re.sub(r'\s+Mutual Fund.*$', '', amc, flags=re.IGNORECASE)
        amc = re.sub(r'\s+Asset Management.*$', '', amc, flags=re.IGNORECASE)
        amc = re.sub(r'\s+AMC.*$', '', amc, flags=re.IGNORECASE)
        
        # Standardize common names
        name_mappings = {
            'ICICI Prudential': 'ICICI Prudential',
            'Aditya Birla Sun Life': 'Aditya Birla Sun Life',
            'SBI': 'SBI',
            'HDFC': 'HDFC',
            'Kotak Mahindra': 'Kotak',
            'Axis': 'Axis',
            'UTI': 'UTI',
            'DSP': 'DSP',
            'Franklin Templeton': 'Franklin Templeton',
            'Nippon India': 'Nippon India',
            'Tata': 'Tata',
            'Mirae Asset': 'Mirae Asset',
            'HSBC': 'HSBC',
            'L&T': 'L&T',
            'Invesco': 'Invesco'
        }
        
        # Try to match with known AMCs
        for key, value in name_mappings.items():
            if key.lower() in amc.lower():
                return value
        
        return amc.strip()
    
    def _validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean data"""
        
        initial_count = len(df)
        
        # Remove duplicates (keep most recent)
        df = df.sort_values('Date', ascending=False)
        df = df.drop_duplicates(subset=['Scheme_Code'], keep='first')
        
        # Remove schemes with invalid data
        df = df[df['NAV'] > 0]
        df = df[df['NAV'] < 100000]  # Sanity check
        
        # Remove schemes with suspicious AMC names
        df = df[df['AMC'].str.len() > 2]
        df = df[~df['AMC'].str.contains('Scheme', case=False, na=False)]
        
        removed = initial_count - len(df)
        if removed > 0:
            print(f"🧹 Cleaned data: Removed {removed:,} invalid/duplicate records")
        
        return df
    
    def get_accurate_scheme_categories(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Accurately categorize schemes using comprehensive pattern matching
        """
        
        print("🏷️  Categorizing schemes...")
        
        def categorize_scheme(name: str) -> str:
            """Categorize a single scheme"""
            name_lower = name.lower()
            
            # Check each category's patterns
            category_scores = {}
            
            for category, patterns in self.category_patterns.items():
                score = 0
                for pattern in patterns:
                    if pattern in name_lower:
                        # Weight by pattern specificity
                        score += len(pattern)
                category_scores[category] = score
            
            # Return category with highest score
            if max(category_scores.values()) > 0:
                return max(category_scores, key=category_scores.get)
            
            # Default fallback based on common patterns
            if any(word in name_lower for word in ['growth', 'bluechip', 'large', 'mid', 'small']):
                return 'Equity'
            elif any(word in name_lower for word in ['fund', 'plan']):
                return 'Other'
            else:
                return 'Other'
        
        # Apply categorization
        df['Category'] = df['Scheme_Name'].apply(categorize_scheme)
        
        # Print category distribution
        category_counts = df['Category'].value_counts()
        print("\n📊 Category Distribution:")
        for cat, count in category_counts.items():
            pct = (count / len(df) * 100)
            print(f"   {cat}: {count:,} ({pct:.1f}%)")
        
        return df
    
    def _load_from_cache(self, ignore_ttl: bool = False) -> Optional[pd.DataFrame]:
        """Load data from cache if available and fresh"""
        
        cache_file = self.cache_dir / f"amfi_nav_latest.csv"
        
        if not cache_file.exists():
            return None
        
        # Check cache age
        if not ignore_ttl:
            cache_age = datetime.now().timestamp() - cache_file.stat().st_mtime
            if cache_age > self.cache_ttl:
                print(f"⏰ Cache expired ({cache_age/3600:.1f} hours old)")
                return None
        
        try:
            df = pd.read_csv(cache_file, parse_dates=['Date'])
            cache_age = datetime.now().timestamp() - cache_file.stat().st_mtime
            print(f"📂 Loaded from cache ({cache_age/60:.0f} minutes old)")
            return df
        except Exception as e:
            print(f"⚠️  Error loading cache: {e}")
            return None
    
    def _save_to_cache(self, df: pd.DataFrame):
        """Save data to cache"""
        
        try:
            cache_file = self.cache_dir / f"amfi_nav_latest.csv"
            df.to_csv(cache_file, index=False)
            print(f"💾 Saved to cache: {cache_file.name}")
        except Exception as e:
            print(f"⚠️  Error saving cache: {e}")
    
    # Keep existing methods for backward compatibility
    def fetch_scheme_details_mfapi(self, scheme_code: str) -> Optional[Dict]:
        """Fetch scheme details from MFapi.in"""
        try:
            url = f"{settings.MFAPI_BASE_URL}/mf/{scheme_code}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"⚠️  Error fetching scheme {scheme_code}: {e}")
            return None
    
    def fetch_historical_nav_mfapi(self, scheme_code: str) -> Optional[pd.DataFrame]:
        """Fetch historical NAV data from MFapi.in"""
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
        """Search schemes by name or code"""
        
        if df is None:
            df = self.fetch_amfi_daily_nav(save_to_cache=False)
        
        query = query.lower()
        mask = (
            df['Scheme_Name'].str.lower().str.contains(query, na=False) |
            df['Scheme_Code'].astype(str).str.contains(query, na=False) |
            df['AMC'].str.lower().str.contains(query, na=False)
        )
        
        results = df[mask]
        print(f"🔍 Found {len(results)} schemes matching '{query}'")
        
        return results
    
    def get_scheme_info(self, scheme_code: str) -> Dict:
        """Get comprehensive scheme information"""
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


# Replace the old class for backward compatibility
MutualFundDataFetcher = ImprovedMutualFundDataFetcher


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧪 Testing Improved Data Fetcher")
    print("="*70 + "\n")
    
    fetcher = ImprovedMutualFundDataFetcher()
    
    # Test: Fetch latest NAV with force refresh
    print("📌 Test: Fetching latest NAV data (force refresh)...")
    df = fetcher.fetch_amfi_daily_nav(force_refresh=True)
    
    print(f"\n📊 Sample Data:")
    print(df.head(10).to_string(index=False))
    
    print(f"\n🏢 Top 10 AMCs by scheme count:")
    print(df['AMC'].value_counts().head(10))
    
    print(f"\n📊 Category Breakdown:")
    print(df['Category'].value_counts())
    
    print("\n" + "="*70)
    print("✅ Improved data fetcher working successfully!")
    print("="*70)
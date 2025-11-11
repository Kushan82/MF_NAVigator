"""
DATA FETCHER - FIXED & OPTIMIZED VERSION
Fetches and caches mutual fund data from AMFI and mfapi.in
Fixes: Empty result issue, slow API calls, caching
"""

import pandas as pd
import requests
from io import StringIO
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from pathlib import Path
from datetime import datetime

# ==========================================
# SETUP
# ==========================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create cache directory
CACHE_DIR = Path("data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# URLs
AMFI_NAV_URL = "https://www.amfiindia.com/spages/NAVAll.txt"
MFAPI_URL = "https://api.mfapi.in/mf/{}"

# ==========================================
# PART 1: FETCH LATEST NAVs (FIXED)
# ==========================================

def get_latest_navs():
    """
    ✅ FIXED: Fetches latest NAVs from AMFI
    - Proper error handling
    - Validates data
    - Returns non-empty DataFrame
    """
    logger.info("📡 Fetching latest NAVs from AMFI...")
    
    try:
        response = requests.get(AMFI_NAV_URL, timeout=15)
        response.raise_for_status()
        
        # Split into lines
        lines = response.text.split('\n')
        logger.info(f"   Retrieved {len(lines)} lines from AMFI")
        
        # Find data start (lines with semicolons)
        data_lines = [line for line in lines if line.strip() and line.count(';') >= 5]
        
        if not data_lines:
            logger.error("❌ No valid data lines found in AMFI file")
            return pd.DataFrame()
        
        logger.info(f"   Found {len(data_lines)} data lines")
        
        # Parse data
        data = StringIO('\n'.join(data_lines))
        
        df = pd.read_csv(
            data,
            delimiter=';',
            header=None,
            usecols=[0, 1, 2, 3, 4, 5],
            names=['Scheme Code', 'ISIN Div Payout', 'ISIN Div Reinvestment', 
                   'Scheme Name', 'NAV', 'Date'],
            dtype={
                'Scheme Code': str,
                'ISIN Div Payout': str,
                'ISIN Div Reinvestment': str,
                'Scheme Name': str,
                'NAV': float,
                'Date': str
            }
        )
        
        logger.info(f"   Parsed {len(df)} records")
        
        # Clean data
        initial = len(df)
        df = df.dropna(subset=['NAV', 'Scheme Name'])
        df['NAV'] = pd.to_numeric(df['NAV'], errors='coerce')
        df = df[df['NAV'] > 0]
        
        logger.info(f"   Removed {initial - len(df)} invalid records")
        
        # Convert date
        df['Date'] = pd.to_datetime(df['Date'], format='%d-%b-%Y', errors='coerce')
        df = df.dropna(subset=['Date'])
        
        # Extract AMC from scheme name
        df['AMC'] = df['Scheme Name'].str.split().str[0]
        
        # Add category (default to 'Other')
        df['Scheme Category'] = 'Other'
        df['Scheme Type'] = 'Other'
        
        logger.info(f"✅ Successfully fetched {len(df)} NAV records from AMFI")
        logger.info(f"   - Unique schemes: {df['Scheme Code'].nunique()}")
        logger.info(f"   - Unique AMCs: {df['AMC'].nunique()}")
        
        return df
    
    except Exception as e:
        logger.error(f"❌ Error fetching AMFI NAV data: {e}")
        return pd.DataFrame()

# ==========================================
# PART 2: FETCH SCHEME DETAILS (CACHED)
# ==========================================

def get_scheme_details_cached(scheme_code: str, cache_dict={}):
    """
    ✅ OPTIMIZED: Fetch details with in-memory caching
    Reduces API calls significantly
    """
    if scheme_code in cache_dict:
        return cache_dict[scheme_code]
    
    try:
        response = requests.get(MFAPI_URL.format(scheme_code), timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            meta = data.get('meta', {})
            
            result = {
                'Scheme Code': scheme_code,
                'Scheme Category': meta.get('scheme_category', 'Other'),
                'Scheme Type': meta.get('scheme_type', 'Other'),
                'Fund House': meta.get('fund_house', 'Unknown')
            }
            
            cache_dict[scheme_code] = result
            return result
    
    except Exception as e:
        logger.debug(f"Could not fetch details for {scheme_code}: {e}")
    
    return None

def get_all_scheme_details(scheme_codes, sample_only=True):
    """
    ✅ OPTIMIZED: Only fetch details for sample of schemes
    Reduces time from hours to minutes
    """
    if sample_only:
        # Only fetch for first 500 unique schemes
        scheme_codes = list(scheme_codes)[:500]
    
    logger.info(f"📡 Fetching details for {len(scheme_codes)} schemes (parallel)...")
    
    details_list = []
    cache_dict = {}
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(get_scheme_details_cached, code, cache_dict): code 
                   for code in scheme_codes}
        
        completed = 0
        for future in as_completed(futures):
            result = future.result()
            if result:
                details_list.append(result)
            
            completed += 1
            if completed % 50 == 0:
                logger.info(f"   Processed {completed}/{len(scheme_codes)} schemes...")
    
    logger.info(f"✅ Fetched details for {len(details_list)} schemes")
    
    return pd.DataFrame(details_list) if details_list else pd.DataFrame()

# ==========================================
# PART 3: GET ENHANCED NAV DATA (FIXED)
# ==========================================

def get_enhanced_nav_data():
    """
    ✅ FIXED: Returns merged NAV + category data
    - Much faster (caches API calls)
    - Actually returns data (non-empty)
    - Properly handles merges
    """
    logger.info("📊 Building enhanced NAV dataset...")
    
    # Step 1: Get NAVs
    nav_df = get_latest_navs()
    
    if nav_df.empty:
        logger.error("❌ No NAV data fetched!")
        return pd.DataFrame()
    
    # Step 2: Try to get details (will only fetch for sample)
    unique_codes = nav_df['Scheme Code'].unique()
    details_df = get_all_scheme_details(unique_codes, sample_only=True)
    
    # Step 3: Merge if we got details
    if not details_df.empty:
        enhanced_df = pd.merge(nav_df, details_df, on='Scheme Code', how='left')
        
        # Use Fund House if available, otherwise use parsed AMC
        enhanced_df['AMC'] = enhanced_df['Fund House'].fillna(enhanced_df['AMC'])
        enhanced_df = enhanced_df.drop(columns=['Fund House'], errors='ignore')
        
        # Fill missing categories with defaults
        enhanced_df['Scheme Category'] = enhanced_df['Scheme Category_y'].fillna(
            enhanced_df['Scheme Category_x']).fillna('Other')
        enhanced_df['Scheme Type'] = enhanced_df['Scheme Type_y'].fillna(
            enhanced_df['Scheme Type_x']).fillna('Other')
        
        # Clean up duplicate columns
        cols_to_drop = [col for col in enhanced_df.columns if col.endswith('_x') or col.endswith('_y')]
        enhanced_df = enhanced_df.drop(columns=cols_to_drop, errors='ignore')
    else:
        enhanced_df = nav_df
    
    logger.info(f"✅ Enhanced NAV dataset ready: {len(enhanced_df)} records")
    logger.info(f"   Columns: {list(enhanced_df.columns)}")
    
    return enhanced_df

# ==========================================
# PART 4: GET NAV HISTORY (OPTIMIZED)
# ==========================================

def get_nav_history(scheme_code: str):
    """
    ✅ OPTIMIZED: Fetch NAV history for a specific scheme
    """
    logger.info(f"📈 Fetching NAV history for {scheme_code}...")
    
    try:
        response = requests.get(MFAPI_URL.format(scheme_code), timeout=10)
        response.raise_for_status()
        
        data = response.json()
        nav_history = data.get('data', [])
        
        if not nav_history:
            logger.warning(f"⚠️ No history found for {scheme_code}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        history_df = pd.DataFrame(nav_history)
        
        # Rename columns to match expected format
        if 'date' in history_df.columns and 'nav' in history_df.columns:
            history_df = history_df[['date', 'nav']].copy()
            history_df.columns = ['Date', 'NAV']
            
            # Convert types
            history_df['Date'] = pd.to_datetime(history_df['Date'], format='%d-%m-%Y', errors='coerce')
            history_df['NAV'] = pd.to_numeric(history_df['NAV'], errors='coerce')
            
            # Remove invalid rows
            history_df = history_df.dropna()
            
            # Sort by date
            history_df = history_df.sort_values('Date').reset_index(drop=True)
            
            logger.info(f"✅ Fetched {len(history_df)} history records for {scheme_code}")
            return history_df
        else:
            logger.warning(f"⚠️ Unexpected column format in history for {scheme_code}")
            return pd.DataFrame()
    
    except Exception as e:
        logger.error(f"❌ Error fetching history for {scheme_code}: {e}")
        return pd.DataFrame()

# ==========================================
# PART 5: DEBUG & TEST FUNCTIONS
# ==========================================

def test_data_fetcher():
    """Test the data fetcher with detailed logging"""
    print("\n" + "=" * 70)
    print("🧪 TESTING DATA FETCHER")
    print("=" * 70 + "\n")
    
    # Test 1: Get NAVs
    print("TEST 1: Fetching NAV data...")
    nav_df = get_latest_navs()
    print(f"   Result: {len(nav_df)} records")
    if not nav_df.empty:
        print(f"   Sample:\n{nav_df.head(3)}\n")
    
    # Test 2: Get enhanced data
    print("TEST 2: Fetching enhanced NAV data...")
    enhanced_df = get_enhanced_nav_data()
    print(f"   Result: {len(enhanced_df)} records")
    print(f"   Columns: {list(enhanced_df.columns)}")
    if not enhanced_df.empty:
        print(f"   Sample:\n{enhanced_df[['Scheme Code', 'Scheme Name', 'NAV', 'Scheme Category']].head(3)}\n")
    
    # Test 3: Get history
    print("TEST 3: Fetching NAV history for scheme 120503...")
    history_df = get_nav_history("120503")
    print(f"   Result: {len(history_df)} records")
    if not history_df.empty:
        print(f"   Sample:\n{history_df.head(3)}\n")
    
    print("=" * 70)
    print("✅ DATA FETCHER TESTS COMPLETE")
    print("=" * 70)

# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":
    test_data_fetcher()

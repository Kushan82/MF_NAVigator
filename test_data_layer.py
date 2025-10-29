"""
Test script for MF_NAVigator data layer
Run this to verify data fetching and preprocessing works
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from data.fetch_data import MutualFundDataFetcher
from data.preprocess import DataPreprocessor

def main():
    print("\n" + "="*70)
    print("🚀 MF_NAVigator Data Layer Test")
    print("="*70)
    
    # Initialize
    fetcher = MutualFundDataFetcher()
    preprocessor = DataPreprocessor()
    
    # Test 1: Fetch latest NAV data
    print("\n📋 Test 1: Fetching Latest NAV Data")
    print("-" * 70)
    try:
        df = fetcher.fetch_amfi_daily_nav()
        print(f"✅ SUCCESS: Fetched {len(df):,} schemes")
        print(f"\nSample data:")
        print(df[['Scheme_Code', 'Scheme_Name', 'NAV', 'AMC']].head(10))
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return
    
    # Test 2: Search functionality
    print("\n\n📋 Test 2: Searching for Schemes")
    print("-" * 70)
    try:
        results = fetcher.search_schemes("HDFC", df)
        print(f"✅ SUCCESS: Found {len(results)} HDFC schemes")
        print(f"\nTop 5 results:")
        print(results[['Scheme_Code', 'Scheme_Name', 'NAV']].head())
    except Exception as e:
        print(f"❌ FAILED: {e}")
    
    # Test 3: Category extraction
    print("\n\n📋 Test 3: Extracting Categories")
    print("-" * 70)
    try:
        df = fetcher.get_scheme_categories(df)
        print(f"✅ SUCCESS: Categorized schemes")
        print(f"\nCategory distribution:")
        print(df['Category'].value_counts())
    except Exception as e:
        print(f"❌ FAILED: {e}")
    
    # Test 4: Data preprocessing
    print("\n\n📋 Test 4: Data Preprocessing")
    print("-" * 70)
    try:
        df_clean = preprocessor.clean_nav_data(df)
        df_clean = preprocessor.calculate_returns(df_clean)
        print(f"✅ SUCCESS: Cleaned and calculated returns")
        print(f"\nReturns summary:")
        print(df_clean[['Daily_Return', 'Return_7D', 'Return_30D']].describe())
    except Exception as e:
        print(f"❌ FAILED: {e}")
    
    # Test 5: Data summary
    print("\n\n📋 Test 5: Data Summary")
    print("-" * 70)
    try:
        summary = preprocessor.get_data_summary(df_clean)
        print(f"✅ SUCCESS: Generated summary")
        print(f"\nTotal Schemes: {summary['total_schemes']:,}")
        print(f"Date Range: {summary['date_range']['start']} to {summary['date_range']['end']}")
        print(f"NAV Range: ₹{summary['nav_stats']['min']:.2f} - ₹{summary['nav_stats']['max']:.2f}")
        print(f"\nTop 5 AMCs by scheme count:")
        for amc, count in list(summary['top_amcs'].items())[:5]:
            print(f"  {amc}: {count} schemes")
    except Exception as e:
        print(f"❌ FAILED: {e}")
    
    print("\n" + "="*70)
    print("✅ All tests completed successfully!")
    print("="*70)
    print("\n🎯 Next steps:")
    print("   1. Data layer is working ✓")
    print("   2. Next: Build analytics module (financial metrics)")
    print("   3. Then: Build ML models for predictions")
    print("\n")

if __name__ == "__main__":
    main()

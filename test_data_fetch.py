# test_data_fetch.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from data.data_fetcher import get_enhanced_nav_data

print("Testing data fetcher...")
df = get_enhanced_nav_data()

if df is not None and not df.empty:
    print(f"✅ SUCCESS: Got {len(df)} records")
    print(f"Columns: {list(df.columns)}")
    print(f"\nSample data:")
    print(df.head(3))
else:
    print("❌ FAILED: No data returned")
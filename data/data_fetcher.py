import pandas as pd
import requests
from io import StringIO
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Part 1: Fetching NAV and Scheme Details (Fixes Problem #1: Categorization) ---

# AMFI NAV data - this is fast but lacks categories
AMFI_NAV_URL = "https://www.amfiindia.com/spages/NAVAll.txt"

# This API provides rich metadata (categories, types) for funds
MFAPI_URL = "https://api.mfapi.in/mf/{}"

def get_latest_navs():
    """
    Fetches the latest NAVs from the AMFI text file.
    This is fast and comprehensive.
    """
    logging.info("Fetching latest NAVs from AMFI...")
    try:
        response = requests.get(AMFI_NAV_URL, timeout=10)
        response.raise_for_status()

        # Clean the file. It has a header and empty lines.
        lines = response.text.split('\n')
        
        # Find the first line that looks like data
        data_start_index = 0
        for i, line in enumerate(lines):
            if line.strip().endswith(';'):
                data_start_index = i
                break

        if data_start_index == 0:
            logging.error("Could not find data start in AMFI file.")
            return pd.DataFrame()

        # Read the data, skipping the header.
        # The delimiter is ';' and there are no headers in the data portion.
        data = StringIO('\n'.join(lines[data_start_index:]))
        df = pd.read_csv(
            data,
            delimiter=';',
            header=None,
            usecols=[0, 1, 2, 3, 4, 5], # We only need the first 6 columns
            names=['Scheme Code', 'ISIN Div Payout', 'ISIN Div Reinvestment', 'Scheme Name', 'NAV', 'Date']
        )
        
        # Drop rows with NaN NAVs (e.g., new funds)
        df = df.dropna(subset=['NAV'])
        
        # Ensure NAV is numeric
        df['NAV'] = pd.to_numeric(df['NAV'], errors='coerce')
        
        # Filter out invalid NAVs
        df = df[df['NAV'] > 0]
        
        # Convert Date
        df['Date'] = pd.to_datetime(df['Date'], format='%d-%b-%Y', errors='coerce')
        
        # Extract AMC from Scheme Name
        df['AMC'] = df['Scheme Name'].apply(lambda x: x.split(' ')[0] if pd.notnull(x) else None)
        
        logging.info(f"Successfully fetched {len(df)} NAV records.")
        return df

    except requests.RequestException as e:
        logging.error(f"Error fetching AMFI NAV data: {e}")
        return pd.DataFrame()

def get_scheme_details(scheme_code):
    """
    Fetches detailed metadata for a single scheme code from mfapi.in.
    """
    try:
        response = requests.get(MFAPI_URL.format(scheme_code), timeout=5)
        if response.status_code == 200:
            data = response.json()
            meta = data.get('meta', {})
            return {
                'Scheme Code': scheme_code,
                'Scheme Category': meta.get('scheme_category'),
                'Scheme Type': meta.get('scheme_type'),
                'Fund House': meta.get('fund_house')
            }
    except requests.RequestException:
        # Don't log error here to avoid flooding, just return None
        return None
    return None

def get_all_scheme_details(scheme_codes):
    """
    Fetches details for all scheme codes in parallel.
    """
    logging.info(f"Fetching details for {len(scheme_codes)} schemes...")
    details_list = []
    # Use ThreadPoolExecutor for parallel API calls
    with ThreadPoolExecutor(max_workers=20) as executor:
        # Create a map of futures to scheme codes
        futures = {executor.submit(get_scheme_details, code): code for code in scheme_codes}
        
        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            if result:
                details_list.append(result)
            
            if (i + 1) % 100 == 0:
                logging.info(f"Processed {i+1}/{len(scheme_codes)} schemes...")
                
    logging.info("Finished fetching scheme details.")
    return pd.DataFrame(details_list)

def get_enhanced_nav_data():
    """
    Combines NAV data with rich scheme metadata.
    This is the dataset you should use for scheme-level analysis in Power BI.
    """
    nav_df = get_latest_navs()
    if nav_df.empty:
        logging.error("No NAV data fetched, aborting.")
        return pd.DataFrame()

    unique_scheme_codes = nav_df['Scheme Code'].unique()
    
    # Get details
    details_df = get_all_scheme_details(unique_scheme_codes)
    
    if details_df.empty:
        logging.warning("Could not fetch scheme details. Returning NAVs without categories.")
        return nav_df

    # Merge NAVs with details
    enhanced_df = pd.merge(nav_df, details_df, on='Scheme Code', how='left')
    
    # Use the Fund House from details, fallback to parsed AMC
    enhanced_df['AMC'] = enhanced_df['Fund House'].fillna(enhanced_df['AMC'])
    enhanced_df = enhanced_df.drop(columns=['Fund House']) # Clean up
    
    logging.info("Successfully merged NAVs with scheme details.")
    return enhanced_df

# --- Part 2: Fetching AMC AUM Data (Fixes Problem #2 & #3: AUM & Growth) ---

def get_aum_data():
    """
    Fetches the latest official AUM data directly from AMFI.
    This is reported, accurate data, not calculated.
    """
    logging.info("Fetching latest AUM data from AMFI...")
    try:
        # AMFI publishes AUM data in an HTML table. We can scrape this.
        # This URL is for the "AUM as on" page.
        aum_url = "https://www.amfiindia.com/research-information/aum-data/average-aum"
        
        # pandas.read_html can scrape tables from a URL
        # We need to set a user-agent to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        
        # Make the request with headers
        response = requests.get(aum_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # pandas read_html returns a list of all tables found
        tables = pd.read_html(StringIO(response.text))
        
        # Find the correct table. It's usually the one with "AMC" and "AUM"
        aum_df = None
        for table in tables:
            if 'Fund House' in table.columns and any(col for col in table.columns if 'Average AUM' in col):
                aum_df = table
                break
        
        if aum_df is None:
            logging.error("Could not find the AUM table on the AMFI page.")
            return pd.DataFrame()

        # The table structure might be nested. Let's find the main AUM column.
        # Example: ('Average AUM for the Month', ' (Rs. in Lacs)')
        # We need to flatten multi-index headers if they exist
        if isinstance(aum_df.columns, pd.MultiIndex):
            # A common structure is ('Header', 'Sub-Header'). We join them.
             aum_df.columns = ['_'.join(col).strip() for col in aum_df.columns.values]
        
        # Now find the AUM and Fund House columns
        # Column names on the site can change, so we search flexibly
        fund_house_col = next((col for col in aum_df.columns if 'Fund House' in col), None)
        aum_col = next((col for col in aum_df.columns if 'Average AUM' in col and 'Lacs' in col), None)

        if not fund_house_col or not aum_col:
            logging.error(f"Could not identify columns in scraped table. Columns found: {aum_df.columns}")
            return pd.DataFrame()

        # Select and rename the columns
        aum_df = aum_df[[fund_house_col, aum_col]]
        aum_df.columns = ['AMC', 'AUM (Lacs)']

        # Clean the data
        # Remove the 'Total' row
        aum_df = aum_df[aum_df['AMC'].str.contains('Total') == False].copy()
        
        # Convert AUM to numeric
        aum_df['AUM (Lacs)'] = pd.to_numeric(aum_df['AUM (Lacs)'], errors='coerce')
        
        # Convert from Lacs to Crores for easier reading
        aum_df['AUM (Crores)'] = aum_df['AUM (Lacs)'] / 100
        
        # Calculate Market Share
        total_aum = aum_df['AUM (Crores)'].sum()
        aum_df['Market Share'] = (aum_df['AUM (Crores)'] / total_aum)
        
        logging.info(f"Successfully fetched AUM data for {len(aum_df)} AMCs.")
        return aum_df.drop(columns=['AUM (Lacs)'])

    except requests.RequestException as e:
        logging.error(f"Error fetching AUM data: {e}")
        return pd.DataFrame()
    except Exception as e:
        logging.error(f"Error processing AUM table: {e}")
        return pd.DataFrame()

# --- Part 3: Fetching Historical NAV (FIX: ADDING THIS FUNCTION) ---

@pd.api.extensions.register_dataframe_accessor("cache")
class CachingAccessor:
    def __init__(self, pandas_obj):
        self._obj = pandas_obj
    
    # You can add caching logic here if needed, for now just a placeholder
    def load(self, *args, **kwargs):
        pass

def get_nav_history(scheme_code: str) -> pd.DataFrame:
    """
    Fetches the complete NAV history for a single scheme from mfapi.in.
    This is required by the backend routes.
    """
    logging.info(f"Fetching NAV history for {scheme_code}...")
    try:
        # Use the correct MFAPI_URL defined at the top
        response = requests.get(MFAPI_URL.format(scheme_code), timeout=10)
        response.raise_for_status()
        
        data = response.json()
        nav_history = data.get('data')
        
        if not nav_history:
            logging.warning(f"No 'data' block found for scheme {scheme_code}")
            return pd.DataFrame()

        # Convert list of dicts to DataFrame
        history_df = pd.DataFrame(nav_history)
        
        # Clean and format the data
        history_df['date'] = pd.to_datetime(history_df['date'], format='%d-%m-%Y')
        history_df['nav'] = pd.to_numeric(history_df['nav'], errors='coerce')
        
        # Sort by date
        history_df = history_df.sort_values(by='date').reset_index(drop=True)
        
        logging.info(f"Successfully fetched {len(history_df)} history records for {scheme_code}.")
        return history_df

    except requests.RequestException as e:
        logging.error(f"Error fetching NAV history for {scheme_code}: {e}")
        return pd.DataFrame()
    except Exception as e:
        logging.error(f"Error processing NAV history for {scheme_code}: {e}")
        return pd.DataFrame()
# --- END FIX ---


# --- Main execution ---

if __name__ == "__main__":
    # This block is for testing
    
    # Test 1: Get enhanced NAV data (with categories)
    logging.info("--- Running NAV Data Fetcher ---")
    start_time = time.time()
    nav_data = get_enhanced_nav_data()
    logging.info(f"NAV data fetch took {time.time() - start_time:.2f} seconds.")
    if not nav_data.empty:
        print(nav_data.head())
        print("\nSample of categories:")
        print(nav_data['Scheme Category'].value_counts().head())
        
        # Save to cache for inspection
        nav_data.to_csv("cache/enhanced_nav_data.csv", index=False)
        logging.info("Saved enhanced_nav_data.csv to cache/")

    # Test 2: Get AUM data
    logging.info("\n--- Running AUM Data Fetcher ---")
    start_time = time.time()
    aum_data = get_aum_data()
    logging.info(f"AUM data fetch took {time.time() - start_time:.2f} seconds.")
    if not aum_data.empty:
        print(aum_data.sort_values(by='Market Share', ascending=False).head())
        
        # Save to cache for inspection
        aum_data.to_csv("cache/latest_aum_data.csv", index=False)
        logging.info("Saved latest_aum_data.csv to cache/")

    # Test 3: Get NAV History
    logging.info("\n--- Running NAV History Fetcher (Test) ---")
    start_time = time.time()
    # Test with a known scheme (e.g., an SBI fund)
    history_data = get_nav_history("120503") 
    logging.info(f"NAV history fetch took {time.time() - start_time:.2f} seconds.")
    if not history_data.empty:
        print(history_data.head())
        print(history_data.tail())
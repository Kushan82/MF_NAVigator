import pandas as pd
import logging
import os
import sys

# Add the root directory to the Python path
# This allows us to import from the 'data' module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # We will use the new, robust data fetcher
    from data.data_fetcher import get_enhanced_nav_data, get_aum_data
except ImportError:
    logging.error("Could not import data_fetcher. Make sure it's in the 'data' directory.")
    sys.exit(1)


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define output paths for the CSV files
# Power BI will read from this 'powerbi_data' directory
OUTPUT_DIR = "powerbi_data"
NAV_OUTPUT_PATH = os.path.join(OUTPUT_DIR, "fact_nav_data.csv")
AUM_OUTPUT_PATH = os.path.join(OUTPUT_DIR, "dim_amc_aum.csv")
SCHEME_OUTPUT_PATH = os.path.join(OUTPUT_DIR, "dim_scheme_details.csv")

def create_output_directory():
    """Ensures the output directory exists."""
    if not os.path.exists(OUTPUT_DIR):
        logging.info(f"Creating directory: {OUTPUT_DIR}")
        os.makedirs(OUTPUT_DIR)

def export_data_for_powerbi():
    """
    Fetches the enhanced data and exports it into a clean
    Star-Schema format (Fact & Dimension tables) for Power BI.
    """
    create_output_directory()
    
    # --- 1. Fetch AUM Data (Dimension Table) ---
    logging.info("Fetching AUM data...")
    dim_amc_aum = get_aum_data()
    
    if dim_amc_aum.empty:
        logging.error("Failed to fetch AUM data. Aborting export.")
        return
    
    # Save the AMC AUM data
    dim_amc_aum.to_csv(AUM_OUTPUT_PATH, index=False, encoding='utf-8')
    logging.info(f"Successfully exported AMC AUM data to {AUM_OUTPUT_PATH}")

    # --- 2. Fetch Enhanced NAV Data ---
    logging.info("Fetching enhanced NAV data... (This may take a few minutes)")
    enhanced_nav_data = get_enhanced_nav_data()
    
    if enhanced_nav_data.empty:
        logging.error("Failed to fetch NAV data. Aborting export.")
        return

    # --- 3. Split NAV data into Fact and Dimension tables ---
    
    # 'dim_scheme_details' (Dimension Table)
    # This table holds the metadata for each scheme.
    # It should have one row per Scheme Code.
    dim_scheme_columns = [
        'Scheme Code', 
        'Scheme Name', 
        'Scheme Category', 
        'Scheme Type', 
        'AMC', 
        'ISIN Div Payout', 
        'ISIN Div Reinvestment'
    ]
    # Drop duplicates to ensure one row per scheme
    dim_scheme_details = enhanced_nav_data[dim_scheme_columns].drop_duplicates(subset=['Scheme Code'])
    
    # Save the Scheme Details dimension table
    dim_scheme_details.to_csv(SCHEME_OUTPUT_PATH, index=False, encoding='utf-8')
    logging.info(f"Successfully exported Scheme Details data to {SCHEME_OUTPUT_PATH}")

    # 'fact_nav_data' (Fact Table)
    # This table holds the transactional data (NAVs over time).
    # It should only contain keys and measures.
    fact_nav_columns = ['Date', 'Scheme Code', 'NAV']
    fact_nav_data = enhanced_nav_data[fact_nav_columns]
    
    # Save the NAV Fact table
    fact_nav_data.to_csv(NAV_OUTPUT_PATH, index=False, encoding='utf-8')
    logging.info(f"Successfully exported NAV Fact data to {NAV_OUTPUT_PATH}")
    
    logging.info("\n--- Power BI Export Complete ---")
    logging.info(f"Fact Table: {NAV_OUTPUT_PATH} ({len(fact_nav_data)} rows)")
    logging.info(f"Scheme Dimension: {SCHEME_OUTPUT_PATH} ({len(dim_scheme_details)} rows)")
    logging.info(f"AMC Dimension: {AUM_OUTPUT_PATH} ({len(dim_amc_aum)} rows)")

if __name__ == "__main__":
    # Run the export process
    export_data_for_powerbi()
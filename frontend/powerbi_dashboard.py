"""
Power BI Dashboard Page - FIXED VERSION
Fixes the Power BI exporter button to run as a subprocess.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import sys
import subprocess # Import subprocess
import os # Import os
import logging

# Add project root to sys.path
# This ensures imports work when run with `streamlit run`
current_dir = Path(__file__).parent.parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# --- REMOVED BROKEN IMPORTS ---
# from models.powerbi_exporter import run_export_pipeline, get_aum_data
# from frontend.utils.api_client import APIClient
# --- END REMOVED ---


def render():
    """Render analytics dashboard page"""
    
    st.markdown("# 📊 Power BI Dashboard") # Renamed title to be specific
    st.markdown("Data export and setup guide for your Power BI dashboard")
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs([
        "📈 Market Overview",
        "📊 Power BI Export",
        "🔧 Power BI Setup Guide"
    ])
    
    with tab1:
        render_market_overview()
    
    with tab2:
        render_powerbi_export()
    
    with tab3:
        render_powerbi_guide()


def render_market_overview():
    """Render market overview with filters"""
    
    st.markdown("### 📊 Market Overview")
    
    powerbi_dir = Path("powerbi_data")
    
    # Check if data exists
    if not powerbi_dir.exists() or not list(powerbi_dir.glob("*.csv")):
        st.warning("⚠️ No data available. Please export data first.")
        
        if st.button("📊 Go to Power BI Export Tab"):
            # This is a hack to switch tabs; Streamlit doesn't support this directly.
            # We just instruct the user.
            st.info("Please click the 'Power BI Export' tab above to generate data.")
        return

    st.info("Data has been exported. Please open the `data.pbix` file in the `powerbi_data` directory.")
    
    # --- SECTION REPLACED ---
    # The old code tried to fetch and display AUM data here.
    # We remove this, as the new flow is:
    # 1. Export data here.
    # 2. View in Power BI Desktop.
    
    st.markdown("#### How to View the Dashboard")
    st.markdown("1.  Go to the **Power BI Export** tab and click **Run Data Exporter**.")
    st.markdown("2.  Open the `powerbi_data` folder in your project.")
    st.markdown("3.  Open the `data.pbix` file with Power BI Desktop.")
    st.markdown("4.  Click the **Refresh** button in the Power BI toolbar to load the new CSVs.")


def render_powerbi_export():
    """Render Power BI export section"""
    
    st.markdown("### 🚀 Power BI Data Export")
    st.markdown("Run this exporter to generate the latest CSV files required for the Power BI dashboard (`data.pbix`).")
    
    if st.button("Run Data Exporter", type="primary"):
        
        # Use relative path from project root
        exporter_script_path = "models/export_for_powerbi.py"
        
        if not os.path.exists(exporter_script_path):
            st.error(f"Exporter script not found at {exporter_script_path}")
            st.info(f"Please ensure you are running Streamlit from the project's root directory. Current directory: {os.getcwd()}")
            return

        with st.spinner(f"Running exporter at `{exporter_script_path}`... This may take a minute..."):
            try:
                # --- THIS IS THE FIX ---
                # We run the exporter script using the same Python executable
                # that is running Streamlit. This is robust.
                
                process = subprocess.run(
                    [sys.executable, exporter_script_path],
                    capture_output=True, text=True, check=True, encoding='utf-8'
                )
                
                st.success("✅ Data export complete!")
                st.text("Exporter Log:")
                st.code(process.stdout, language="log")
                if process.stderr:
                    st.text("Exporter Errors (if any):")
                    st.code(process.stderr, language="log")
                
                st.info("You can now open `powerbi_data/data.pbix` in Power BI Desktop and click 'Refresh'.")
                
            except subprocess.CalledProcessError as e:
                st.error(f"Failed to run exporter script:")
                st.text("STDOUT:")
                st.code(e.stdout, language="log")
                st.text("STDERR:")
                st.code(e.stderr, language="log")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
                logging.error(f"Exporter button failed: {e}", exc_info=True)
                
    st.markdown("---\n*This process fetches live data from AMFI and mfapi.in, then saves it to the `powerbi_data` folder.*")


def render_powerbi_guide():
    """Render Power BI setup guide"""
    
    st.markdown("### 🔧 Power BI Setup Guide")
    st.info("This guide explains how the Power BI file is set up and how to fix common issues.")
    
    st.markdown("""
    #### Data Model (Star Schema)
    The Power BI file uses a "Star Schema" for performance.
    
    * **Fact Table (Numbers):** `fact_nav_data.csv`
    * **Dimension Tables (Details):** 1.  `dim_scheme_details.csv`
        2.  `dim_amc_aum.csv`
        
    #### Relationships
    1.  `dim_scheme_details[Scheme Code]` (One) -> `fact_nav_data[Scheme Code]` (Many)
    2.  `dim_amc_aum[AMC]` (One) -> `dim_scheme_details[AMC]` (Many)
    
    This model allows you to filter millions of NAV records instantly by clicking an AMC or Scheme Category.
    
    ---
    
    ####  Troubleshooting
    
    **Issue: Data is old**
    - Click "Run Data Exporter" on the "Power BI Export" tab
    - Open `data.pbix` and click "Refresh"
    
    **Issue: Filters not working**
    - In Power BI, go to the "Model" view.
    - Check that the relationships above exist and are active.
    
    **Issue: Incorrect CAGR / Growth**
    - The AUM data is the latest *monthly* snapshot.
    - To calculate AUM growth, the `data_fetcher.py` script would need to be expanded to scrape historical AUM reports from AMFI.
    - NAV-based CAGR is calculated in the app itself (`Scheme Analysis` page).
    """)
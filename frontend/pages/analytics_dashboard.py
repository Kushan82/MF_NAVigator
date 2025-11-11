"""
Analytics Dashboard Page - FIXED
This page now properly fetches AUM data from the new /api/nav/amc endpoint.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit.components.v1 as components
from frontend.utils.api_client import APIClient
from pathlib import Path
import logging

api = APIClient()

def render():
    """Render analytics dashboard page"""
    
    st.markdown("# 📊 Analytics Dashboard")
    st.markdown("Advanced data analytics and market insights")
    st.markdown("---")
    
    # Dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Market Overview", # Changed title back
        "🔥 Top Performers",
        "📊 Category Analysis",
        "🎯 Advanced Analytics"
    ])
    
    with tab1:
        # --- FIX: Renamed function to match your original file ---
        render_market_overview()
    
    with tab2:
        render_top_performers()
    
    with tab3:
        render_category_analysis()
    
    with tab4:
        render_advanced_analytics()

# --- FIX: This function now fetches data from the API ---
@st.cache_data(ttl=3600)
def get_aum_data_from_api():
    """Fetches AUM data from the new /api/nav/amc endpoint"""
    try:
        # This API call maps to /nav/amc
        return api.get_aum_data() 
    except Exception as e:
        logging.error(f"Failed to load AUM data: {e}")
        return []

def render_market_overview():
    """Render Power BI market overview with data export"""
    
    st.markdown("### 📊 AMC Market Overview")
    
    aum_data = get_aum_data_from_api()
    
    if not aum_data:
        st.error("Could not load AUM data from the API. Please ensure the backend is running.")
        return

    df = pd.DataFrame(aum_data)

    # --- FIX: Our new API provides clean, correct columns ---
    if 'AMC' not in df.columns or 'AUM (Crores)' not in df.columns or 'Market Share' not in df.columns:
        st.error("Received incomplete AUM data from API. Expected 'AMC', 'AUM (Crores)', and 'Market Share'.")
        logging.error(f"Unexpected AUM data columns: {df.columns}")
        return

    # Ensure types are correct for plotting
    df['AUM (Crores)'] = pd.to_numeric(df['AUM (Crores)'], errors='coerce')
    df['Market Share'] = pd.to_numeric(df['Market Share'], errors='coerce')

    st.header("AMC Market Share")

    # Top 10 AMCs by Market Share
    top_10_amcs = df.nlargest(10, 'Market Share')
    fig_pie = px.pie(top_10_amcs, values='Market Share', names='AMC', 
                     title='Top 10 AMCs by Market Share',
                     hover_data={'Market Share': ':.2%'}) # Format hover as percentage
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')

    # Treemap for all AMCs
    fig_treemap = px.treemap(df, path=['AMC'], values='AUM (Crores)',
                             title='AUM Distribution (All AMCs)',
                             hover_data={'AUM (Crores)': ':.2f Cr'}) # Format hover
    fig_treemap.data[0].textinfo = 'label+value'


    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_pie, use_container_width=True)
    with col2:
        st.plotly_chart(fig_treemap, use_container_width=True)

    st.header("AUM Data Table")
    # Format columns for display
    df_display = df.sort_values(by='Market Share', ascending=False).copy()
    df_display['Market Share'] = df_display['Market Share'].map('{:.2%}'.format)
    df_display['AUM (Crores)'] = df_display['AUM (Crores)'].map('{:,.2f} Cr'.format)

    st.dataframe(df_display, use_container_width=True, hide_index=True)
# --- END FIX ---


def render_top_performers():
    """Render top performers section"""
    
    st.markdown("### 🔥 Top Performers")
    
    st.info("🚧 Top performers analysis coming soon!")
    
    st.markdown("""
    **Will display:**
    - Top 10 gainers (daily/weekly/monthly)
    - Top 10 losers
    - Most volatile funds
    - Highest volume traded
    - Best risk-adjusted returns (Sharpe)
    """)


def render_category_analysis():
    """Render category analysis section"""
    
    st.markdown("### 📊 Category Analysis")
    
    st.info("🚧 Category analysis coming soon!")
    
    st.markdown("""
    **Planned visualizations:**
    - Performance by category
    - Category-wise distribution
    - Risk-return by category
    - Top schemes in each category
    - Category trends over time
    """)


def render_advanced_analytics():
    """Render advanced analytics section"""
    
    st.markdown("### 🎯 Advanced Analytics")
    
    st.info("🚧 Advanced analytics tools coming soon!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Statistical Analysis:**
        - Correlation heatmap
        - Distribution analysis
        - Rolling statistics
        - Regression analysis
        - Factor analysis
        """)
    
    with col2:
        st.markdown("""
        **Predictive Analytics:**
        - Time series forecasting
        - Monte Carlo simulation
        - Cluster analysis
        - Anomaly detection
        - Sentiment analysis
        """)
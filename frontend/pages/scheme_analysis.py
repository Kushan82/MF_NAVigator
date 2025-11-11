"""
Scheme Analysis Page - Detailed metrics with advanced search
FIXED: Removed bad import for 'search_bar'.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from frontend.utils.api_client import APIClient
import logging # Added for error tracking

api = APIClient()

def render():
    """Render scheme analysis page"""
    
    st.markdown("# 📊 Scheme Analysis")
    st.markdown("Detailed financial and risk analysis for any mutual fund scheme")
    st.markdown("---")
    
    # Check if scheme was selected from another page
    if st.session_state.get('selected_scheme_code'):
        render_scheme_analysis(st.session_state['selected_scheme_code'])
        # Clear the state so it doesn't stick
        st.session_state['selected_scheme_code'] = None
    else:
        render_scheme_search()

def render_scheme_search():
    """Render scheme search with filters"""
    
    st.markdown("### 🔍 Search Scheme to Analyze")
    
    # Search tabs
    tab1, tab2 = st.tabs(["🔍 Quick Search", "🎯 Advanced Filters"])
    
    with tab1:
        render_quick_search()
    
    with tab2:
        render_advanced_filters()

def render_quick_search():
    """Render quick search interface"""
    
    st.markdown("#### Quick Search")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input("Search by scheme name or code:", key="analysis_search")
    
    with col2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        search_button = st.button("Search", key="analysis_search_btn")

    if search_button and search_query:
        with st.spinner("Searching..."):
            try:
                # This API call maps to /nav/search, which is correct
                results = api.search_schemes(search_query)
                if results:
                    st.session_state['analysis_search_results'] = results
                else:
                    st.warning("No schemes found.")
            except Exception as e:
                st.error(f"Search failed: {e}")
    
    if 'analysis_search_results' in st.session_state:
        results = st.session_state['analysis_search_results']
        for item in results:
            if st.button(f"{item['Scheme Name']} ({item['Scheme Code']})", key=f"select_{item['Scheme Code']}"):
                st.session_state['selected_scheme_code_from_search'] = item['Scheme Code']
                st.session_state.pop('analysis_search_results', None) # Clear search results
                st.rerun() # Rerun to load the analysis page

    if st.session_state.get('selected_scheme_code_from_search'):
        render_scheme_analysis(st.session_state.pop('selected_scheme_code_from_search'))


def render_advanced_filters():
    """Render advanced filters interface"""
    st.info("🚧 Advanced filters coming soon!")
    # Placeholder for advanced filters
    # This could use the new /nav/categories endpoint
    
    # try:
    #     if 'nav_categories' not in st.session_state:
    #         st.session_state['nav_categories'] = api.get_categories()
    #     categories = st.session_state['nav_categories']
    #     st.multiselect("Filter by Category:", options=categories.get('categories', []))
    #     st.multiselect("Filter by Type:", options=categories.get('types', []))
    # except Exception as e:
    #     st.error(f"Could not load categories: {e}")


def render_scheme_analysis(scheme_code: str):
    """Render the main analysis for the selected scheme"""
    
    st.markdown(f"### Analyzing Scheme: `{scheme_code}`")
    
    try:
        render_scheme_details(scheme_code)
        render_financial_summary(scheme_code)
        render_risk_summary(scheme_code)
        render_historical_section(scheme_code)
    
    except Exception as e:
        st.error(f"Failed to load all scheme data: {e}")
        logging.error(f"Error rendering scheme analysis for {scheme_code}: {e}", exc_info=True)

def render_scheme_details(scheme_code: str):
    """Render scheme details section"""
    
    st.markdown("#### General Details")
    
    # --- FIX ---
    # We get details from the all_schemes_data loaded on the Home page
    # This avoids a new API call and uses the new categorized data
    
    if 'all_schemes_data' not in st.session_state or not st.session_state['all_schemes_data']:
        st.warning("All schemes data not found in session. Please visit Home page first to load data.")
        # Fallback to API call if session is empty
        try:
            with st.spinner("Loading scheme data..."):
                all_schemes = api.get_all_nav()
                st.session_state['all_schemes_data'] = all_schemes
        except Exception as e:
            st.error(f"Failed to load scheme data from API: {e}")
            return
    
    all_schemes_df = pd.DataFrame(st.session_state['all_schemes_data'])
    
    # Find the scheme
    # Ensure Scheme Code is string for matching
    all_schemes_df['Scheme Code'] = all_schemes_df['Scheme Code'].astype(str)
    scheme_details = all_schemes_df[all_schemes_df['Scheme Code'] == str(scheme_code)]
    
    if scheme_details.empty:
        st.error(f"Could not find details for Scheme Code: {scheme_code}")
        return

    details = scheme_details.iloc[0]
    
    st.subheader(details['Scheme Name'])
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Latest NAV", f"₹{float(details['NAV']):.2f}")
    col2.metric("As of Date", pd.to_datetime(details['Date']).strftime('%d-%b-%Y'))
    
    # --- ENHANCEMENT: Display new data ---
    col3.metric("Category", details.get('Scheme Category', 'N/A'))
    col4.metric("Type", details.get('Scheme Type', 'N/A'))
    # --- END ENHANCEMENT ---


def render_financial_summary(scheme_code: str):
    """Render financial summary (CAGR)"""
    
    st.markdown("#### 📈 Financial Metrics (CAGR)")
    
    # --- FIX ---
    # The old `get_financial_metrics` endpoint doesn't exist.
    # We will call the `get_cagr` endpoint for 1, 3, and 5 years.
    
    cagr_data = {}
    with st.spinner("Calculating CAGR..."):
        for years in [1, 3, 5]:
            try:
                # This API call maps to /analytics/cagr/{scheme_code}
                cagr_val = api.get_cagr(scheme_code, years)
                cagr_data[f"{years}-Year"] = cagr_val.get('cagr')
            except Exception:
                cagr_data[f"{years}-Year"] = None # Show N/A if calc fails
    # --- END FIX ---
    
    col1, col2, col3 = st.columns(3)
    col1.metric("1-Year CAGR", f"{cagr_data['1-Year']:.2f}%" if cagr_data['1-Year'] is not None else "N/A")
    col2.metric("3-Year CAGR", f"{cagr_data['3-Year']:.2f}%" if cagr_data['3-Year'] is not None else "N/A")
    col3.metric("5-Year CAGR", f"{cagr_data['5-Year']:.2f}%" if cagr_data['5-Year'] is not None else "N/A")

def render_risk_summary(scheme_code: str):
    """Render risk summary section"""
    
    st.markdown("#### ⚠️ Risk Metrics")
    
    try:
        with st.spinner("Calculating Risk Metrics..."):
            # This API call maps to /analytics/risk/{scheme_code}, which is correct
            rm = api.get_risk_metrics(scheme_code)
    except Exception as e:
        st.error(f"Could not calculate risk metrics: {e}")
        return

    # --- FIX: Ensure values are formatted correctly from float ---
    metrics_data = (
        ["Std Deviation (Volatility)", f"{rm.get('std_dev', 0):.2f}%"],
        ["Sharpe Ratio", f"{rm.get('sharpe_ratio', 0):.2f}"],
        ["Sortino Ratio", f"{rm.get('sortino_ratio', 0):.2f}"],
        ["Max Drawdown", f"{rm.get('max_drawdown', 0):.2f}%"],
        ["Value at Risk (VaR 95%)", f"{rm.get('var_95', 0):.2f}%"]
    )
    # --- END FIX ---
    
    df_summary = pd.DataFrame(metrics_data, columns=["Metric", "Value"])
    
    st.dataframe(df_summary, use_container_width=True, hide_index=True)

def render_historical_section(scheme_code: str):
    """Render historical data section"""
    
    st.markdown("### 📈 Historical NAV Data")
    
    with st.expander("View Historical Data Chart"):
        try:
            with st.spinner("Fetching historical data..."):
                # This API call maps to /nav/history/{scheme_code}, which is correct
                hist_data = api.get_nav_history(scheme_code) # Corrected function name
                
                if hist_data:
                    df_hist = pd.DataFrame(hist_data)
                    df_hist['date'] = pd.to_datetime(df_hist['date'])
                    
                    # Plot
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df_hist['date'],
                        y=df_hist['nav'],
                        mode='lines',
                        name='NAV'
                    ))
                    
                    fig.update_layout(
                        title=f"NAV History",
                        xaxis_title="Date",
                        yaxis_title="NAV (₹)",
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.dataframe(df_hist.sort_values('date', ascending=False), use_container_width=True, height=300)
                else:
                    st.warning("No historical data found for this scheme.")
        except Exception as e:
            st.error(f"Could not load historical data: {e}")
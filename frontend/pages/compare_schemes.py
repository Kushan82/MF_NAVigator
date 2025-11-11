"""
Compare Schemes Page - Side-by-side comparison with advanced Plotly visualizations
FIXED: Removed bad imports and aligned with new API.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from frontend.utils.api_client import APIClient
import numpy as np
import logging

api = APIClient()

# --- NEW: Function to cache categories ---
@st.cache_data(ttl=3600)
def get_scheme_categories():
    """Fetches categories from the new API endpoint"""
    try:
        return api.get_categories()
    except Exception as e:
        logging.error(f"Failed to get scheme categories: {e}")
        return {"categories": [], "types": []}
# --- END NEW ---

def render():
    """Render compare schemes page with enhanced visualizations"""
    
    st.markdown("# ⚖️ Compare Schemes")
    st.markdown("Side-by-side comparison with advanced analytics")
    st.markdown("---")
    
    # Initialize compare list if doesn't exist
    if 'compare_schemes_list' not in st.session_state:
        st.session_state['compare_schemes_list'] = []
    
    # Initialize show_add_form flag
    if 'show_compare_add_form' not in st.session_state:
        st.session_state['show_compare_add_form'] = False
    
    # Display current list or add interface
    if len(st.session_state['compare_schemes_list']) > 0:
        render_comparison_interface()
    else:
        st.info("👆 No schemes added yet. Add schemes from Home page or search below.")
        render_add_scheme_interface()

def render_add_scheme_interface():
    """Render the interface to add schemes to the comparison list"""
    
    st.markdown("### ➕ Add Schemes to Compare")

    # --- ENHANCEMENT: Add category filter ---
    categories_data = get_scheme_categories()
    categories = ["All Categories"] + sorted(categories_data.get('categories', []))
    selected_category = st.selectbox("Filter by Category:", categories)
    # --- END ENHANCEMENT ---

    search_query = st.text_input("Search by scheme name:", key="compare_search")

    if search_query:
        with st.spinner("Searching..."):
            try:
                # This API call maps to /nav/search, which is correct
                results = api.search_schemes(search_query)
                
                if results:
                    # --- FIX: We must load all scheme data to filter by category ---
                    if 'all_schemes_data' not in st.session_state or not st.session_state['all_schemes_data']:
                        st.session_state['all_schemes_data'] = api.get_all_nav()
                    
                    all_schemes_df = pd.DataFrame(st.session_state['all_schemes_data'])
                    all_schemes_df['Scheme Code'] = all_schemes_df['Scheme Code'].astype(str)
                    
                    # Get scheme codes from search results
                    result_codes = [str(r['Scheme Code']) for r in results]
                    
                    # Filter this list by category
                    if selected_category != "All Categories":
                        filtered_codes = all_schemes_df[
                            (all_schemes_df['Scheme Code'].isin(result_codes)) &
                            (all_schemes_df['Scheme Category'] == selected_category)
                        ]['Scheme Code'].tolist()
                        
                        # Now filter the original results list
                        results = [r for r in results if str(r['Scheme Code']) in filtered_codes]
                        if not results:
                             st.warning(f"No schemes found for '{search_query}' in category '{selected_category}'.")
                    # --- END FIX ---
                    
                    if results:
                        st.session_state['compare_search_results'] = results
                else:
                    st.warning("No schemes found.")
            except Exception as e:
                st.error(f"Search failed: {e}")

    if 'compare_search_results' in st.session_state:
        results = st.session_state['compare_search_results']
        for item in results:
            if st.button(f"➕ {item['Scheme Name']}", key=f"add_comp_{item['Scheme Code']}"):
                if item['Scheme Code'] not in [s['Scheme Code'] for s in st.session_state['compare_schemes_list']]:
                    st.session_state['compare_schemes_list'].append(item)
                    st.session_state.pop('compare_search_results', None) # Clear search
                    st.rerun()
                else:
                    st.warning("Scheme already in comparison list.")


def render_comparison_interface():
    """Render the main comparison view for selected schemes"""
    
    schemes = st.session_state['compare_schemes_list']
    scheme_codes = [s['Scheme Code'] for s in schemes]
    scheme_names = {s['Scheme Code']: s['Scheme Name'] for s in schemes}

    st.markdown(f"### Comparing {len(schemes)} Schemes")
    
    # Display selected schemes as tags
    cols = st.columns(min(len(schemes) + 1, 6)) # Max 6 columns
    for i, s in enumerate(schemes):
        with cols[i % 5]: # Wrap to next row if more than 5
            if st.button(f"❌ {s['Scheme Name']}", key=f"remove_comp_{s['Scheme Code']}"):
                st.session_state['compare_schemes_list'] = [sch for sch in schemes if sch['Scheme Code'] != s['Scheme Code']]
                st.rerun()
    
    with cols[len(schemes) % 5 if len(schemes) < 5 else 5]:
        if st.button("➕ Add More"):
            st.session_state['show_compare_add_form'] = True
            st.rerun()
            
    if st.session_state.get('show_compare_add_form'):
        render_add_scheme_interface()
        
    st.markdown("---")
    
    # Fetch comparison data
    try:
        with st.spinner("Fetching comparison data..."):
            # This API call maps to /analytics/compare, which is correct
            comp_data = api.compare_schemes(scheme_codes)
            if not comp_data:
                st.error("Could not fetch comparison data.")
                return
    except Exception as e:
        st.error(f"Failed to fetch comparison: {e}")
        return

    # Render visualizations
    render_normalized_nav_chart(comp_data.get('normalized_performance', {}), scheme_names)
    render_metrics_table(comp_data.get('metrics', {}))
    render_radar_chart(comp_data.get('metrics', {}))


def render_normalized_nav_chart(data: dict, names: dict):
    """Render normalized NAV chart"""
    st.markdown("#### 📈 Normalized Performance (Rebased to 100)")
    
    fig = go.Figure()
    if not data:
        st.warning("No normalized performance data available.")
        return
        
    for code, hist_data_list in data.items():
        if not hist_data_list: # Skip if empty list
            continue
        df = pd.DataFrame(hist_data_list)
        if 'date' not in df.columns or 'normalized_nav' not in df.columns:
            logging.warning(f"Skipping scheme {code}: missing 'date' or 'normalized_nav'")
            continue
            
        fig.add_trace(go.Scatter(
            x=pd.to_datetime(df['date']),
            y=df['normalized_nav'],
            mode='lines',
            name=names.get(code, code)
        ))
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Normalized NAV",
        hovermode="x unified",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

def render_metrics_table(data: dict):
    """Render metrics comparison table"""
    st.markdown("#### 📋 Metrics Table")
    if not data:
        st.warning("No metrics data available.")
        return
        
    df = pd.DataFrame(data)
    if 'scheme_code' in df.columns:
        df = df.set_index('scheme_code')
        
    st.dataframe(df, use_container_width=True)

def render_radar_chart(data: dict):
    """Render multi-metric radar chart"""
    st.markdown("#### 🕸️ Multi-Metric Radar (Higher Score = Better)")
    
    if not data:
        st.warning("No metrics data available for radar chart.")
        return
        
    df = pd.DataFrame(data)
    if df.empty:
        return
    
    # Use scheme_name if available, else scheme_code
    if 'scheme_name' not in df.columns:
        df['scheme_name'] = df['scheme_code']

    # Metrics to include in radar (must be numeric)
    metrics = ['cagr_1y', 'cagr_3y', 'sharpe_ratio', 'sortino_ratio', 'volatility', 'max_drawdown']
    
    # Ensure all metrics are numeric, fill N/A with 0
    for m in metrics:
        if m not in df.columns:
            df[m] = 0.0 # Add column if missing
        df[m] = pd.to_numeric(df[m], errors='coerce').fillna(0)

    # Normalize data
    df_norm = df.copy()
    for m in metrics:
        min_val = df[m].min()
        max_val = df[m].max()
        range_val = max_val - min_val
        if range_val == 0:
            df_norm[m] = 50.0 # All values are same
        else:
            # For volatility and max drawdown, lower is better (invert score)
            if m in ['volatility', 'max_drawdown']:
                df_norm[m] = 100 - ((df[m] - min_val) / range_val * 100)
            else:
                df_norm[m] = (df[m] - min_val) / range_val * 100

    fig = go.Figure()
    
    for _, row in df_norm.iterrows():
        values = row[metrics].values.tolist()
        labels = [m.replace('_', ' ').title() for m in metrics]
        
        # Close the radar chart
        values.append(values[0])
        labels.append(labels[0])
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=labels,
            fill='toself',
            name=row['scheme_name'], # Use name
            hovertemplate='%{theta}<br>Score: %{r:.1f}<extra></extra>'
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True,
        title="Multi-Metric Comparison (Higher = Better Performance)",
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Legend
    st.info("""
    **📌 How to Read:**
    - All metrics normalized to 0-100. A larger area is better.
    - `Volatility` and `Max Drawdown` are inverted (lower is better, so it results in a higher score).
    """)
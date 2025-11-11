"""
Compare Schemes Page - COMPLETE VERSION
Side-by-side comparison with advanced Plotly visualizations
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from frontend.utils.api_client import APIClient
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api = APIClient()

# ==========================================
# CACHED DATA FUNCTIONS
# ==========================================

@st.cache_data(ttl=3600)
def get_scheme_categories():
    """Fetch categories from API (cached)"""
    try:
        return api._make_request("GET", f"{api.api_v1}/nav/categories", show_error=False)
    except Exception as e:
        logger.error(f"Failed to get categories: {e}")
        return {"categories": [], "types": []}

@st.cache_data(ttl=3600)
def get_all_nav_data():
    """Fetch all NAV data (cached)"""
    try:
        return api._make_request("GET", f"{api.api_v1}/nav", show_error=False)
    except Exception as e:
        logger.error(f"Failed to get NAV data: {e}")
        return []

# ==========================================
# MAIN RENDER FUNCTION
# ==========================================

def render():
    """Render compare schemes page"""
    
    st.markdown("# ⚖️ Compare Schemes")
    st.markdown("Side-by-side comparison with advanced analytics")
    st.markdown("---")
    
    # Initialize compare list if doesn't exist
    if 'compare_schemes_list' not in st.session_state:
        st.session_state['compare_schemes_list'] = []
    
    # Display current list or add interface
    if len(st.session_state['compare_schemes_list']) >= 2:
        render_comparison_interface()
    elif len(st.session_state['compare_schemes_list']) == 1:
        st.info(f"👆 Added 1 scheme. Add at least one more to compare.")
        render_add_scheme_interface()
    else:
        st.info("👆 No schemes added yet. Add at least 2 schemes to compare.")
        render_add_scheme_interface()

# ==========================================
# ADD SCHEME INTERFACE
# ==========================================

def render_add_scheme_interface():
    """Render interface to add schemes"""
    
    st.markdown("### ➕ Add Schemes to Compare")
    
    # Category filter
    categories_data = get_scheme_categories()
    categories = ["All Categories"] + sorted(categories_data.get('categories', []))
    selected_category = st.selectbox("Filter by Category:", categories, key="compare_category_filter")
    
    # Search box
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_query = st.text_input(
            "Search by scheme name:",
            placeholder="Enter scheme name or AMC",
            key="compare_search_input"
        )
    
    with col2:
        limit = st.number_input("Max Results", min_value=5, max_value=50, value=20, key="compare_search_limit")
    
    with col3:
        st.write("")
        st.write("")
        search_btn = st.button("🔍 Search", key="compare_search_btn", use_container_width=True)
    
    if search_btn and search_query and len(search_query) >= 2:
        with st.spinner("Searching..."):
            try:
                # Search for schemes
                results = api._make_request(
                    "GET",
                    f"{api.api_v1}/nav/search",
                    params={"q": search_query, "limit": limit},
                    show_error=True
                )
                
                if results:
                    # Filter by category if needed
                    if selected_category != "All Categories":
                        all_nav_data = get_all_nav_data()
                        df_all = pd.DataFrame(all_nav_data)
                        
                        # Get scheme codes matching the category
                        filtered_codes = df_all[
                            df_all['Scheme Category'] == selected_category
                        ]['Scheme Code'].astype(str).tolist()
                        
                        # Filter results
                        results = [r for r in results if str(r['Scheme Code']) in filtered_codes]
                    
                    if results:
                        st.session_state['compare_search_results'] = results
                        st.success(f"✅ Found {len(results)} schemes")
                    else:
                        st.warning(f"No schemes found in category '{selected_category}'")
                else:
                    st.warning("No schemes found")
            
            except Exception as e:
                st.error(f"Search failed: {e}")
    
    # Display search results
    if 'compare_search_results' in st.session_state:
        results = st.session_state['compare_search_results']
        
        st.markdown("---")
        st.markdown("#### 📋 Search Results")
        
        for i, item in enumerate(results):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.text(f"{item['Scheme Name'][:50]}...")
            with col2:
                st.text(f"₹{item['current_nav']:.2f}")
            with col3:
                st.text(item['amc'][:15])
            with col4:
                # Check if already added
                already_added = any(
                    s['scheme_code'] == str(item['Scheme Code'])
                    for s in st.session_state['compare_schemes_list']
                )
                
                if already_added:
                    st.button("✓ Added", key=f"added_{i}", disabled=True, use_container_width=True)
                else:
                    if st.button("➕ Add", key=f"add_{i}", use_container_width=True):
                        st.session_state['compare_schemes_list'].append({
                            'scheme_code': str(item['Scheme Code']),
                            'scheme_name': item['Scheme Name']
                        })
                        st.rerun()

# ==========================================
# COMPARISON INTERFACE
# ==========================================

def render_comparison_interface():
    """Render main comparison view"""
    
    schemes = st.session_state['compare_schemes_list']
    scheme_codes = [s['scheme_code'] for s in schemes]
    
    st.markdown(f"### Comparing {len(schemes)} Schemes")
    
    # Display selected schemes as chips
    cols = st.columns(min(len(schemes) + 1, 6))
    
    for i, s in enumerate(schemes):
        with cols[i % 5]:
            if st.button(f"❌ {s['scheme_name'][:20]}", key=f"remove_{i}", use_container_width=True):
                st.session_state['compare_schemes_list'].pop(i)
                st.rerun()
    
    with cols[len(schemes) % 5 if len(schemes) < 5 else 5]:
        if st.button("➕ Add More", key="add_more_btn", use_container_width=True):
            st.session_state['show_add_form'] = True
    
    # Show add form if requested
    if st.session_state.get('show_add_form'):
        st.markdown("---")
        render_add_scheme_interface()
        if st.button("❌ Close Add Form", key="close_add_form"):
            st.session_state['show_add_form'] = False
            st.rerun()
    
    st.markdown("---")
    
    # Fetch comparison data
    with st.spinner("📊 Fetching comparison data..."):
        try:
            comp_data = api._make_request(
                "POST",
                f"{api.api_v1}/analytics/compare",
                json=scheme_codes,
                show_error=True
            )
            
            if not comp_data:
                st.error("Could not fetch comparison data")
                return
        
        except Exception as e:
            st.error(f"Failed to fetch comparison: {e}")
            return
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Metrics Table",
        "📈 Performance Chart",
        "🕸️ Radar Chart",
        "🔗 Correlation"
    ])
    
    with tab1:
        render_metrics_table(comp_data)
    
    with tab2:
        render_performance_chart(comp_data)
    
    with tab3:
        render_radar_chart(comp_data)
    
    with tab4:
        render_correlation_matrix(comp_data)

# ==========================================
# VISUALIZATION FUNCTIONS
# ==========================================

def render_metrics_table(comp_data: dict):
    """Render comparison metrics table"""
    
    st.markdown("### 📋 Performance Metrics Comparison")
    
    comparison = comp_data.get('comparison', [])
    
    if not comparison:
        st.warning("No comparison data available")
        return
    
    df = pd.DataFrame(comparison)
    
    # Get scheme names
    scheme_names = {}
    for s in st.session_state['compare_schemes_list']:
        scheme_names[s['scheme_code']] = s['scheme_name']
    
    # Add scheme names
    if 'scheme_code' in df.columns:
        df['Scheme Name'] = df['scheme_code'].map(lambda x: scheme_names.get(x, x)[:40])
    
    # Select and reorder columns
    display_cols = [
        'Scheme Name', 'current_nav', 'cagr', 'annualized_return',
        'sharpe_ratio', 'sortino_ratio', 'volatility', 'max_drawdown'
    ]
    
    display_cols = [c for c in display_cols if c in df.columns]
    df_display = df[display_cols].copy()
    
    # Format columns
    if 'current_nav' in df_display.columns:
        df_display['current_nav'] = df_display['current_nav'].apply(lambda x: f"₹{x:.2f}" if pd.notna(x) else "N/A")
    
    for col in ['cagr', 'annualized_return', 'volatility', 'max_drawdown']:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A")
    
    for col in ['sharpe_ratio', 'sortino_ratio']:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(lambda x: f"{x:.3f}" if pd.notna(x) else "N/A")
    
    # Rename columns
    df_display.columns = [
        'Scheme', 'Current NAV', 'CAGR', 'Ann. Return',
        'Sharpe', 'Sortino', 'Volatility', 'Max DD'
    ][:len(df_display.columns)]
    
    # Display table
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # Highlight best performers
    st.markdown("---")
    st.markdown("### 🏆 Best Performers")
    
    best_schemes = comp_data.get('best_schemes', {})
    
    if best_schemes:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'best_by_sharpe' in best_schemes:
                best = best_schemes['best_by_sharpe']
                scheme_name = scheme_names.get(best['scheme_code'], best['scheme_code'])
                st.success(f"**Best Sharpe Ratio**\n\n{scheme_name[:30]}\n\nSharpe: {best['sharpe_ratio']:.3f}")
        
        with col2:
            if 'best_by_return' in best_schemes:
                best = best_schemes['best_by_return']
                scheme_name = scheme_names.get(best['scheme_code'], best['scheme_code'])
                st.success(f"**Best Return**\n\n{scheme_name[:30]}\n\nCAGR: {best['cagr']*100:.2f}%")
        
        with col3:
            if 'lowest_volatility' in best_schemes:
                best = best_schemes['lowest_volatility']
                scheme_name = scheme_names.get(best['scheme_code'], best['scheme_code'])
                st.success(f"**Lowest Volatility**\n\n{scheme_name[:30]}\n\nVol: {best['volatility']*100:.2f}%")

def render_performance_chart(comp_data: dict):
    """Render normalized performance chart"""
    
    st.markdown("### 📈 Normalized Performance (Rebased to 100)")
    
    normalized_perf = comp_data.get('normalized_performance', {})
    
    if not normalized_perf:
        st.warning("No performance data available")
        return
    
    # Get scheme names
    scheme_names = {}
    for s in st.session_state['compare_schemes_list']:
        scheme_names[s['scheme_code']] = s['scheme_name']
    
    # Create chart
    fig = go.Figure()
    
    colors = px.colors.qualitative.Plotly
    
    for i, (code, data) in enumerate(normalized_perf.items()):
        if not data:
            continue
        
        df = pd.DataFrame(data)
        
        if 'date' not in df.columns or 'normalized_nav' not in df.columns:
            continue
        
        fig.add_trace(go.Scatter(
            x=pd.to_datetime(df['date']),
            y=df['normalized_nav'],
            mode='lines',
            name=scheme_names.get(code, code)[:30],
            line=dict(width=2, color=colors[i % len(colors)]),
            hovertemplate='<b>%{fullData.name}</b><br>Date: %{x}<br>Value: %{y:.2f}<extra></extra>'
        ))
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Normalized Value (Base = 100)",
        hovermode="x unified",
        height=600,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=0.01
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Performance summary
    st.markdown("---")
    st.info("""
    **📌 How to Read:**
    - All schemes start at 100 for easy comparison
    - Higher line = better performance
    - Steeper slope = faster growth
    - Line above 100 = positive returns
    """)

def render_radar_chart(comp_data: dict):
    """Render multi-metric radar chart"""
    
    st.markdown("### 🕸️ Multi-Metric Radar Chart")
    
    comparison = comp_data.get('comparison', [])
    
    if not comparison:
        st.warning("No comparison data available")
        return
    
    df = pd.DataFrame(comparison)
    
    # Get scheme names
    scheme_names = {}
    for s in st.session_state['compare_schemes_list']:
        scheme_names[s['scheme_code']] = s['scheme_name']
    
    # Metrics to include
    metrics = ['cagr', 'sharpe_ratio', 'sortino_ratio', 'volatility', 'max_drawdown']
    
    # Check which metrics are available
    available_metrics = [m for m in metrics if m in df.columns]
    
    if not available_metrics:
        st.warning("No metrics available for radar chart")
        return
    
    # Normalize metrics (0-100 scale)
    df_norm = df.copy()
    
    for metric in available_metrics:
        values = df[metric].dropna()
        
        if len(values) == 0:
            continue
        
        min_val = values.min()
        max_val = values.max()
        range_val = max_val - min_val
        
        if range_val == 0:
            df_norm[f'{metric}_norm'] = 50
        else:
            # For volatility and max_drawdown, invert (lower is better)
            if metric in ['volatility', 'max_drawdown']:
                df_norm[f'{metric}_norm'] = 100 - ((df[metric] - min_val) / range_val * 100)
            else:
                df_norm[f'{metric}_norm'] = (df[metric] - min_val) / range_val * 100
    
    # Create radar chart
    fig = go.Figure()
    
    colors = px.colors.qualitative.Plotly
    
    for i, row in df_norm.iterrows():
        scheme_code = row.get('scheme_code', '')
        scheme_name = scheme_names.get(scheme_code, scheme_code)[:25]
        
        # Get normalized values
        values = [row.get(f'{m}_norm', 0) for m in available_metrics]
        labels = [m.replace('_', ' ').title() for m in available_metrics]
        
        # Close the polygon
        values.append(values[0])
        labels.append(labels[0])
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=labels,
            fill='toself',
            name=scheme_name,
            line=dict(color=colors[i % len(colors)], width=2),
            hovertemplate='<b>%{fullData.name}</b><br>%{theta}<br>Score: %{r:.1f}<extra></extra>'
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True,
        height=600,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="right",
            x=1.3
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.info("""
    **📌 How to Read:**
    - All metrics normalized to 0-100 scale
    - Larger area = better overall performance
    - Volatility & Max Drawdown are inverted (lower is better = higher score)
    - Compare shapes to see relative strengths
    """)

def render_correlation_matrix(comp_data: dict):
    """Render correlation heatmap"""
    
    st.markdown("### 🔗 Correlation Matrix")
    
    corr_matrix_dict = comp_data.get('correlation_matrix', {})
    
    if not corr_matrix_dict:
        st.warning("No correlation data available")
        return
    
    # Convert dict to DataFrame
    df_corr = pd.DataFrame(corr_matrix_dict)
    
    # Get scheme names
    scheme_names = {}
    for s in st.session_state['compare_schemes_list']:
        scheme_names[s['scheme_code']] = s['scheme_name']
    
    # Rename columns and index
    df_corr.columns = [scheme_names.get(c, c)[:25] for c in df_corr.columns]
    df_corr.index = [scheme_names.get(i, i)[:25] for i in df_corr.index]
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=df_corr.values,
        x=df_corr.columns,
        y=df_corr.index,
        colorscale='RdBu',
        zmid=0,
        text=df_corr.values,
        texttemplate='%{text:.2f}',
        textfont={"size": 12},
        colorbar=dict(title="Correlation"),
        hovertemplate='<b>%{y}</b> vs <b>%{x}</b><br>Correlation: %{z:.3f}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Return Correlation Between Schemes",
        height=600,
        xaxis={'side': 'bottom'},
        yaxis={'side': 'left'}
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Interpretation
    st.markdown("---")
    with st.expander("ℹ️ Understanding Correlation"):
        st.markdown("""
        **Correlation ranges from -1 to +1:**
        
        - **+1.0:** Perfect positive correlation (move together)
        - **+0.7 to +1.0:** Strong positive correlation
        - **+0.3 to +0.7:** Moderate positive correlation
        - **-0.3 to +0.3:** Low/No correlation (good for diversification)
        - **-0.7 to -0.3:** Moderate negative correlation
        - **-1.0 to -0.7:** Strong negative correlation
        - **-1.0:** Perfect negative correlation (move opposite)
        
        **For Portfolio Diversification:**
        - Lower correlation is better (reduces overall risk)
        - Aim for correlation below 0.7 between holdings
        - Negative correlation can provide hedging benefits
        """)
    
    # Diversification score
    st.markdown("---")
    st.markdown("### 📊 Diversification Analysis")
    
    # Calculate average correlation
    mask = np.triu(np.ones_like(df_corr, dtype=bool), k=1)
    corr_values = df_corr.values[mask]
    avg_corr = np.mean(corr_values)
    
    div_score = max(0, min(100, (1 - avg_corr) * 100))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Average Correlation", f"{avg_corr:.3f}")
    
    with col2:
        st.metric("Diversification Score", f"{div_score:.1f}/100")
    
    # Interpretation
    if div_score >= 70:
        st.success("✅ **Excellent Diversification** - Low correlation between schemes")
    elif div_score >= 50:
        st.info("📊 **Good Diversification** - Moderate correlation, can be improved")
    elif div_score >= 30:
        st.warning("⚠️ **Fair Diversification** - High correlation, consider more diverse schemes")
    else:
        st.error("❌ **Poor Diversification** - Very high correlation, schemes move together")
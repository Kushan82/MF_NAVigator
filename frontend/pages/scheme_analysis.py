"""
Scheme Analysis Page - COMPLETE VERSION
Detailed financial and risk analysis with advanced search and visualizations
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from frontend.utils.api_client import APIClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api = APIClient()

# ==========================================
# CACHED DATA FUNCTIONS
# ==========================================

@st.cache_data(ttl=3600)
def get_scheme_categories():
    """Fetch categories from API (cached for 1 hour)"""
    try:
        return api._make_request("GET", f"{api.api_v1}/nav/categories", show_error=False)
    except Exception as e:
        logger.error(f"Failed to get categories: {e}")
        return {"categories": [], "types": []}

@st.cache_data(ttl=3600)
def get_all_nav_data():
    """Fetch all NAV data (cached for 1 hour)"""
    try:
        return api._make_request("GET", f"{api.api_v1}/nav", show_error=False)
    except Exception as e:
        logger.error(f"Failed to get NAV data: {e}")
        return []

# ==========================================
# MAIN RENDER FUNCTION
# ==========================================

def render():
    """Render scheme analysis page"""
    
    st.markdown("# 📊 Scheme Analysis")
    st.markdown("Detailed financial and risk analysis for any mutual fund scheme")
    st.markdown("---")
    
    # Check if scheme was selected from another page
    if st.session_state.get('selected_scheme_code'):
        scheme_code = st.session_state['selected_scheme_code']
        scheme_name = st.session_state.get('selected_scheme_name', scheme_code)
        
        render_scheme_analysis(scheme_code, scheme_name)
        
        # Add button to search for another scheme
        st.markdown("---")
        if st.button("🔍 Search Another Scheme", use_container_width=True):
            st.session_state['selected_scheme_code'] = None
            st.session_state['selected_scheme_name'] = None
            st.rerun()
    else:
        render_scheme_search()

# ==========================================
# SEARCH INTERFACE
# ==========================================

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
        search_query = st.text_input(
            "Search by scheme name, AMC, or code:",
            placeholder="e.g., HDFC Balanced, SBI, 119551",
            key="analysis_quick_search"
        )
    
    with col2:
        st.write("")
        st.write("")
        search_button = st.button("🔍 Search", key="analysis_search_btn", use_container_width=True)
    
    if search_button and search_query and len(search_query) >= 2:
        with st.spinner("Searching..."):
            try:
                results = api._make_request(
                    "GET",
                    f"{api.api_v1}/nav/search",
                    params={"q": search_query, "limit": 20},
                    show_error=True
                )
                
                if results and len(results) > 0:
                    st.session_state['analysis_search_results'] = results
                    st.success(f"✅ Found {len(results)} schemes")
                else:
                    st.warning("No schemes found.")
            except Exception as e:
                st.error(f"Search failed: {e}")
    
    # Display search results
    if 'analysis_search_results' in st.session_state:
        results = st.session_state['analysis_search_results']
        
        st.markdown("---")
        st.markdown("#### 📋 Select a Scheme")
        
        # Create selection
        selected_idx = st.selectbox(
            "Choose scheme to analyze:",
            options=range(len(results)),
            format_func=lambda x: f"{results[x]['Scheme Name'][:60]} ({results[x]['Scheme Code']})",
            key="analysis_scheme_select"
        )
        
        if selected_idx is not None:
            selected = results[selected_idx]
            
            # Show scheme preview
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Code", selected['Scheme Code'])
            with col2:
                st.metric("NAV", f"₹{selected['current_nav']:.2f}")
            with col3:
                st.metric("AMC", selected['amc'][:20])
            with col4:
                st.metric("Category", selected.get('category', 'N/A')[:15])
            
            st.markdown("---")
            
            if st.button("📊 Analyze This Scheme", type="primary", use_container_width=True):
                st.session_state['selected_scheme_code'] = selected['Scheme Code']
                st.session_state['selected_scheme_name'] = selected['Scheme Name']
                st.session_state.pop('analysis_search_results', None)
                st.rerun()

def render_advanced_filters():
    """Render advanced filters interface"""
    
    st.markdown("#### Filter by Category & AMC")
    
    # Get categories
    categories_data = get_scheme_categories()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        categories = ["All"] + sorted(categories_data.get('categories', []))
        selected_category = st.selectbox(
            "Category",
            options=categories,
            key="analysis_filter_category"
        )
    
    with col2:
        amcs = [
            'All', 'HDFC', 'SBI', 'ICICI Prudential', 'Axis', 'Kotak',
            'Aditya Birla Sun Life', 'UTI', 'Nippon India', 'DSP',
            'Franklin Templeton', 'Mirae Asset', 'Tata', 'HSBC', 'L&T'
        ]
        selected_amc = st.selectbox(
            "AMC (Fund House)",
            options=amcs,
            key="analysis_filter_amc"
        )
    
    with col3:
        limit = st.number_input(
            "Max Results",
            min_value=10,
            max_value=200,
            value=50,
            key="analysis_filter_limit"
        )
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("🔍 Apply Filters", use_container_width=True, type="primary", key="analysis_apply_filters"):
            apply_filters(selected_category, selected_amc, limit)
    
    with col2:
        if st.button("🔄 Reset", use_container_width=True, key="analysis_reset_filters"):
            if 'analysis_filtered_results' in st.session_state:
                del st.session_state['analysis_filtered_results']
            st.rerun()
    
    st.markdown("---")
    
    # Display filtered results
    if 'analysis_filtered_results' in st.session_state:
        results = st.session_state['analysis_filtered_results']
        
        st.success(f"✅ Found {len(results)} schemes")
        
        # Display as table
        df_display = pd.DataFrame([
            {
                'Scheme Name': r['Scheme Name'][:50],
                'Code': r['Scheme Code'],
                'AMC': r['amc'][:25],
                'Category': r.get('category', 'N/A')[:25],
                'NAV': f"₹{r['current_nav']:.2f}"
            }
            for r in results
        ])
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Selection
        st.markdown("---")
        selected_idx = st.selectbox(
            "Choose scheme to analyze:",
            options=range(len(results)),
            format_func=lambda x: f"{results[x]['Scheme Name'][:60]} ({results[x]['Scheme Code']})",
            key="analysis_filtered_select"
        )
        
        if selected_idx is not None and st.button("📊 Analyze", type="primary"):
            selected = results[selected_idx]
            st.session_state['selected_scheme_code'] = selected['Scheme Code']
            st.session_state['selected_scheme_name'] = selected['Scheme Name']
            st.session_state.pop('analysis_filtered_results', None)
            st.rerun()
    else:
        st.info("💡 **Select filters and click 'Apply Filters' to see results**")

def apply_filters(category: str, amc: str, limit: int):
    """Apply filters and store results"""
    
    with st.spinner("🔍 Applying filters..."):
        try:
            # Get all NAV data
            all_nav = get_all_nav_data()
            
            if not all_nav:
                st.error("Could not load scheme data")
                return
            
            df = pd.DataFrame(all_nav)
            
            # Apply category filter
            if category != 'All':
                df = df[df['Scheme Category'] == category]
            
            # Apply AMC filter
            if amc != 'All':
                df = df[df['AMC'].str.contains(amc, case=False, na=False)]
            
            # Limit results
            df = df.head(limit)
            
            if len(df) == 0:
                st.warning("❌ No schemes match your filter combination")
                return
            
            # Convert to list of dicts
            results = []
            for _, row in df.iterrows():
                results.append({
                    'Scheme Code': str(row['Scheme Code']),
                    'Scheme Name': row['Scheme Name'],
                    'current_nav': float(row['NAV']),
                    'nav_date': str(row['Date']),
                    'amc': row['AMC'],
                    'category': row.get('Scheme Category', 'N/A')
                })
            
            st.session_state['analysis_filtered_results'] = results
            st.rerun()
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# ==========================================
# ANALYSIS INTERFACE
# ==========================================

def render_scheme_analysis(scheme_code: str, scheme_name: str = None):
    """Render the main analysis for the selected scheme"""
    
    # Header
    st.markdown(f"## 📊 {scheme_name or scheme_code}")
    st.markdown(f"**Scheme Code:** {scheme_code}")
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Overview",
        "📈 Financial Metrics",
        "⚠️ Risk Metrics",
        "📊 Historical Data",
        "📉 Performance Charts"
    ])
    
    with tab1:
        render_overview(scheme_code)
    
    with tab2:
        render_financial_metrics(scheme_code)
    
    with tab3:
        render_risk_metrics(scheme_code)
    
    with tab4:
        render_historical_data(scheme_code)
    
    with tab5:
        render_performance_charts(scheme_code)

def render_overview(scheme_code: str):
    """Render scheme overview section"""
    
    st.markdown("### 📋 Scheme Details")
    
    try:
        # Get scheme details
        details = api._make_request(
            "GET",
            f"{api.api_v1}/schemes/{scheme_code}",
            show_error=True
        )
        
        if not details:
            st.error("Could not load scheme details")
            return
        
        # Display basic info
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Current NAV", f"₹{details['current_nav']:.2f}")
        with col2:
            st.metric("As of Date", pd.to_datetime(details['nav_date']).strftime('%d-%b-%Y'))
        with col3:
            st.metric("Category", details.get('category', 'N/A'))
        with col4:
            st.metric("Type", details.get('scheme_type', 'N/A'))
        
        st.markdown("---")
        
        # Additional details
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"**AMC:** {details['amc']}")
        with col2:
            st.markdown(f"**ISIN (Div):** {details.get('isin_div', 'N/A')}")
        with col3:
            st.markdown(f"**ISIN (Growth):** {details.get('isin_growth', 'N/A')}")
        
    except Exception as e:
        st.error(f"Error loading overview: {e}")

def render_financial_metrics(scheme_code: str):
    """Render financial metrics section"""
    
    st.markdown("### 📈 Financial Performance Metrics")
    
    try:
        # Get comprehensive metrics
        with st.spinner("Calculating metrics..."):
            metrics = api._make_request(
                "GET",
                f"{api.api_v1}/analytics/comprehensive/{scheme_code}",
                show_error=True
            )
        
        if not metrics:
            st.error("Could not calculate metrics")
            return
        
        fin_metrics = metrics.get('financial_metrics', {})
        
        # Display key metrics
        st.markdown("#### 📊 Returns")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cagr = fin_metrics.get('cagr')
            if cagr is not None:
                st.metric("CAGR", f"{cagr*100:.2f}%")
            else:
                st.metric("CAGR", "N/A")
        
        with col2:
            ann_ret = fin_metrics.get('annualized_return', 0)
            st.metric("Annualized Return", f"{ann_ret*100:.2f}%")
        
        with col3:
            sharpe = fin_metrics.get('sharpe_ratio')
            if sharpe is not None:
                st.metric("Sharpe Ratio", f"{sharpe:.3f}")
            else:
                st.metric("Sharpe Ratio", "N/A")
        
        with col4:
            sortino = fin_metrics.get('sortino_ratio')
            if sortino is not None:
                st.metric("Sortino Ratio", f"{sortino:.3f}")
            else:
                st.metric("Sortino Ratio", "N/A")
        
        # Absolute returns
        abs_returns = fin_metrics.get('absolute_returns', {})
        if abs_returns:
            st.markdown("---")
            st.markdown("#### 📅 Absolute Returns")
            
            periods = ['1Y', '3Y', '5Y']
            cols = st.columns(len(periods))
            
            for i, period in enumerate(periods):
                with cols[i]:
                    ret_val = abs_returns.get(period)
                    if ret_val is not None and not pd.isna(ret_val):
                        st.metric(f"{period} Return", f"{ret_val:.2f}%")
                    else:
                        st.metric(f"{period} Return", "N/A")
        
        # Interpretation
        st.markdown("---")
        with st.expander("ℹ️ Understanding Financial Metrics"):
            st.markdown("""
            **CAGR (Compound Annual Growth Rate):** Average annual growth rate over time
            
            **Sharpe Ratio:** Risk-adjusted return (higher is better)
            - Above 1: Good
            - Above 2: Very good
            - Above 3: Excellent
            
            **Sortino Ratio:** Similar to Sharpe but only considers downside risk
            
            **Annualized Return:** Average yearly return
            """)
    
    except Exception as e:
        st.error(f"Error loading financial metrics: {e}")

def render_risk_metrics(scheme_code: str):
    """Render risk metrics section"""
    
    st.markdown("### ⚠️ Risk Assessment")
    
    try:
        with st.spinner("Calculating risk metrics..."):
            metrics = api._make_request(
                "GET",
                f"{api.api_v1}/analytics/comprehensive/{scheme_code}",
                show_error=True
            )
        
        if not metrics:
            st.error("Could not calculate risk metrics")
            return
        
        risk_metrics = metrics.get('risk_metrics', {})
        
        # Display risk metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            vol = risk_metrics.get('volatility', 0)
            st.metric("Volatility", f"{vol*100:.2f}%")
        
        with col2:
            dd = risk_metrics.get('max_drawdown', 0)
            st.metric("Max Drawdown", f"{abs(dd)*100:.2f}%")
        
        with col3:
            var = risk_metrics.get('var_95', 0)
            st.metric("VaR (95%)", f"{var*100:.2f}%")
        
        with col4:
            calmar = risk_metrics.get('calmar_ratio')
            if calmar is not None:
                st.metric("Calmar Ratio", f"{calmar:.3f}")
            else:
                st.metric("Calmar Ratio", "N/A")
        
        st.markdown("---")
        
        # Additional risk metrics table
        st.markdown("#### 📋 Detailed Risk Metrics")
        
        risk_data = [
            ["Volatility (Std Dev)", f"{risk_metrics.get('volatility', 0)*100:.2f}%"],
            ["Downside Deviation", f"{risk_metrics.get('downside_deviation', 0)*100:.2f}%"],
            ["Maximum Drawdown", f"{abs(risk_metrics.get('max_drawdown', 0))*100:.2f}%"],
            ["Value at Risk (95%)", f"{risk_metrics.get('var_95', 0)*100:.2f}%"],
            ["CVaR (95%)", f"{risk_metrics.get('cvar_95', 0)*100:.2f}%"],
            ["Ulcer Index", f"{risk_metrics.get('ulcer_index', 0):.4f}"]
        ]
        
        df_risk = pd.DataFrame(risk_data, columns=["Metric", "Value"])
        st.dataframe(df_risk, use_container_width=True, hide_index=True)
        
        # Risk interpretation
        st.markdown("---")
        with st.expander("ℹ️ Understanding Risk Metrics"):
            st.markdown("""
            **Volatility:** Measure of price fluctuation (lower is less risky)
            
            **Max Drawdown:** Largest peak-to-trough decline
            
            **VaR (Value at Risk):** Expected loss in worst 5% of scenarios
            
            **CVaR (Conditional VaR):** Average loss in worst 5% of scenarios
            
            **Calmar Ratio:** Return relative to max drawdown (higher is better)
            
            **Downside Deviation:** Volatility of negative returns only
            """)
    
    except Exception as e:
        st.error(f"Error loading risk metrics: {e}")

def render_historical_data(scheme_code: str):
    """Render historical NAV data section - FIXED"""
    
    st.markdown("### 📊 Historical NAV Data")
    
    try:
        with st.spinner("Fetching historical data..."):
            # FIX: Use correct endpoint path
            history = api._make_request(
                "GET",
                f"{api.api_v1}/schemes/{scheme_code}/history",
                params={"days": 3650},  # Get up to 10 years
                show_error=True
            )
        
        # FIX: Better null checking
        if not history or not isinstance(history, list):
            st.warning("No historical data available for this scheme")
            return
        
        df_hist = pd.DataFrame(history)
        
        # Validate required columns
        if 'date' not in df_hist.columns or 'nav' not in df_hist.columns:
            st.error("Invalid data format received")
            return
        
        df_hist['date'] = pd.to_datetime(df_hist['date'])
        df_hist = df_hist.sort_values('date', ascending=False)
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Records", f"{len(df_hist):,}")
        with col2:
            st.metric("Latest NAV", f"₹{df_hist['nav'].iloc[0]:.2f}")
        with col3:
            st.metric("Highest NAV", f"₹{df_hist['nav'].max():.2f}")
        with col4:
            st.metric("Lowest NAV", f"₹{df_hist['nav'].min():.2f}")
        
        st.markdown("---")
        
        # Data table with filters
        st.markdown("#### 📋 NAV Records")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            show_last = st.selectbox(
                "Show last:",
                options=[30, 90, 180, 365, len(df_hist)],
                format_func=lambda x: f"{x} days" if x < len(df_hist) else "All records",
                key="hist_filter"
            )
        
        display_df = df_hist.head(show_last).copy()
        display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
        display_df['nav'] = display_df['nav'].round(4)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=400
        )
        
        # Download button
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"{scheme_code}_history.csv",
            mime="text/csv",
            key="hist_download"
        )
    
    except Exception as e:
        st.error(f"Error loading historical data: {e}")
        logger.error(f"Historical data error: {e}", exc_info=True)

def render_performance_charts(scheme_code: str):
    """Render performance visualization charts - FIXED"""
    
    st.markdown("### 📉 Performance Visualizations")
    
    try:
        with st.spinner("Generating charts..."):
            # FIX: Use correct endpoint
            history = api._make_request(
                "GET",
                f"{api.api_v1}/schemes/{scheme_code}/history",
                params={"days": 1825},  # 5 years
                show_error=True
            )
        
        # FIX: Comprehensive validation
        if not history or not isinstance(history, list):
            st.warning("No data available for charts")
            return
        
        df_hist = pd.DataFrame(history)
        
        if df_hist.empty or 'date' not in df_hist.columns or 'nav' not in df_hist.columns:
            st.warning("Invalid data format for charts")
            return
        
        df_hist['date'] = pd.to_datetime(df_hist['date'])
        df_hist = df_hist.sort_values('date')
        
        # 1. NAV Timeline Chart
        st.markdown("#### 📈 NAV Timeline")
        
        fig1 = go.Figure()
        
        fig1.add_trace(go.Scatter(
            x=df_hist['date'],
            y=df_hist['nav'],
            mode='lines',
            name='NAV',
            line=dict(color='#1f77b4', width=2),
            hovertemplate='<b>Date:</b> %{x}<br><b>NAV:</b> ₹%{y:.4f}<extra></extra>'
        ))
        
        fig1.update_layout(
            title="NAV Over Time",
            xaxis_title="Date",
            yaxis_title="NAV (₹)",
            height=500,
            hovermode='x unified',
            showlegend=False
        )
        
        st.plotly_chart(fig1, use_container_width=True)
        
        # 2. Returns Distribution
        st.markdown("---")
        st.markdown("#### 📊 Daily Returns Distribution")
        
        df_hist['daily_return'] = df_hist['nav'].pct_change() * 100
        df_hist = df_hist.dropna()
        
        fig2 = go.Figure()
        
        fig2.add_trace(go.Histogram(
            x=df_hist['daily_return'],
            nbinsx=50,
            name='Daily Returns',
            marker_color='#2ca02c',
            hovertemplate='<b>Return Range:</b> %{x:.2f}%<br><b>Frequency:</b> %{y}<extra></extra>'
        ))
        
        fig2.update_layout(
            title="Distribution of Daily Returns",
            xaxis_title="Daily Return (%)",
            yaxis_title="Frequency",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        
        # 3. Rolling Statistics
        st.markdown("---")
        st.markdown("#### 📉 Rolling Statistics (30-Day Window)")
        
        df_hist['rolling_mean'] = df_hist['nav'].rolling(window=30).mean()
        df_hist['rolling_std'] = df_hist['nav'].rolling(window=30).std()
        
        fig3 = make_subplots(
            rows=2, cols=1,
            subplot_titles=('30-Day Rolling Mean', '30-Day Rolling Volatility'),
            vertical_spacing=0.15
        )
        
        fig3.add_trace(
            go.Scatter(
                x=df_hist['date'],
                y=df_hist['rolling_mean'],
                mode='lines',
                name='Rolling Mean',
                line=dict(color='#ff7f0e', width=2)
            ),
            row=1, col=1
        )
        
        fig3.add_trace(
            go.Scatter(
                x=df_hist['date'],
                y=df_hist['rolling_std'],
                mode='lines',
                name='Rolling Std',
                line=dict(color='#d62728', width=2),
                fill='tozeroy'
            ),
            row=2, col=1
        )
        
        fig3.update_xaxes(title_text="Date", row=2, col=1)
        fig3.update_yaxes(title_text="NAV (₹)", row=1, col=1)
        fig3.update_yaxes(title_text="Std Dev", row=2, col=1)
        
        fig3.update_layout(height=600, showlegend=False)
        
        st.plotly_chart(fig3, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error generating charts: {e}")
        logger.error(f"Chart generation error: {e}", exc_info=True)

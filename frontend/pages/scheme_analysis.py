"""
Scheme Analysis Page - Detailed metrics with advanced search
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from frontend.utils.api_client import APIClient

api = APIClient()

def render():
    """Render scheme analysis page"""
    
    st.markdown("# 📊 Scheme Analysis")
    st.markdown("Detailed financial and risk analysis for any mutual fund scheme")
    st.markdown("---")
    
    # Check if scheme was selected from another page
    if st.session_state.get('selected_scheme_code'):
        render_scheme_analysis(st.session_state['selected_scheme_code'])
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
        search_query = st.text_input(
            "Search by scheme name, AMC, or code",
            placeholder="e.g., HDFC Balanced, SBI Bluechip, 119551",
            key="analysis_quick_search"
        )
    
    with col2:
        limit = st.number_input("Results", min_value=5, max_value=100, value=20, key="analysis_quick_limit")
    
    if search_query and len(search_query) >= 2:
        with st.spinner("🔍 Searching..."):
            results = api.search_schemes(search_query, limit)
            
            if results and results['total_results'] > 0:
                display_search_results(results)
            else:
                st.warning("❌ No schemes found")


def render_advanced_filters():
    """Render advanced filter interface - FIXED CATEGORIES"""
    
    st.markdown("#### Filter by Category & AMC")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # FIXED: Match actual backend categories
        categories = [
            'All',
            'Debt',
            'Hybrid',
            'Other'  # This includes Equity schemes
        ]
        
        selected_category = st.selectbox(
            "Category",
            options=categories,
            key="filter_category_select",
            help="Other = Equity and specialized schemes"
        )
    
    with col2:
        # AMC filter (unchanged)
        amcs = [
            'All',
            'HDFC',
            'SBI',
            'ICICI Prudential',
            'Axis',
            'Kotak',
            'Aditya Birla Sun Life',
            'UTI',
            'Nippon India',
            'DSP',
            'Franklin Templeton',
            'Mirae Asset',
            'Tata',
            'HSBC',
            'L&T',
            'Invesco',
            'Sundaram',
            'BOI',
            'Baroda BNP Paribas',
            'Canara Robeco',
            'Edelweiss',
            'IDBI',
            'IDFC',
            'JM Financial',
            'LIC',
            'Mahindra Manulife',
            'Motilal Oswal',
            'Parag Parikh',
            'PGIM India',
            'Quantum',
            'Quant',
            'Shriram',
            'Union'
        ]
        
        selected_amc = st.selectbox(
            "AMC (Fund House)",
            options=amcs,
            key="filter_amc_select"
        )
    
    with col3:
        limit = st.number_input("Max Results", min_value=10, max_value=100, value=50, key="filter_limit")
    
    # Info about categories
    if selected_category == 'Other':
        st.info("💡 **'Other'** category includes Equity schemes (Large Cap, Mid Cap, Small Cap, etc.)")
    
    # Apply filters button
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("🔍 Apply Filters", use_container_width=True, type="primary", key="apply_filters_btn"):
            apply_filters(selected_category, selected_amc, limit)
    
    with col2:
        if st.button("🔄 Reset Filters", use_container_width=True, key="reset_filters_btn"):
            st.session_state['filter_category'] = 'All'
            st.session_state['filter_amc'] = 'All'
            if 'filtered_results' in st.session_state:
                del st.session_state['filtered_results']
            if 'analysis_filtered_results' in st.session_state:
                del st.session_state['analysis_filtered_results']
            st.rerun()
    
    # Display filtered results
    if 'filtered_results' in st.session_state:
        display_search_results(st.session_state['filtered_results'])
    elif 'analysis_filtered_results' in st.session_state:
        display_search_results(st.session_state['analysis_filtered_results'])


def apply_filters(category: str, amc: str, limit: int):
    """Apply filters - FIXED to match backend data structure"""
    
    with st.spinner("🔍 Applying filters..."):
        try:
            # Fetch initial results
            if amc != 'All':
                # Search by AMC name
                search_query = amc
            else:
                # Get broad results
                search_query = "Fund"
            
            # Fetch more results to filter from
            results = api.search_schemes(search_query, limit=min(limit * 2, 200))
            
            if not results or results['total_results'] == 0:
                st.warning(f"❌ No schemes found for search: {search_query}")
                return
            
            schemes_list = results['schemes']
            
            # Filter by category (exact match since categories are simple: Debt, Hybrid, Other)
            if category != 'All':
                schemes_list = [
                    s for s in schemes_list 
                    if s.get('category') == category
                ]
            
            # Filter by AMC (case-insensitive contains)
            if amc != 'All':
                schemes_list = [
                    s for s in schemes_list 
                    if amc.lower() in s.get('amc', '').lower()
                ]
            
            # Limit results
            schemes_list = schemes_list[:limit]
            
            # Store results
            filtered_results = {
                'total_results': len(schemes_list),
                'schemes': schemes_list
            }
            
            # Determine which session state key to use
            if 'analysis_filter_category' in st.session_state:
                st.session_state['analysis_filtered_results'] = filtered_results
            else:
                st.session_state['filtered_results'] = filtered_results
            
            # Show results
            if len(schemes_list) > 0:
                st.success(f"✅ Found {len(schemes_list)} schemes")
                
                # Show category breakdown
                category_counts = {}
                for s in schemes_list:
                    cat = s.get('category', 'Unknown')
                    category_counts[cat] = category_counts.get(cat, 0) + 1
                
                st.caption(f"Breakdown: {dict(category_counts)}")
            else:
                st.warning("❌ No schemes match your filters")
                st.info("💡 **Tips:**\n- Try 'All' for Category\n- Try 'All' for AMC\n- Some AMCs may have limited schemes in certain categories")
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

def display_search_results(results: dict):
    """Display search results"""
    
    schemes_list = results['schemes']
    
    if not schemes_list:
        st.warning("No schemes to display")
        return
    
    st.markdown("---")
    st.markdown(f"#### 📊 Select Scheme to Analyze ({len(schemes_list)} results)")
    
    # Display as table
    df = pd.DataFrame([
        {
            'Scheme Name': scheme['scheme_name'][:50],
            'Code': scheme['scheme_code'],
            'AMC': scheme['amc'][:25],
            'Category': str(scheme.get('category', 'N/A'))[:25],
            'NAV': scheme['current_nav'],
            'Date': scheme['nav_date']
        }
        for scheme in schemes_list
    ])
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "NAV": st.column_config.NumberColumn("NAV (₹)", format="%.2f")
        }
    )
    
    st.markdown("---")
    
    # Selection
    selected_idx = st.selectbox(
        "Choose scheme to analyze:",
        options=range(len(schemes_list)),
        format_func=lambda x: f"{schemes_list[x]['scheme_name'][:40]} ({schemes_list[x]['scheme_code']})",
        key="analysis_scheme_select"
    )
    
    if selected_idx is not None:
        selected_scheme = schemes_list[selected_idx]
        
        # Show quick info
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Code", selected_scheme['scheme_code'])
        with col2:
            st.metric("NAV", f"₹{selected_scheme['current_nav']:.2f}")
        with col3:
            st.metric("AMC", selected_scheme['amc'][:20])
        with col4:
            st.metric("Date", selected_scheme['nav_date'])
        
        # Analyze button
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("📊 Analyze This Scheme", use_container_width=True, type="primary", key="analysis_analyze_btn"):
                st.session_state['selected_scheme_code'] = selected_scheme['scheme_code']
                st.session_state['selected_scheme_name'] = selected_scheme['scheme_name']
                st.rerun()
        
        with col2:
            if st.button("❌ Clear Selection", use_container_width=True, key="analysis_clear_btn"):
                if 'analysis_filtered_results' in st.session_state:
                    del st.session_state['analysis_filtered_results']
                st.rerun()


def render_scheme_analysis(scheme_code: str):
    """Render detailed scheme analysis"""
    
    with st.spinner("📊 Fetching comprehensive metrics..."):
        try:
            data = api.get_comprehensive_metrics(scheme_code)
            
            if not data:
                st.error("❌ Unable to fetch scheme data")
                if st.button("🔙 Search Another Scheme"):
                    st.session_state['selected_scheme_code'] = None
                    st.rerun()
                return
            
            # Header with change scheme button
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"## {data['scheme_name']}")
                st.markdown(f"**Scheme Code:** {data['scheme_code']}")
            
            with col2:
                if st.button("🔄 Change Scheme", use_container_width=True):
                    st.session_state['selected_scheme_code'] = None
                    st.session_state['selected_scheme_name'] = None
                    st.rerun()
            
            st.markdown("---")
            
            # Key metrics
            display_key_metrics(data)
            
            st.markdown("---")
            
            # Detailed tabs
            render_metric_tabs(data)
            
            # Historical data section
            st.markdown("---")
            render_historical_section(scheme_code)
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            if st.button("🔙 Search Another Scheme"):
                st.session_state['selected_scheme_code'] = None
                st.rerun()


def display_key_metrics(data: dict):
    """Display key metrics row"""
    
    fm = data['financial_metrics']
    rm = data['risk_metrics']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Current NAV", f"₹{fm['current_nav']:.2f}")
    
    with col2:
        cagr = fm.get('cagr')
        if cagr and not pd.isna(cagr):
            st.metric("CAGR", f"{cagr*100:.2f}%")
        else:
            st.metric("CAGR", "N/A")
    
    with col3:
        sharpe = fm.get('sharpe_ratio')
        if sharpe and not pd.isna(sharpe):
            st.metric("Sharpe Ratio", f"{sharpe:.3f}")
        else:
            st.metric("Sharpe Ratio", "N/A")
    
    with col4:
        st.metric("Volatility", f"{rm['volatility']*100:.2f}%")


def render_metric_tabs(data: dict):
    """Render detailed metric tabs"""
    
    tab1, tab2, tab3 = st.tabs(["📈 Returns", "⚠️ Risk", "📊 All Metrics"])
    
    with tab1:
        render_returns_tab(data['financial_metrics'])
    
    with tab2:
        render_risk_tab(data['risk_metrics'])
    
    with tab3:
        render_all_metrics_tab(data)


def render_returns_tab(fm: dict):
    """Render returns tab"""
    
    st.markdown("### 📈 Returns Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Short-term Returns")
        abs_ret = fm.get('absolute_returns', {})
        
        for period in ['1D', '1W', '1M', '3M']:
            if abs_ret.get(period) and not pd.isna(abs_ret[period]):
                st.metric(
                    period.replace('D', ' Day').replace('W', ' Week').replace('M', ' Month'),
                    f"{abs_ret[period]:.2f}%"
                )
    
    with col2:
        st.markdown("#### Long-term Returns")
        
        for period in ['6M', '1Y', '3Y', '5Y']:
            if abs_ret.get(period) and not pd.isna(abs_ret[period]):
                st.metric(
                    period.replace('M', ' Months').replace('Y', ' Year').replace('3', '3 ').replace('5', '5 '),
                    f"{abs_ret[period]:.2f}%"
                )
    
    # Returns chart
    if abs_ret:
        st.markdown("---")
        render_returns_chart(abs_ret)


def render_risk_tab(rm: dict):
    """Render risk tab"""
    
    st.markdown("### ⚠️ Risk Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Volatility (Annual)", f"{rm['volatility']*100:.2f}%")
        st.metric("Downside Deviation", f"{rm['downside_deviation']*100:.2f}%")
    
    with col2:
        st.metric("Maximum Drawdown", f"{abs(rm['max_drawdown'])*100:.2f}%")
        st.metric("Ulcer Index", f"{rm['ulcer_index']:.4f}")
    
    with col3:
        st.metric("VaR (95%)", f"{rm['var_95']*100:.2f}%")
        st.metric("CVaR (95%)", f"{rm['cvar_95']*100:.2f}%")


def render_all_metrics_tab(data: dict):
    """Render all metrics"""
    
    st.markdown("### 📊 Complete Metrics Summary")
    
    fm = data['financial_metrics']
    rm = data['risk_metrics']
    
    metrics_data = []
    
    # Financial
    metrics_data.append(["📊 Financial Metrics", ""])
    metrics_data.append(["Current NAV", f"₹{fm['current_nav']:.2f}"])
    
    if fm.get('cagr') and not pd.isna(fm['cagr']):
        metrics_data.append(["CAGR", f"{fm['cagr']*100:.2f}%"])
    
    metrics_data.append(["Annualized Return", f"{fm['annualized_return']*100:.2f}%"])
    
    if fm.get('sharpe_ratio') and not pd.isna(fm['sharpe_ratio']):
        metrics_data.append(["Sharpe Ratio", f"{fm['sharpe_ratio']:.3f}"])
    
    # Risk
    metrics_data.append(["", ""])
    metrics_data.append(["⚠️ Risk Metrics", ""])
    metrics_data.append(["Volatility", f"{rm['volatility']*100:.2f}%"])
    metrics_data.append(["Max Drawdown", f"{abs(rm['max_drawdown'])*100:.2f}%"])
    metrics_data.append(["VaR (95%)", f"{rm['var_95']*100:.2f}%"])
    
    df_summary = pd.DataFrame(metrics_data, columns=["Metric", "Value"])
    
    st.dataframe(df_summary, use_container_width=True, hide_index=True)
    
    # Download
    csv = df_summary.to_csv(index=False)
    st.download_button(
        label="📥 Download Metrics CSV",
        data=csv,
        file_name=f"{data['scheme_code']}_metrics.csv",
        mime="text/csv"
    )


def render_returns_chart(abs_returns: dict):
    """Render returns bar chart"""
    
    returns_data = {k: v for k, v in abs_returns.items() if v is not None and not pd.isna(v)}
    
    if not returns_data:
        return
    
    fig = go.Figure(data=[
        go.Bar(
            x=list(returns_data.keys()),
            y=list(returns_data.values()),
            marker_color=['green' if v >= 0 else 'red' for v in returns_data.values()]
        )
    ])
    
    fig.update_layout(
        title="Returns Across Time Periods",
        xaxis_title="Period",
        yaxis_title="Return (%)",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_historical_section(scheme_code: str):
    """Render historical data section"""
    
    st.markdown("### 📈 Historical NAV Data")
    
    with st.expander("View Historical Data"):
        days = st.slider("Select period (days)", min_value=30, max_value=365, value=90)
        
        if st.button("Fetch Historical Data"):
            with st.spinner("Fetching data..."):
                hist_data = api.get_historical_data(scheme_code, limit=days)
                
                if hist_data and hist_data.get('data'):
                    df_hist = pd.DataFrame(hist_data['data'])
                    
                    # Plot
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df_hist['date'],
                        y=df_hist['nav'],
                        mode='lines',
                        name='NAV'
                    ))
                    
                    fig.update_layout(
                        title=f"NAV History - Last {days} days",
                        xaxis_title="Date",
                        yaxis_title="NAV (₹)",
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Download
                    csv = df_hist.to_csv(index=False)
                    st.download_button(
                        "📥 Download Historical Data",
                        data=csv,
                        file_name=f"{scheme_code}_history.csv",
                        mime="text/csv"
                    )

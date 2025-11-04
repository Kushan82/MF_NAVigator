"""
Scheme Analysis Page - Detailed metrics with advanced search
COMPLETE VERSION with all helper functions
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
    """Render advanced filter interface"""
    
    st.markdown("#### Filter by Category & AMC")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        categories = ['All', 'Debt', 'Hybrid', 'Other']
        selected_category = st.selectbox(
            "Category",
            options=categories,
            key="filter_category_select",
            help="Other = Equity and specialized schemes"
        )
    
    with col2:
        amcs = [
            'All', 'HDFC', 'SBI', 'ICICI Prudential', 'Axis', 'Kotak',
            'Aditya Birla Sun Life', 'UTI', 'Nippon India', 'DSP',
            'Franklin Templeton', 'Mirae Asset', 'Tata', 'HSBC', 'L&T',
            'Invesco', 'Sundaram', 'BOI', 'Baroda BNP Paribas',
            'Canara Robeco', 'Edelweiss', 'IDBI', 'IDFC', 'JM Financial',
            'LIC', 'Mahindra Manulife', 'Motilal Oswal', 'Parag Parikh',
            'PGIM India', 'Quantum', 'Quant', 'Shriram', 'Union'
        ]
        
        selected_amc = st.selectbox(
            "AMC (Fund House)",
            options=amcs,
            key="filter_amc_select"
        )
    
    with col3:
        limit = st.number_input(
            "Max Results",
            min_value=10,
            max_value=200,
            value=50,
            key="filter_limit"
        )
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("🔍 Apply Filters", use_container_width=True, type="primary", key="apply_filters_btn"):
            apply_filters(selected_category, selected_amc, limit)
    
    with col2:
        if st.button("🔄 Reset", use_container_width=True, key="reset_filters_btn"):
            if 'analysis_filtered_results' in st.session_state:
                del st.session_state['analysis_filtered_results']
            st.rerun()
    
    st.markdown("---")
    
    # Display results if available
    if 'analysis_filtered_results' in st.session_state:
        display_search_results(st.session_state['analysis_filtered_results'])
    else:
        st.info("💡 **Select filters and click 'Apply Filters' to see results**")


def apply_filters(category: str, amc: str, limit: int):
    """Apply filters - Returns up to limit results"""
    
    with st.spinner("🔍 Applying filters..."):
        try:
            # Determine search query
            if amc != 'All':
                search_query = amc
            else:
                search_query = "Fund"
            
            # Fetch double the limit to allow filtering
            fetch_limit = min(limit * 3, 200)
            results = api.search_schemes(search_query, limit=fetch_limit)
            
            if not results or results['total_results'] == 0:
                st.warning(f"❌ No schemes found for: {search_query}")
                return
            
            schemes_list = results['schemes']
            
            # Filter by category (exact match)
            if category != 'All':
                schemes_list = [
                    s for s in schemes_list 
                    if s.get('category') == category
                ]
            
            # Filter by AMC (contains, case-insensitive)
            if amc != 'All':
                schemes_list = [
                    s for s in schemes_list 
                    if amc.lower() in s.get('amc', '').lower()
                ]
            
            # Apply limit
            schemes_list = schemes_list[:limit]
            
            if len(schemes_list) == 0:
                st.warning("❌ No schemes match your filter combination")
                return
            
            # Store results
            filtered_results = {
                'total_results': len(schemes_list),
                'schemes': schemes_list
            }
            
            st.session_state['analysis_filtered_results'] = filtered_results
            st.rerun()
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


def display_search_results(results: dict):
    """Display search results with proper table and selection"""
    
    schemes_list = results['schemes']
    
    if not schemes_list:
        st.warning("No schemes to display")
        return
    
    st.markdown("---")
    st.markdown(f"#### 📊 Results ({len(schemes_list)} schemes)")
    
    # View type selector
    view_type = st.radio(
        "View as:",
        options=["📋 Table", "📦 Cards"],
        horizontal=True,
        key=f"view_type_{len(schemes_list)}"
    )
    
    if view_type == "📋 Table":
        render_table_view(schemes_list)
    else:
        render_cards_view(schemes_list)


def render_table_view(schemes_list: list):
    """Render schemes as a table with selection"""
    
    # Create DataFrame for display
    df = pd.DataFrame([
        {
            'Scheme Name': scheme['scheme_name'][:50],
            'Code': scheme['scheme_code'],
            'AMC': scheme['amc'][:25],
            'Category': str(scheme.get('category', 'N/A'))[:25],
            'NAV': f"₹{scheme['current_nav']:.2f}",
            'Date': scheme['nav_date']
        }
        for scheme in schemes_list
    ])
    
    # Display table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("---")
    st.markdown("#### 🎯 Select a Scheme")
    
    # Selection dropdown
    selected_idx = st.selectbox(
        "Choose scheme:",
        options=range(len(schemes_list)),
        format_func=lambda x: f"{schemes_list[x]['scheme_name'][:40]} ({schemes_list[x]['scheme_code']})",
        key=f"table_select_{len(schemes_list)}"
    )
    
    # Display selected scheme details
    if selected_idx is not None:
        display_scheme_actions(schemes_list[selected_idx])


def render_cards_view(schemes_list: list):
    """Render schemes as expandable cards with pagination"""
    
    # Pagination
    items_per_page = 10
    total_pages = (len(schemes_list) + items_per_page - 1) // items_per_page
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.write(f"Page: **1 of {total_pages}**")
    
    with col2:
        page = st.slider(
            "Select page",
            min_value=1,
            max_value=total_pages,
            value=1,
            key=f"card_page_{len(schemes_list)}"
        )
    
    with col3:
        st.write(f"Showing {items_per_page} per page")
    
    # Get schemes for current page
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(schemes_list))
    page_schemes = schemes_list[start_idx:end_idx]
    
    st.markdown(f"Showing {start_idx + 1} to {end_idx} of {len(schemes_list)} schemes")
    st.markdown("---")
    
    # Display cards
    for i, scheme in enumerate(page_schemes):
        card_idx = start_idx + i
        
        with st.expander(
            f"📊 {scheme['scheme_name'][:50]} - {scheme['scheme_code']}",
            expanded=False
        ):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("NAV", f"₹{scheme['current_nav']:.2f}")
            with col2:
                st.metric("AMC", scheme['amc'][:20])
            with col3:
                category = scheme.get('category', 'N/A')
                st.metric("Category", str(category)[:20])
            with col4:
                st.metric("Date", scheme['nav_date'])
            
            st.markdown("---")
            
            # Actions in card
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("📊 Analyze", key=f"card_analyze_{card_idx}", use_container_width=True):
                    navigate_to_analysis(scheme)
            
            with col2:
                if st.button("🤖 Predict", key=f"card_predict_{card_idx}", use_container_width=True):
                    navigate_to_prediction(scheme)
            
            with col3:
                if st.button("⚖️ Compare", key=f"card_compare_{card_idx}", use_container_width=True):
                    add_to_compare(scheme['scheme_code'])
            
            with col4:
                if st.button("💼 Portfolio", key=f"card_portfolio_{card_idx}", use_container_width=True):
                    add_to_portfolio(scheme)


def display_scheme_actions(scheme: dict):
    """Display action buttons for selected scheme"""
    
    selected_code = scheme['scheme_code']
    
    st.markdown("---")
    st.markdown("#### 📊 Selected Scheme Details")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Code", selected_code)
    with col2:
        st.metric("NAV", f"₹{scheme['current_nav']:.2f}")
    with col3:
        st.metric("AMC", scheme['amc'][:20])
    with col4:
        category = scheme.get('category', 'N/A')
        st.metric("Category", str(category)[:15] if category else "N/A")
    with col5:
        st.metric("Date", scheme['nav_date'])
    
    # Action buttons
    st.markdown("---")
    st.markdown("#### ⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 View Analysis", use_container_width=True, type="primary", key="action_analyze"):
            navigate_to_analysis(scheme)
    
    with col2:
        if st.button("🤖 Predict NAV", use_container_width=True, key="action_predict"):
            navigate_to_prediction(scheme)
    
    with col3:
        if st.button("⚖️ Add to Compare", use_container_width=True, key="action_compare"):
            add_to_compare(selected_code)
    
    with col4:
        if st.button("💼 Add to Portfolio", use_container_width=True, key="action_portfolio"):
            add_to_portfolio(scheme)


# ==========================================
# HELPER FUNCTIONS - Navigation & Actions
# ==========================================

def navigate_to_analysis(scheme: dict):
    """Navigate to scheme analysis page"""
    st.session_state['selected_scheme_code'] = scheme['scheme_code']
    st.session_state['selected_scheme_name'] = scheme['scheme_name']
    st.session_state['navigate_to'] = '📊 Scheme Analysis'
    st.rerun()


def navigate_to_prediction(scheme: dict):
    """Navigate to NAV predictions page"""
    st.session_state['selected_scheme_code'] = scheme['scheme_code']
    st.session_state['selected_scheme_name'] = scheme['scheme_name']
    st.session_state['navigate_to'] = '🤖 NAV Predictions'
    st.rerun()


def add_to_compare(scheme_code: str):
    """Add scheme to comparison list"""
    if scheme_code not in st.session_state['compare_schemes_list']:
        st.session_state['compare_schemes_list'].append(scheme_code)
        st.success(f"✅ Added to comparison! ({len(st.session_state['compare_schemes_list'])} total)")
    else:
        st.warning("Already in comparison list")


def add_to_portfolio(scheme: dict):
    """Add scheme to portfolio"""
    if not any(s['code'] == scheme['scheme_code'] for s in st.session_state['portfolio_schemes_list']):
        st.session_state['portfolio_schemes_list'].append({
            'code': scheme['scheme_code'],
            'name': scheme['scheme_name'],
            'weight': 0.2
        })
        st.success(f"✅ Added to portfolio! ({len(st.session_state['portfolio_schemes_list'])} total)")
    else:
        st.warning("Already in portfolio")


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

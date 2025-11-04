"""
Home page - Advanced search with filters
"""

import streamlit as st
import pandas as pd
from frontend.utils.api_client import APIClient

api = APIClient()

def render():
    """Render home page"""
    
    st.markdown('<div class="main-header">🚀 MF_NAVigator</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI-Powered Mutual Fund Analytics & Prediction Platform</div>', unsafe_allow_html=True)
    
    # Hero metrics
    from frontend.components.metrics_display import display_hero_metrics
    display_hero_metrics()
    
    st.markdown("---")
    
    # Search section with filters
    render_advanced_search()
    
    st.markdown("---")
    
    # Platform capabilities
    render_capabilities()
    
    # Footer
    render_footer()


def render_advanced_search():
    """Render advanced search with filters"""
    
    st.markdown("### 🔍 Search & Filter Mutual Funds")
    
    # Initialize session state for filters
    if 'filter_category' not in st.session_state:
        st.session_state['filter_category'] = 'All'
    if 'filter_amc' not in st.session_state:
        st.session_state['filter_amc'] = 'All'
    
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
            key="home_quick_search"
        )
    
    with col2:
        limit = st.number_input("Results", min_value=5, max_value=100, value=20, key="home_quick_limit")
    
    if search_query and len(search_query) >= 2:
        with st.spinner("🔍 Searching..."):
            results = api.search_schemes(search_query, limit)
            
            if results and results['total_results'] > 0:
                display_search_results(results)
            else:
                st.warning("❌ No schemes found")

def render_advanced_filters():
    """Render advanced filter interface - IMPROVED"""
    
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
    
    # Apply button
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("🔍 Apply Filters", use_container_width=True, type="primary", key="apply_filters_btn"):
            apply_filters(selected_category, selected_amc, limit)
    
    with col2:
        if st.button("🔄 Reset", use_container_width=True, key="reset_filters_btn"):
            st.session_state['filter_category'] = 'All'
            st.session_state['filter_amc'] = 'All'
            if 'filtered_results' in st.session_state:
                del st.session_state['filtered_results']
            if 'analysis_filtered_results' in st.session_state:
                del st.session_state['analysis_filtered_results']
            st.rerun()
    
    st.markdown("---")
    
    # Display results if available
    if 'filtered_results' in st.session_state:
        display_search_results(st.session_state['filtered_results'])
    elif 'analysis_filtered_results' in st.session_state:
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
            
            # Determine session state key
            if 'analysis_filter_category' in st.session_state:
                st.session_state['analysis_filtered_results'] = filtered_results
            else:
                st.session_state['filtered_results'] = filtered_results
            
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
        key=f"view_type_{len(schemes_list)}"  # Unique key
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

def display_as_table(schemes_list: list):
    """Display schemes as a sortable table"""
    
    # Convert to DataFrame
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
    
    # Selection
    st.markdown("---")
    st.markdown("#### 🎯 Select a Scheme")
    
    selected_idx = st.selectbox(
        "Choose scheme:",
        options=range(len(schemes_list)),
        format_func=lambda x: f"{schemes_list[x]['scheme_name'][:40]} ({schemes_list[x]['scheme_code']})",
        key="table_scheme_select"
    )
    
    if selected_idx is not None:
        display_scheme_actions(schemes_list[selected_idx])


def display_as_cards(schemes_list: list):
    """Display schemes as expandable cards"""
    
    st.markdown("---")
    
    for i, scheme in enumerate(schemes_list[:10]):  # Show first 10 as cards
        with st.expander(f"📊 {scheme['scheme_name'][:50]} - {scheme['scheme_code']}"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("NAV", f"₹{scheme['current_nav']:.2f}")
            with col2:
                st.metric("AMC", scheme['amc'][:20])
            with col3:
                category = scheme.get('category', 'N/A')
                st.metric("Category", str(category)[:20] if category else "N/A")
            with col4:
                st.metric("Date", scheme['nav_date'])
            
            # Actions in expander
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("📊 Analyze", key=f"card_analyze_{i}", use_container_width=True):
                    navigate_to_analysis(scheme)
            
            with col2:
                if st.button("🤖 Predict", key=f"card_predict_{i}", use_container_width=True):
                    navigate_to_prediction(scheme)
            
            with col3:
                if st.button("⚖️ Compare", key=f"card_compare_{i}", use_container_width=True):
                    add_to_compare(scheme['scheme_code'])
            
            with col4:
                if st.button("💼 Portfolio", key=f"card_portfolio_{i}", use_container_width=True):
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


def render_capabilities():
    """Render platform capabilities"""
    
    st.markdown("### 📊 Platform Capabilities")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        #### 💰 Financial Metrics
        - **CAGR** - Compound Annual Growth
        - **Sharpe Ratio** - Risk-adjusted returns
        - **Returns** - 1D to 5Y periods
        - **Alpha & Beta** - Market comparison
        """)
    
    with col2:
        st.markdown("""
        #### ⚠️ Risk Metrics
        - **Volatility** - Price fluctuations
        - **Max Drawdown** - Worst-case loss
        - **VaR & CVaR** - Risk measures
        - **Downside Deviation** - Below-target risk
        """)
    
    with col3:
        st.markdown("""
        #### 🎯 Advanced Features
        - **Portfolio Builder** - Multi-scheme analysis
        - **Scheme Comparison** - Side-by-side
        - **ML Predictions** - XGBoost forecasting
        - **Category Filters** - Smart search
        """)


def render_footer():
    """Render footer"""
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>🚀 Built with Python, FastAPI, XGBoost & Streamlit</p>
        <p>📊 Data: AMFI India & MFapi.in</p>
    </div>
    """, unsafe_allow_html=True)

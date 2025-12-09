"""
Home page - Search and overview with scheme selection
"""

import streamlit as st
import pandas as pd
from frontend.utils.api_client import APIClient

api = APIClient()


def render():
    """Render home page"""
    
    # Hero section
    st.markdown('<div style="text-align: center; padding: 20px;"><h1>🚀 MF_NAVigator</h1></div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align: center; color: #666;"><h3>Mutual Fund Analytics & NAV Prediction Platform</h3></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick stats
    display_quick_stats()
    
    st.markdown("---")
    
    # Search section
    st.markdown("### 🔍 Search Mutual Funds")
    
    # Tabs for search methods
    tab1, tab2 = st.tabs(["🔍 Quick Search", "🎯 Advanced Filters"])
    
    with tab1:
        render_quick_search()
    
    with tab2:
        render_advanced_filters()
    
    st.markdown("---")
    
    # Footer
    render_footer()


def display_quick_stats():
    """Display quick statistics"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total Schemes", "9,000+")
    
    with col2:
        st.metric("🏢 AMCs", "44+")
    
    with col3:
        st.metric("🔄 Data Updated", "Daily")
    
    with col4:
        st.metric("💡 AI Powered", "Yes")


def render_quick_search():
    """Render quick search interface"""
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input(
            "Search by scheme name, AMC, or code",
            placeholder="e.g., HDFC, SBI Bluechip, 119551",
            key="home_quick_search"
        )
    
    with col2:
        limit = st.number_input("Results", min_value=5, max_value=100, value=20, key="home_quick_limit")
    
    if search_query and len(search_query) >= 2:
        with st.spinner("🔍 Searching..."):
            results = api.search_schemes(search_query, limit)
            
            if results and results.get('total_results', 0) > 0:
                display_search_results(results)
            else:
                st.warning("❌ No schemes found")


def render_advanced_filters():
    """Render advanced filter interface"""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        categories = ['All', 'Debt', 'Hybrid', 'Other']
        selected_category = st.selectbox(
            "Category",
            options=categories,
            key="home_filter_category",
            help="Other = Equity and specialized schemes"
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
            key="home_filter_amc"
        )
    
    with col3:
        limit = st.number_input(
            "Max Results",
            min_value=10,
            max_value=200,
            value=50,
            key="home_filter_limit"
        )
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("🔍 Apply Filters", use_container_width=True, type="primary", key="home_apply_filters"):
            apply_filters(selected_category, selected_amc, limit)
    
    with col2:
        if st.button("🔄 Reset", use_container_width=True, key="home_reset_filters"):
            if 'home_filtered_results' in st.session_state:
                del st.session_state['home_filtered_results']
            st.rerun()
    
    st.markdown("---")
    
    # Display results if available
    if 'home_filtered_results' in st.session_state:
        display_search_results(st.session_state['home_filtered_results'])
    else:
        st.info("💡 **Select filters and click 'Apply Filters' to see results**")


def apply_filters(category: str, amc: str, limit: int):
    """Apply filters and store results"""
    
    with st.spinner("🔍 Applying filters..."):
        try:
            # Determine search query
            if amc != 'All':
                search_query = amc
            else:
                search_query = "Fund"
            
            # Fetch results
            fetch_limit = min(limit * 3, 200)
            results = api.search_schemes(search_query, limit=fetch_limit)
            
            if not results or results.get('total_results', 0) == 0:
                st.warning(f"❌ No schemes found")
                return
            
            schemes_list = results['schemes']
            
            # Filter by category
            if category != 'All':
                schemes_list = [
                    s for s in schemes_list 
                    if s.get('category') == category
                ]
            
            # Filter by AMC
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
            
            st.session_state['home_filtered_results'] = filtered_results
            st.rerun()
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


def display_search_results(results: dict):
    """Display search results with table and card views"""
    
    schemes_list = results.get('schemes', [])
    
    if not schemes_list:
        st.warning("No schemes to display")
        return
    
    st.success(f"✅ Found {len(schemes_list)} schemes")
    
    # View type selector
    view_type = st.radio(
        "View as:",
        options=["📋 Table", "📦 Cards"],
        horizontal=True,
        key=f"home_view_type_{len(schemes_list)}"
    )
    
    if view_type == "📋 Table":
        render_table_view(schemes_list)
    else:
        render_cards_view(schemes_list)


def render_table_view(schemes_list: list):
    """Render schemes as a table"""
    
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
    
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.markdown("#### 🎯 Select a Scheme")
    
    selected_idx = st.selectbox(
        "Choose scheme:",
        options=range(len(schemes_list)),
        format_func=lambda x: f"{schemes_list[x]['scheme_name'][:40]} ({schemes_list[x]['scheme_code']})",
        key=f"home_table_select_{len(schemes_list)}"
    )
    
    if selected_idx is not None:
        display_scheme_actions(schemes_list[selected_idx])


def render_cards_view(schemes_list: list):
    """Render schemes as cards with pagination"""
    items_per_page = 10
    total_pages = (len(schemes_list) - 1) // items_per_page + 1
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        page = st.slider("Select page", min_value=1, max_value=total_pages, value=1, key=f"home_card_page_{len(schemes_list)}")
    
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(schemes_list))
    page_schemes = schemes_list[start_idx:end_idx]
    
    st.markdown(f"Showing {start_idx + 1} to {end_idx} of {len(schemes_list)} schemes")
    st.markdown("---")
    
    for i, scheme in enumerate(page_schemes):
        card_idx = start_idx + i
        
        with st.expander(f"{scheme['scheme_name'][:50]} - {scheme['scheme_code']}", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("NAV", f"₹{scheme['current_nav']:.2f}")
            
            with col2:
                st.metric("AMC", scheme['amc'][:20])
            
            with col3:
                st.metric("Category", str(scheme.get('category', 'N/A'))[:20])
            
            with col4:
                st.metric("Date", scheme['nav_date'])
            
            st.markdown("---")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("🔍 Analyze", key=f"home_card_analyze_{card_idx}", use_container_width=True):
                    navigate_to_analysis(scheme)
            
            with col2:
                if st.button("📈 Predict", key=f"home_card_predict_{card_idx}", use_container_width=True):
                    navigate_to_prediction(scheme)
            
            with col3:
                if st.button("⚖️ Compare", key=f"home_card_compare_{card_idx}", use_container_width=True):
                    # ✅ FIX: Pass both code AND name
                    add_to_compare(scheme['scheme_code'], scheme.get('scheme_name', scheme['scheme_code']))
            
            with col4:
                if st.button("📊 Portfolio", key=f"home_card_portfolio_{card_idx}", use_container_width=True):
                    # ✅ FIX: Pass entire scheme dict
                    add_to_portfolio(scheme)

def display_scheme_actions(scheme: dict):
    """Display action buttons for selected scheme"""
    st.markdown("---")
    st.markdown("### Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔍 View Analysis", use_container_width=True, type="primary", key="home_action_analyze"):
            navigate_to_analysis(scheme)
    
    with col2:
        if st.button("📈 Predict NAV", use_container_width=True, key="home_action_predict"):
            navigate_to_prediction(scheme)
    
    with col3:
        if st.button("⚖️ Add to Compare", use_container_width=True, key="home_action_compare"):
            # ✅ FIX: Pass both code AND name
            add_to_compare(scheme['scheme_code'], scheme.get('scheme_name', scheme['scheme_code']))
    
    with col4:
        if st.button("📊 Add to Portfolio", use_container_width=True, key="home_action_portfolio"):
            # ✅ FIX: Pass entire scheme dict
            add_to_portfolio(scheme)


def navigate_to_analysis(scheme: dict):
    st.session_state['selected_scheme_code'] = scheme['scheme_code']
    st.session_state['selected_scheme_name'] = scheme.get('scheme_name', scheme['scheme_code'])
    st.switch_page("pages/scheme_analysis.py")

def navigate_to_prediction(scheme: dict):
    st.session_state['selected_scheme_code'] = scheme['scheme_code']
    st.session_state['selected_scheme_name'] = scheme.get('scheme_name', scheme['scheme_code'])
    st.switch_page("pages/nav_predictions.py")


def add_to_compare(scheme_code: str, scheme_name: str = None):
    """
    Add scheme to comparison list - FIXED
    
    Args:
        scheme_code: Scheme code
        scheme_name: Scheme name (optional)
    """
    if 'compare_schemes_list' not in st.session_state:
        st.session_state['compare_schemes_list'] = []
    
    # ✅ FIX: Check if already added (handle both dict and string)
    already_added = any(
        (s.get("scheme_code") if isinstance(s, dict) else s) == scheme_code
        for s in st.session_state['compare_schemes_list']
    )
    
    if not already_added:
        # ✅ FIX: Always add as dict with both code and name
        st.session_state['compare_schemes_list'].append({
            "scheme_code": scheme_code,
            "scheme_name": scheme_name or scheme_code
        })
        st.success(f"✅ Added to comparison! ({len(st.session_state['compare_schemes_list'])} total)")
    else:
        st.warning("⚠️ Already in comparison list")

def add_to_portfolio(scheme: dict):
    """Add scheme to portfolio builder"""
    if 'portfolio_schemes_list' not in st.session_state:
        st.session_state['portfolio_schemes_list'] = []
    
    scheme_code = scheme['scheme_code']
    
    # Check if already added
    already_added = any(
        s.get("scheme_code") == scheme_code
        for s in st.session_state['portfolio_schemes_list']
    )
    
    if not already_added:
        # ✅ FIX: Add as dict with all necessary info
        st.session_state['portfolio_schemes_list'].append({
            "scheme_code": scheme_code,
            "scheme_name": scheme.get('scheme_name', scheme_code),
            "current_nav": scheme.get('current_nav', 0),
            "weight": 0  # User will set this in portfolio builder
        })
        st.success(f"✅ Added to portfolio! ({len(st.session_state['portfolio_schemes_list'])} total)")
    else:
        st.warning("⚠️ Already in portfolio")


def render_footer():
    """Render footer"""
    
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p><strong>🚀 Built with ❤️ using Python, FastAPI, XGBoost, and Streamlit</strong></p>
        <p>📊 Data sources: AMFI India & MFapi.in</p>
        <p>📈 Compare, Analyze, Predict - All Mutual Funds in One Place</p>
        <p style='font-size: 0.9em;'>⚠️ Disclaimer: For educational purposes only. Not financial advice.</p>
    </div>
    """, unsafe_allow_html=True)

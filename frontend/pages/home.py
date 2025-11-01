"""
Home page - Search and overview with scheme selection
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
    
    # Search section
    st.markdown("### 🔍 Search Mutual Funds")
    
    # Search input
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input(
            "Search by scheme name, AMC, or code",
            placeholder="e.g., HDFC, SBI, Axis",
            key="home_search_query"
        )
    
    with col2:
        limit = st.number_input("Max Results", min_value=5, max_value=50, value=20, key="home_limit")
    
    # Store search results in session state
    if search_query and len(search_query) >= 2:
        if 'last_search' not in st.session_state or st.session_state['last_search'] != search_query:
            st.session_state['last_search'] = search_query
            with st.spinner("🔍 Searching..."):
                results = api.search_schemes(search_query, limit)
                st.session_state['search_results'] = results
        
        # Display results
        if st.session_state.get('search_results'):
            results = st.session_state['search_results']
            st.success(f"✅ Found {results['total_results']} schemes")
            
            schemes_list = results['schemes']
            
            if schemes_list:
                st.markdown("---")
                st.markdown("#### 📋 Select a Scheme")
                
                # Create a dictionary for selectbox
                scheme_dict = {}
                for scheme in schemes_list:
                    key = f"{scheme['scheme_name'][:40]} ({scheme['scheme_code']})"
                    scheme_dict[key] = scheme
                
                # Selectbox
                selected_key = st.selectbox(
                    "Choose a scheme:",
                    options=list(scheme_dict.keys()),
                    key="home_scheme_selectbox",
                    label_visibility="collapsed"
                )
                
                if selected_key:
                    selected_scheme = scheme_dict[selected_key]
                    selected_code = selected_scheme['scheme_code']
                    
                    # Display scheme details
                    st.markdown("---")
                    st.markdown("#### 📊 Scheme Information")
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        st.metric("Code", selected_code)
                    with col2:
                        st.metric("NAV", f"₹{selected_scheme['current_nav']:.2f}")
                    with col3:
                        st.metric("AMC", selected_scheme['amc'][:20])
                    with col4:
                        category = selected_scheme.get('category', 'N/A')
                        st.metric("Category", str(category)[:15] if category else "N/A")
                    with col5:
                        st.metric("Date", selected_scheme['nav_date'])
                    
                    # Action buttons
                    st.markdown("---")
                    st.markdown("#### ⚡ Quick Actions")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        if st.button("📊 View Analysis", use_container_width=True, type="primary", key="home_btn_analyze"):
                            st.session_state['selected_scheme_code'] = selected_code
                            st.session_state['navigate_to'] = '📊 Scheme Analysis'
                            st.rerun()
                    
                    with col2:
                        if st.button("🤖 Predict NAV", use_container_width=True, key="home_btn_predict"):
                            st.session_state['selected_scheme_code'] = selected_code
                            st.session_state['navigate_to'] = '🤖 NAV Predictions'
                            st.rerun()
                    
                    with col3:
                        if st.button("⚖️ Add to Compare", use_container_width=True, key="home_btn_compare"):
                            if selected_code not in st.session_state['compare_schemes_list']:
                                st.session_state['compare_schemes_list'].append(selected_code)
                                st.success(f"✅ Added to comparison! ({len(st.session_state['compare_schemes_list'])} total)")
                            else:
                                st.warning("Already in comparison list")
                    
                    with col4:
                        if st.button("💼 Add to Portfolio", use_container_width=True, key="home_btn_portfolio"):
                            if not any(s['code'] == selected_code for s in st.session_state['portfolio_schemes_list']):
                                st.session_state['portfolio_schemes_list'].append({
                                    'code': selected_code,
                                    'name': selected_scheme['scheme_name'],
                                    'weight': 0.2
                                })
                                st.success(f"✅ Added to portfolio! ({len(st.session_state['portfolio_schemes_list'])} total)")
                            else:
                                st.warning("Already in portfolio")
    
    # Show lists if any schemes added
    if st.session_state['compare_schemes_list'] or st.session_state['portfolio_schemes_list']:
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        if st.session_state['compare_schemes_list']:
            with col1:
                st.markdown(f"### 📋 Comparison List ({len(st.session_state['compare_schemes_list'])})")
                for i, code in enumerate(st.session_state['compare_schemes_list'], 1):
                    st.text(f"{i}. {code}")
                
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    if st.button("🔄 Compare Now", use_container_width=True, key="home_compare_go"):
                        st.session_state['navigate_to'] = 'compare_schemes'
                        st.rerun()
                with col_b:
                    if st.button("🗑️ Clear", use_container_width=True, key="home_compare_clear"):
                        st.session_state['compare_schemes_list'] = []
                        st.rerun()
        
        if st.session_state['portfolio_schemes_list']:
            with col2:
                st.markdown(f"### 💼 Portfolio List ({len(st.session_state['portfolio_schemes_list'])})")
                for i, item in enumerate(st.session_state['portfolio_schemes_list'], 1):
                    st.text(f"{i}. {item['code']}")
                
                col_c, col_d, col_e = st.columns(3)
                with col_c:
                    if st.button("🏗️ Go to Portfolio", use_container_width=True, key="home_portfolio_go"):
                        st.session_state['navigate_to'] = 'portfolio_builder'
                        st.rerun()
                with col_d:
                    if st.button("🗑️ Clear Portfolio", use_container_width=True, key="home_portfolio_clear"):
                        st.session_state['portfolio_schemes_list'] = []
                        st.rerun()
    
    # Platform capabilities
    st.markdown("---")
    st.markdown("### 📊 Platform Capabilities")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        #### 💰 Financial Metrics
        - **CAGR** - Annual growth rate
        - **Sharpe Ratio** - Risk-adjusted returns
        - **Sortino Ratio** - Downside risk
        - **Returns** - Multiple time periods
        - **Alpha & Beta** - Active returns
        """)
    
    with col2:
        st.markdown("""
        #### ⚠️ Risk Metrics
        - **Volatility** - Price fluctuations
        - **Max Drawdown** - Worst loss
        - **Value at Risk** - Potential losses
        - **Downside Dev** - Below-target risk
        - **Ulcer Index** - Drawdown severity
        """)
    
    with col3:
        st.markdown("""
        #### 🎯 Advanced Features
        - **Portfolio Analysis** - Multi-schemes
        - **Scheme Comparison** - Side-by-side
        - **ML Predictions** - NAV forecasting
        - **Historical Data** - Full history
        - **Risk Analysis** - Detailed metrics
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>🚀 Built with Python, FastAPI, XGBoost & Streamlit</p>
        <p>📊 Data: AMFI India & MFapi.in</p>
    </div>
    """, unsafe_allow_html=True)

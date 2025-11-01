"""
Compare Schemes Page - Side-by-side comparison with persistent state
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from frontend.utils.api_client import APIClient

api = APIClient()

def render():
    """Render compare schemes page"""
    
    st.markdown("# ⚖️ Compare Schemes")
    st.markdown("Side-by-side comparison of multiple mutual funds")
    st.markdown("---")
    
    # Display current list
    if st.session_state['compare_schemes_list']:
        render_comparison_interface()
    else:
        st.info("👆 No schemes added yet. Add schemes from Home page or search below.")
        render_add_scheme_interface()


def render_add_scheme_interface():
    """Render interface to add schemes"""
    
    st.markdown("### Add Schemes to Compare")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_query = st.text_input(
            "Search scheme",
            placeholder="Enter scheme name, AMC, or code",
            key="compare_search_input"
        )
    
    with col2:
        limit = st.number_input("Max Results", min_value=5, max_value=50, value=20, key="compare_search_limit")
    
    with col3:
        st.write("")
        st.write("")
        search_btn = st.button("🔍 Search", key="compare_search_btn", use_container_width=True)
    
    if search_btn and search_query and len(search_query) >= 2:
        with st.spinner("🔍 Searching..."):
            results = api.search_schemes(search_query, limit)
            
            if results and results['total_results'] > 0:
                display_search_results_for_add(results)
            else:
                st.warning("No schemes found")


def display_search_results_for_add(results: dict):
    """Display search results for adding to comparison"""
    
    st.success(f"✅ Found {results['total_results']} schemes")
    
    schemes_list = results['schemes']
    
    # Create selection options
    scheme_options = {}
    for scheme in schemes_list:
        display_text = f"{scheme['scheme_name'][:40]} - {scheme['scheme_code']} ({scheme['amc'][:15]})"
        scheme_options[display_text] = scheme
    
    # Select scheme
    selected_display = st.selectbox(
        "Choose a scheme to add:",
        options=list(scheme_options.keys()),
        key=f"compare_add_selector_{results['total_results']}"
    )
    
    selected_scheme = scheme_options[selected_display]
    selected_code = selected_scheme['scheme_code']
    
    # Display info
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Code", selected_code)
    with col2:
        st.metric("NAV", f"₹{selected_scheme['current_nav']:.2f}")
    with col3:
        st.metric("AMC", selected_scheme['amc'][:20])
    with col4:
        st.metric("Date", selected_scheme['nav_date'])
    
    # Add button
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Add to Comparison", use_container_width=True, type="primary", key="compare_add_btn"):
            if selected_code not in st.session_state['compare_schemes_list']:
                st.session_state['compare_schemes_list'].append(selected_code)
                st.success(f"✅ Added! Total: {len(st.session_state['compare_schemes_list'])}")
                st.rerun()
            else:
                st.warning("Already in comparison list")
    
    with col2:
        if st.button("❌ Cancel", use_container_width=True, key="compare_cancel_btn"):
            st.rerun()


def render_comparison_interface():
    """Render comparison interface with persistent list"""
    
    st.markdown(f"### 📊 Schemes Selected ({len(st.session_state['compare_schemes_list'])})")
    
    # Display current list with actions
    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
    col1.write("**Scheme Code**")
    col2.write("**Action 1**")
    col3.write("**Action 2**")
    col4.write("**Action 3**")
    col5.write("**Remove**")
    
    st.markdown("---")
    
    for i, code in enumerate(st.session_state['compare_schemes_list']):
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
        
        with col1:
            st.text(f"{i+1}. {code}")
        
        with col2:
            if st.button("📊", key=f"comp_view_{i}", help="View Details"):
                st.session_state['selected_scheme_code'] = code
                st.session_state['navigate_to'] = 'scheme_analysis'
                st.rerun()
        
        with col3:
            if st.button("🤖", key=f"comp_predict_{i}", help="Predict"):
                st.session_state['selected_scheme_code'] = code
                st.session_state['navigate_to'] = 'nav_predictions'
                st.rerun()
        
        with col4:
            st.write("")  # Placeholder
        
        with col5:
            if st.button("🗑️", key=f"comp_remove_{i}", help="Remove"):
                st.session_state['compare_schemes_list'].remove(code)
                st.rerun()
    
    st.markdown("---")
    
    # Action buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("➕ Add More", use_container_width=True, key="comp_add_more"):
            st.session_state['show_add_form'] = True
            st.rerun()
    
    with col2:
        if len(st.session_state['compare_schemes_list']) >= 2:
            if st.button("🔄 Compare Now", use_container_width=True, type="primary", key="comp_compare_btn"):
                st.session_state['run_comparison'] = True
                st.rerun()
        else:
            st.button("🔄 Compare Now (Need 2+)", use_container_width=True, disabled=True)
    
    with col3:
        if st.button("🗑️ Clear All", use_container_width=True, key="comp_clear_all"):
            st.session_state['compare_schemes_list'] = []
            st.rerun()
    
    with col4:
        if st.button("📥 Export CSV", use_container_width=True, key="comp_export"):
            st.info("Export feature coming soon!")
    
    # Show add form if requested
    if st.session_state.get('show_add_form'):
        st.markdown("---")
        render_add_scheme_interface()
        st.session_state['show_add_form'] = False
    
    # Run comparison
    if st.session_state.get('run_comparison'):
        st.markdown("---")
        render_comparison_results()


def render_comparison_results():
    """Render comparison results"""
    
    st.markdown("### 📊 Comparison Results")
    
    with st.spinner("📊 Comparing schemes..."):
        try:
            data = api.compare_schemes(st.session_state['compare_schemes_list'])
            
            if not data or not data.get('schemes'):
                st.error("❌ Unable to compare schemes")
                return
            
            # Display results
            df_compare = pd.DataFrame(data['schemes'])
            
            # Display table
            st.dataframe(
                df_compare[[
                    'scheme_code', 'scheme_name', 'current_nav', 'cagr',
                    'sharpe_ratio', 'volatility', 'max_drawdown'
                ]].fillna('N/A'),
                use_container_width=True,
                hide_index=True
            )
            
            # Best performers
            st.markdown("---")
            st.markdown("#### 🏆 Best Performers")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if data.get('best_by_sharpe'):
                    st.success(f"**🎯 Best Sharpe:** {data['best_by_sharpe']}")
            
            with col2:
                if data.get('best_by_return'):
                    st.success(f"**📈 Best Return:** {data['best_by_return']}")
            
            # Charts
            st.markdown("---")
            render_comparison_charts(df_compare)
            
            # Download
            csv = df_compare.to_csv(index=False)
            st.download_button(
                label="📥 Download Comparison",
                data=csv,
                file_name="comparison.csv",
                mime="text/csv",
                key="comp_download"
            )
            
            st.session_state['run_comparison'] = False
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


def render_comparison_charts(df: pd.DataFrame):
    """Render comparison charts"""
    
    # Returns chart
    if 'cagr' in df.columns:
        try:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df['scheme_code'], y=df['cagr'], name='CAGR', marker_color='lightblue'))
            fig.update_layout(title="CAGR Comparison", height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        except:
            pass
    
    # Risk chart
    if 'volatility' in df.columns:
        try:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df['scheme_code'], y=df['volatility'], name='Volatility', marker_color='orange'))
            fig.update_layout(title="Volatility Comparison", height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        except:
            pass

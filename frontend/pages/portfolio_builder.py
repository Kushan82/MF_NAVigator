"""
Portfolio Builder Page - Create and analyze portfolios with editable weights
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from frontend.utils.api_client import APIClient

api = APIClient()

def render():
    """Render portfolio builder page"""
    
    st.markdown("# 📈 Portfolio Builder")
    st.markdown("Create and analyze multi-scheme portfolios")
    st.markdown("---")
    
    # Display current portfolio or add interface
    if st.session_state['portfolio_schemes_list']:
        render_portfolio_manager()
    else:
        st.info("👆 No schemes added yet. Add schemes from Home page or search below.")
        render_add_scheme_interface()


def render_add_scheme_interface():
    """Render interface to add schemes"""
    
    st.markdown("### Add Schemes to Portfolio")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_query = st.text_input(
            "Search scheme",
            placeholder="Enter scheme name, AMC, or code",
            key="portfolio_search_input"
        )
    
    with col2:
        limit = st.number_input("Max Results", min_value=5, max_value=50, value=20, key="portfolio_search_limit")
    
    with col3:
        st.write("")
        st.write("")
        search_btn = st.button("🔍 Search", key="portfolio_search_btn", use_container_width=True)
    
    if search_btn and search_query and len(search_query) >= 2:
        with st.spinner("🔍 Searching..."):
            results = api.search_schemes(search_query, limit)
            
            if results and results['total_results'] > 0:
                display_search_results_for_add(results)
            else:
                st.warning("No schemes found")


def display_search_results_for_add(results: dict):
    """Display search results for adding to portfolio"""
    
    st.success(f"✅ Found {results['total_results']} schemes")
    
    schemes_list = results['schemes']
    
    # Create selection options
    scheme_options = {}
    for scheme in schemes_list:
        display_text = f"{scheme['scheme_name'][:40]} - {scheme['scheme_code']}"
        scheme_options[display_text] = scheme
    
    # Select scheme
    selected_display = st.selectbox(
        "Choose a scheme to add:",
        options=list(scheme_options.keys()),
        key=f"portfolio_add_selector_{results['total_results']}"
    )
    
    selected_scheme = scheme_options[selected_display]
    selected_code = selected_scheme['scheme_code']
    
    # Weight input
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Code", selected_code)
    with col2:
        st.metric("NAV", f"₹{selected_scheme['current_nav']:.2f}")
    with col3:
        st.metric("AMC", selected_scheme['amc'][:20])
    with col4:
        weight = st.number_input("Weight (%)", min_value=1, max_value=100, value=20, key="portfolio_weight_input")
    
    # Add button
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Add to Portfolio", use_container_width=True, type="primary", key="portfolio_add_btn"):
            if not any(s['code'] == selected_code for s in st.session_state['portfolio_schemes_list']):
                st.session_state['portfolio_schemes_list'].append({
                    'code': selected_code,
                    'name': selected_scheme['scheme_name'],
                    'weight': weight / 100.0
                })
                st.success(f"✅ Added! Total: {len(st.session_state['portfolio_schemes_list'])}")
                st.rerun()
            else:
                st.warning("Already in portfolio")
    
    with col2:
        if st.button("❌ Cancel", use_container_width=True, key="portfolio_cancel_btn"):
            st.rerun()


def render_portfolio_manager():
    """Render portfolio manager with editable weights"""
    
    st.markdown(f"### 💼 Portfolio ({len(st.session_state['portfolio_schemes_list'])} schemes)")
    
    # Calculate total weight
    total_weight = sum([item['weight'] for item in st.session_state['portfolio_schemes_list']])
    
    # Display portfolio table with editable weights
    st.markdown("#### Edit Portfolio")
    
    # Create columns for header
    col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 1, 1.5, 1.5, 0.8])
    col1.write("**#**")
    col2.write("**Scheme Name**")
    col3.write("**Code**")
    col4.write("**Weight (%)**")
    col5.write("**Decimal**")
    col6.write("**Remove**")
    
    st.markdown("---")
    
    # Display schemes with editable weights
    for i, item in enumerate(st.session_state['portfolio_schemes_list']):
        col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 1, 1.5, 1.5, 0.8])
        
        with col1:
            st.text(f"{i+1}")
        
        with col2:
            st.text(item['name'][:30])
        
        with col3:
            st.text(item['code'])
        
        with col4:
            # Editable weight percentage
            weight_pct = st.number_input(
                f"Weight % for {item['code']}",
                min_value=1.0,
                max_value=100.0,
                value=item['weight'] * 100,
                step=1.0,
                key=f"weight_pct_{i}",
                label_visibility="collapsed"
            )
            # Update weight in session state
            st.session_state['portfolio_schemes_list'][i]['weight'] = weight_pct / 100.0
        
        with col5:
            # Show decimal weight
            st.text(f"{st.session_state['portfolio_schemes_list'][i]['weight']:.3f}")
        
        with col6:
            if st.button("🗑️", key=f"port_remove_{i}", help="Remove"):
                st.session_state['portfolio_schemes_list'].pop(i)
                st.rerun()
    
    st.markdown("---")
    
    # Recalculate total weight
    total_weight = sum([item['weight'] for item in st.session_state['portfolio_schemes_list']])
    
    # Weight validation
    st.markdown("#### Weight Validation")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Weight", f"{total_weight*100:.1f}%")
    
    with col2:
        if abs(total_weight - 1.0) < 0.01:
            st.success("✅ Balanced (100%)")
        else:
            st.warning(f"⚠️ Not balanced ({total_weight*100:.1f}%)")
    
    with col3:
        st.text("")  # Spacer
    
    # Action buttons
    st.markdown("---")
    st.markdown("#### Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("➕ Add More", use_container_width=True, key="port_add_more"):
            st.session_state['show_add_form'] = True
            st.rerun()
    
    with col2:
        if abs(total_weight - 1.0) < 0.01:
            if st.button("🔄 Analyze", use_container_width=True, type="primary", key="port_analyze"):
                st.session_state['run_analysis'] = True
                st.rerun()
        else:
            st.button("🔄 Analyze (Balance weights first)", use_container_width=True, disabled=True)
    
    with col3:
        if st.button("⚖️ Auto-Balance", use_container_width=True, key="port_balance"):
            weight = 1.0 / len(st.session_state['portfolio_schemes_list'])
            for item in st.session_state['portfolio_schemes_list']:
                item['weight'] = weight
            st.success("✅ Auto-balanced!")
            st.rerun()
    
    with col4:
        if st.button("🗑️ Clear All", use_container_width=True, key="port_clear"):
            st.session_state['portfolio_schemes_list'] = []
            if 'run_analysis' in st.session_state:
                st.session_state['run_analysis'] = False
            st.rerun()
    
    # Show add form if requested
    if st.session_state.get('show_add_form'):
        st.markdown("---")
        st.markdown("### Add More Schemes")
        render_add_scheme_interface()
        st.session_state['show_add_form'] = False
    
    # Run analysis
    if st.session_state.get('run_analysis'):
        st.markdown("---")
        render_portfolio_analysis()


def render_portfolio_analysis():
    """Render portfolio analysis results"""
    
    st.markdown("### 📊 Portfolio Analysis Results")
    
    with st.spinner("📊 Analyzing portfolio..."):
        try:
            # Prepare request
            schemes = [
                {"scheme_code": item['code'], "weight": item['weight']}
                for item in st.session_state['portfolio_schemes_list']
            ]
            
            data = api.analyze_portfolio(schemes)
            
            if not data:
                st.error("❌ Unable to analyze portfolio")
                return
            
            # Display key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Annual Return", f"{data['annualized_return']*100:.2f}%")
            with col2:
                st.metric("Volatility", f"{data['volatility']*100:.2f}%")
            with col3:
                st.metric("Sharpe Ratio", f"{data['sharpe_ratio']:.3f}")
            with col4:
                st.metric("Max Drawdown", f"{abs(data['max_drawdown'])*100:.2f}%")
            
            # Additional metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Sortino Ratio", f"{data['sortino_ratio']:.3f}")
            with col2:
                st.metric("VaR (95%)", f"{data['var_95']*100:.2f}%")
            with col3:
                st.metric("Diversification", f"{data['diversification_score']:.3f}")
            
            # Portfolio allocation pie chart
            st.markdown("---")
            st.markdown("#### 📊 Portfolio Allocation")
            
            fig = go.Figure(data=[go.Pie(
                labels=[f"{item['code']}" for item in st.session_state['portfolio_schemes_list']],
                values=[item['weight']*100 for item in st.session_state['portfolio_schemes_list']],
                hole=0.3,
                textinfo='label+percent'
            )])
            
            fig.update_layout(
                title="Portfolio Weight Distribution",
                height=500,
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Weights table
            st.markdown("---")
            st.markdown("#### Allocation Breakdown")
            
            allocation_df = pd.DataFrame([
                {
                    'Scheme Code': item['code'],
                    'Scheme Name': item['name'][:30],
                    'Weight (%)': f"{item['weight']*100:.2f}%",
                    'Decimal': f"{item['weight']:.4f}"
                }
                for item in st.session_state['portfolio_schemes_list']
            ])
            
            st.dataframe(allocation_df, use_container_width=True, hide_index=True)
            
            # Download results
            csv = allocation_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Portfolio",
                data=csv,
                file_name="portfolio_allocation.csv",
                mime="text/csv",
                key="port_download"
            )
            
            st.session_state['run_analysis'] = False
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

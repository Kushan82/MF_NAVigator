"""
Portfolio Builder Page - Create, save, and manage portfolios
COMPLETE VERSION - Fixes all rerun issues
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from frontend.utils.api_client import APIClient

api = APIClient()

def render():
    """Render portfolio builder page"""
    
    st.markdown("# 📈 Portfolio Builder")
    st.markdown("Create, manage, and analyze multi-scheme portfolios")
    st.markdown("---")
    
    # Show tabs: Builder vs Saved Portfolios
    tab1, tab2 = st.tabs(["🏗️ Build Portfolio", "📚 Saved Portfolios"])
    
    with tab1:
        render_portfolio_builder()
    
    with tab2:
        render_saved_portfolios()


# ==========================================
# TAB 1: PORTFOLIO BUILDER
# ==========================================

def render_portfolio_builder():
    """Render portfolio builder interface"""
    
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
            key="portfolio_search_input_unique_1"
        )
    
    with col2:
        limit = st.number_input("Max Results", min_value=5, max_value=50, value=20, key="portfolio_search_limit_unique_1")
    
    with col3:
        st.write("")
        st.write("")
        search_btn = st.button("🔍 Search", key="portfolio_search_btn_unique_1", use_container_width=True)
    
    if search_btn and search_query and len(search_query) >= 2:
        # Store search results in session state
        with st.spinner("🔍 Searching..."):
            results = api.search_schemes(search_query, limit)
            if results and results['total_results'] > 0:
                st.session_state['portfolio_search_results'] = results
                st.session_state['portfolio_search_query'] = search_query
    
    # Display stored results if available
    if st.session_state.get('portfolio_search_results'):
        display_search_results_for_add(st.session_state['portfolio_search_results'])


def display_search_results_for_add(results: dict):
    """Display search results for adding to portfolio"""
    
    st.success(f"✅ Found {results['total_results']} schemes")
    
    schemes_list = results['schemes']
    
    # Create selection options
    scheme_options = {}
    for scheme in schemes_list:
        display_text = f"{scheme['scheme_name'][:40]} - {scheme['scheme_code']}"
        scheme_options[display_text] = scheme
    
    st.markdown("---")
    st.markdown("#### 📋 Select Scheme")
    
    # Initialize selected index in session state to prevent reset
    if 'portfolio_selected_scheme_idx' not in st.session_state:
        st.session_state['portfolio_selected_scheme_idx'] = 0
    
    # Selectbox with persistent index
    selected_idx = st.selectbox(
        "Choose a scheme to add:",
        options=range(len(schemes_list)),
        index=st.session_state['portfolio_selected_scheme_idx'],
        format_func=lambda x: f"{schemes_list[x]['scheme_name'][:40]} - {schemes_list[x]['scheme_code']}",
        key=f"portfolio_scheme_selectbox_{results['total_results']}"
    )
    
    # Update session state
    st.session_state['portfolio_selected_scheme_idx'] = selected_idx
    
    selected_scheme = schemes_list[selected_idx]
    selected_code = selected_scheme['scheme_code']
    
    # Show scheme info
    st.markdown("---")
    st.markdown("#### 📊 Scheme Details")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Code", selected_code)
    with col2:
        st.metric("NAV", f"₹{selected_scheme['current_nav']:.2f}")
    with col3:
        st.metric("AMC", selected_scheme['amc'][:20])
    with col4:
        st.metric("Category", selected_scheme.get('category', 'N/A')[:20])
    
    st.markdown("---")
    st.markdown("#### ⚖️ Set Weight")
    
    # Initialize weight in session state
    weight_key = f"temp_portfolio_weight_{selected_code}"
    if weight_key not in st.session_state:
        st.session_state[weight_key] = 20.0
    
    # Use slider (less prone to rerun issues than number_input)
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        weight = st.slider(
            "Weight (%)",
            min_value=1.0,
            max_value=100.0,
            value=st.session_state[weight_key],
            step=0.5,
            key=f"portfolio_weight_slider_{selected_code}"
        )
        st.session_state[weight_key] = weight
    
    with col2:
        st.metric("Selected", f"{weight:.1f}%")
    
    with col3:
        st.metric("Decimal", f"{weight/100:.3f}")
    
    st.markdown("---")
    
    # Add button
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("✅ Add", use_container_width=True, type="primary", key="portfolio_add_btn_final"):
            if not any(s['code'] == selected_code for s in st.session_state['portfolio_schemes_list']):
                st.session_state['portfolio_schemes_list'].append({
                    'code': selected_code,
                    'name': selected_scheme['scheme_name'],
                    'weight': weight / 100.0
                })
                # Clear temp data
                if weight_key in st.session_state:
                    del st.session_state[weight_key]
                st.session_state['portfolio_search_results'] = None
                st.session_state['portfolio_selected_scheme_idx'] = 0
                st.success(f"✅ Added! Total: {len(st.session_state['portfolio_schemes_list'])}")
                st.rerun()
            else:
                st.warning("Already in portfolio")
    
    with col2:
        if st.button("❌ Cancel", use_container_width=True, key="portfolio_cancel_final"):
            if weight_key in st.session_state:
                del st.session_state[weight_key]
            st.session_state['portfolio_search_results'] = None
            st.session_state['portfolio_selected_scheme_idx'] = 0
            st.rerun()


def render_portfolio_manager():
    """Render portfolio manager with editable weights - NO RESET VERSION"""
    
    st.markdown(f"### 💼 Portfolio ({len(st.session_state['portfolio_schemes_list'])} schemes)")
    
    # Initialize weight_changes in session state
    if 'weight_changes' not in st.session_state:
        st.session_state['weight_changes'] = {}
    
    # Initialize show_add_form flag
    if 'show_portfolio_add_form' not in st.session_state:
        st.session_state['show_portfolio_add_form'] = False
    
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
    
    # Display schemes with editable weights using sliders (not number inputs)
    for i, item in enumerate(st.session_state['portfolio_schemes_list']):
        col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 1, 1.5, 1.5, 0.8])
        
        with col1:
            st.text(f"{i+1}")
        
        with col2:
            st.text(item['name'][:30])
        
        with col3:
            st.text(item['code'])
        
        with col4:
            # Get current weight from session state (with fallback)
            current_weight = st.session_state['weight_changes'].get(i, item['weight'] * 100)
            
            # Use slider instead of number_input to avoid rerun on change
            weight_pct = st.slider(
                f"Weight for {item['code']}",
                min_value=0.1,
                max_value=100.0,
                value=float(current_weight),
                step=0.1,
                key=f"weight_slider_edit_{i}_{item['code']}",
                label_visibility="collapsed"
            )
            
            # Store in local cache
            st.session_state['weight_changes'][i] = weight_pct
            
            # Update session state
            st.session_state['portfolio_schemes_list'][i]['weight'] = weight_pct / 100.0
        
        with col5:
            st.text(f"{st.session_state['portfolio_schemes_list'][i]['weight']:.3f}")
        
        with col6:
            if st.button("🗑️", key=f"port_remove_{i}_{item['code']}", help="Remove"):
                st.session_state['portfolio_schemes_list'].pop(i)
                if i in st.session_state['weight_changes']:
                    del st.session_state['weight_changes'][i]
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
            weight_balanced = True
        else:
            remaining = (1.0 - total_weight) * 100
            if remaining > 0:
                st.warning(f"⚠️ Need {remaining:.1f}% more")
            else:
                st.warning(f"⚠️ {abs(remaining):.1f}% over 100%")
            weight_balanced = False
    
    with col3:
        st.text("")
    
    # Action buttons
    st.markdown("---")
    st.markdown("#### Actions")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("➕ Add More", use_container_width=True, key="port_add_more_unique"):
            st.session_state['show_portfolio_add_form'] = True
            st.rerun()
    
    with col2:
        if st.button("⚖️ Auto-Balance", use_container_width=True, key="port_balance_unique"):
            weight = 1.0 / len(st.session_state['portfolio_schemes_list'])
            for i, item in enumerate(st.session_state['portfolio_schemes_list']):
                item['weight'] = weight
                st.session_state['weight_changes'][i] = weight * 100
            st.success("✅ Auto-balanced!")
            st.rerun()
    
    with col3:
        if weight_balanced:
            if st.button("💾 Create Portfolio", use_container_width=True, type="primary", key="port_create_unique"):
                st.session_state['show_create_modal'] = True
        else:
            st.button("💾 Create Portfolio (Balance first)", use_container_width=True, disabled=True)
    
    with col4:
        if st.button("🔄 Reset", use_container_width=True, key="port_reset_unique"):
            st.session_state['portfolio_schemes_list'] = []
            st.session_state['weight_changes'] = {}
            st.rerun()
    
    with col5:
        if st.button("🗑️ Clear All", use_container_width=True, key="port_clear_unique"):
            st.session_state['portfolio_schemes_list'] = []
            st.session_state['weight_changes'] = {}
            st.rerun()
    
    # NEW: Show add form if "Add More" is clicked
    if st.session_state.get('show_portfolio_add_form'):
        st.markdown("---")
        st.markdown("### ➕ Add More Schemes")
        
        render_add_scheme_interface()
        
        # Add close button
        if st.button("❌ Close Add Form", use_container_width=True, key="close_add_form"):
            st.session_state['show_portfolio_add_form'] = False
            st.rerun()
    
    # Show create portfolio modal
    if st.session_state.get('show_create_modal'):
        render_create_portfolio_modal()

def render_create_portfolio_modal():
    """Render modal dialog to name and save portfolio"""
    
    st.markdown("---")
    st.markdown("### 💾 Create New Portfolio")
    
    with st.form("create_portfolio_form", clear_on_submit=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            portfolio_name = st.text_input(
                "Portfolio Name",
                placeholder="e.g., Aggressive Growth, Conservative Mix",
                help="Give your portfolio a unique name",
                key="portfolio_name_input_modal"
            )
        
        with col2:
            st.write("")
            st.write("")
        
        # Add description (optional)
        portfolio_description = st.text_area(
            "Description (Optional)",
            placeholder="Add notes about this portfolio...",
            height=80,
            key="portfolio_description_input_modal"
        )
        
        # Show portfolio summary
        st.markdown("#### Portfolio Summary")
        
        summary_df = pd.DataFrame([
            {
                'Scheme Code': item['code'],
                'Scheme Name': item['name'][:35],
                'Weight (%)': f"{item['weight']*100:.2f}%",
                'Decimal': f"{item['weight']:.4f}"
            }
            for item in st.session_state['portfolio_schemes_list']
        ])
        
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
        
        # Form submission
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submit_btn = st.form_submit_button("✅ Save Portfolio", use_container_width=True)
        
        with col2:
            cancel_btn = st.form_submit_button("❌ Cancel", use_container_width=True)
        
        if submit_btn:
            if not portfolio_name or len(portfolio_name.strip()) == 0:
                st.error("❌ Portfolio name cannot be empty")
            else:
                # Save portfolio
                save_portfolio(portfolio_name, portfolio_description)
        
        if cancel_btn:
            st.session_state['show_create_modal'] = False
            st.rerun()


def save_portfolio(portfolio_name: str, description: str = ""):
    """Save portfolio to backend"""
    
    try:
        # Prepare portfolio data
        portfolio_data = {
            "name": portfolio_name.strip(),
            "description": description.strip(),
            "schemes": [
                {
                    "scheme_code": item['code'],
                    "scheme_name": item['name'],
                    "weight": item['weight']
                }
                for item in st.session_state['portfolio_schemes_list']
            ],
            "created_at": datetime.now().isoformat(),
            "total_weight": sum([item['weight'] for item in st.session_state['portfolio_schemes_list']])
        }
        
        # Call API to save
        with st.spinner("💾 Saving portfolio..."):
            response = api.save_portfolio(portfolio_data)
        
        if response and response.get('success'):
            st.success(f"✅ Portfolio '{portfolio_name}' saved successfully!")
            st.info(f"Portfolio ID: {response.get('portfolio_id')}")
            
            # Reset form
            st.session_state['portfolio_schemes_list'] = []
            st.session_state['weight_changes'] = {}
            st.session_state['show_create_modal'] = False
            
            # Refresh saved portfolios
            st.rerun()
        else:
            st.error(f"❌ Error saving portfolio: {response.get('error', 'Unknown error')}")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")


# ==========================================
# TAB 2: SAVED PORTFOLIOS
# ==========================================

def render_saved_portfolios():
    """Render saved portfolios management interface"""
    
    st.markdown("### 📚 Your Saved Portfolios")
    
    # Fetch portfolios
    with st.spinner("📂 Loading portfolios..."):
        portfolios = get_saved_portfolios()
    
    if not portfolios:
        st.info("📭 No portfolios saved yet. Create one using the Portfolio Builder!")
        return
    
    st.success(f"✅ Found {len(portfolios)} portfolio(s)")
    
    st.markdown("---")
    
    # Display portfolios
    for portfolio in portfolios:
        render_portfolio_card(portfolio)


def get_saved_portfolios():
    """Fetch saved portfolios from backend"""
    
    try:
        portfolios = api.get_saved_portfolios()
        return portfolios if portfolios else []
    except Exception as e:
        st.error(f"❌ Error loading portfolios: {str(e)}")
        return []


def render_portfolio_card(portfolio: dict):
    """Render individual portfolio card - FIXED"""
    
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col1:
            st.markdown(f"#### 📋 {portfolio['name']}")
            if portfolio.get('description'):
                st.caption(portfolio['description'])
            st.caption(f"Created: {portfolio.get('created_at', 'N/A')}")
        
        with col2:
            st.metric("Schemes", len(portfolio.get('schemes', [])))
            st.metric("Weight", f"{portfolio.get('total_weight', 0)*100:.1f}%")
        
        with col3:
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                # FIXED: Changed navigation method
                if st.button("📊 Analyze", key=f"analyze_{portfolio['id']}", use_container_width=True):
                    # Store portfolio data and navigate to portfolio builder tab
                    st.session_state['analyzing_portfolio'] = portfolio
                    st.success("✅ Loading portfolio analysis...")
                    # Show analysis inline instead of navigating
                    show_portfolio_analysis(portfolio)
            
            with col_b:
                if st.button("✏️ Edit", key=f"edit_{portfolio['id']}", use_container_width=True):
                    load_portfolio_for_edit(portfolio)
            
            with col_c:
                if st.button("🗑️ Delete", key=f"delete_{portfolio['id']}", use_container_width=True):
                    delete_portfolio(portfolio['id'], portfolio['name'])
        
        st.markdown("---")
def show_portfolio_analysis(portfolio: dict):
    """Show portfolio analysis inline - NEW FUNCTION"""
    
    st.markdown("---")
    st.markdown(f"### 📊 Analysis: {portfolio['name']}")
    
    try:
        # Prepare portfolio data for API
        portfolio_request = {
            "name": portfolio['name'],
            "description": portfolio.get('description', ''),
            "schemes": portfolio.get('schemes', [])
        }
        
        # Call portfolio analysis API
        with st.spinner("📊 Analyzing portfolio..."):
            analysis = api.analyze_portfolio(portfolio_request)
        
        if not analysis:
            st.error("❌ Could not analyze portfolio")
            return
        
        # Display metrics
        st.markdown("#### 📈 Portfolio Metrics")
        
        metrics = analysis.get('metrics', {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            ann_return = metrics.get('annualized_return', 0)
            st.metric("Annual Return", f"{ann_return*100:.2f}%")
        
        with col2:
            volatility = metrics.get('volatility', 0)
            st.metric("Volatility", f"{volatility*100:.2f}%")
        
        with col3:
            sharpe = metrics.get('sharpe_ratio', 0)
            st.metric("Sharpe Ratio", f"{sharpe:.3f}")
        
        with col4:
            max_dd = metrics.get('max_drawdown', 0)
            st.metric("Max Drawdown", f"{abs(max_dd)*100:.2f}%")
        
        # Additional metrics
        st.markdown("---")
        st.markdown("#### 📋 Additional Metrics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            sortino = metrics.get('sortino_ratio', 0)
            st.metric("Sortino Ratio", f"{sortino:.3f}")
        
        with col2:
            var_95 = metrics.get('var_95', 0)
            st.metric("VaR (95%)", f"{var_95*100:.2f}%")
        
        with col3:
            # Add diversification if available
            st.metric("Schemes", len(portfolio.get('schemes', [])))
        
        # Scheme breakdown
        st.markdown("---")
        st.markdown("#### 🎯 Portfolio Composition")
        
        schemes_df = pd.DataFrame(portfolio.get('schemes', []))
        if not schemes_df.empty:
            schemes_df['weight_pct'] = schemes_df['weight'] * 100
            schemes_df = schemes_df[['scheme_name', 'weight_pct']]
            schemes_df.columns = ['Scheme Name', 'Weight (%)']
            
            st.dataframe(schemes_df, use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error(f"❌ Analysis error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

def load_portfolio_for_edit(portfolio: dict):
    """Load portfolio into builder for editing"""
    
    st.session_state['portfolio_schemes_list'] = [
        {
            'code': scheme['scheme_code'],
            'name': scheme['scheme_name'],
            'weight': scheme['weight']
        }
        for scheme in portfolio.get('schemes', [])
    ]
    st.session_state['weight_changes'] = {
        i: scheme['weight'] * 100 
        for i, scheme in enumerate(portfolio.get('schemes', []))
    }
    st.success("✅ Portfolio loaded for editing!")
    st.info("💡 You can now edit weights and save as a new portfolio")
    st.rerun()


def delete_portfolio(portfolio_id: str, portfolio_name: str):
    """Delete portfolio with confirmation"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Confirm Delete", key=f"confirm_delete_{portfolio_id}", use_container_width=True):
            try:
                with st.spinner(f"🗑️ Deleting '{portfolio_name}'..."):
                    api.delete_portfolio(portfolio_id)
                st.success("✅ Portfolio deleted!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    with col2:
        if st.button("❌ Cancel", key=f"cancel_delete_{portfolio_id}", use_container_width=True):
            st.rerun()

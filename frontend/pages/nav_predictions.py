"""
NAV Predictions Page - ML-powered forecasting with advanced search and filters
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from frontend.utils.api_client import APIClient

api = APIClient()

def render():
    """Render NAV predictions page"""
    
    st.markdown("# 🤖 NAV Predictions")
    st.markdown("ML-powered NAV forecasting using XGBoost")
    st.markdown("---")
    
    # Check if scheme was selected from another page
    if st.session_state.get('selected_scheme_code'):
        render_prediction_for_selected_scheme()
    else:
        render_scheme_search()


def render_scheme_search():
    """Render scheme search with filters"""
    
    st.markdown("### 🔍 Search Scheme for NAV Prediction")
    
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
            key="prediction_quick_search"
        )
    
    with col2:
        limit = st.number_input("Results", min_value=5, max_value=100, value=20, key="prediction_quick_limit")
    
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
            key="prediction_filter_category",
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
            key="prediction_filter_amc"
        )
    
    with col3:
        limit = st.number_input(
            "Max Results",
            min_value=10,
            max_value=200,
            value=50,
            key="prediction_filter_limit"
        )
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("🔍 Apply Filters", use_container_width=True, type="primary", key="prediction_apply_filters"):
            apply_filters(selected_category, selected_amc, limit)
    
    with col2:
        if st.button("🔄 Reset", use_container_width=True, key="prediction_reset_filters"):
            if 'prediction_filtered_results' in st.session_state:
                del st.session_state['prediction_filtered_results']
            st.rerun()
    
    st.markdown("---")
    
    # Display results if available
    if 'prediction_filtered_results' in st.session_state:
        display_search_results(st.session_state['prediction_filtered_results'])
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
            
            st.session_state['prediction_filtered_results'] = filtered_results
            st.rerun()
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


def display_search_results(results: dict):
    """Display search results with table and card views"""
    
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
        key=f"prediction_view_type_{len(schemes_list)}"
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
        key=f"prediction_table_select_{len(schemes_list)}"
    )
    
    # Display selected scheme details
    if selected_idx is not None:
        display_scheme_details_and_predict(schemes_list[selected_idx])


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
            key=f"prediction_card_page_{len(schemes_list)}"
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
            
            # Action button
            if st.button("🤖 Predict NAV", key=f"card_predict_{card_idx}", use_container_width=True, type="primary"):
                navigate_to_prediction(scheme)


def navigate_to_prediction(scheme: dict):
    """Navigate to prediction with scheme selected"""
    st.session_state['selected_scheme_code'] = scheme['scheme_code']
    st.session_state['selected_scheme_name'] = scheme['scheme_name']
    st.rerun()


def display_scheme_details_and_predict(scheme: dict):
    """Display selected scheme details and prediction interface"""
    
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
    
    # Prediction button
    st.markdown("---")
    st.markdown("#### ⚡ Make Prediction")
    
    if st.button("🤖 Predict NAV", use_container_width=True, type="primary", key="action_predict"):
        navigate_to_prediction(scheme)


def render_prediction_for_selected_scheme():
    """Render prediction interface for selected scheme"""
    
    scheme_code = st.session_state['selected_scheme_code']
    scheme_name = st.session_state.get('selected_scheme_name', scheme_code)
    
    st.markdown(f"## {scheme_name}")
    st.markdown(f"**Scheme Code:** {scheme_code}")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("🔄 Change Scheme", use_container_width=True):
            st.session_state['selected_scheme_code'] = None
            st.session_state['selected_scheme_name'] = None
            st.rerun()
    
    st.markdown("---")
    
    # Prediction settings
    st.markdown("### ⚙️ Prediction Settings")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        forecast_days = st.slider(
            "Forecast Horizon (Days)",
            min_value=7,
            max_value=90,
            value=30,
            step=1,
            key="prediction_forecast_days"
        )
    
    with col2:
        st.write("")
        st.write("")
        st.write("")
        if st.button("🔮 Generate Prediction", use_container_width=True, type="primary", key="predict_generate_btn"):
            st.session_state['run_prediction'] = True
            st.rerun()
    
    with col3:
        st.metric("Model", "XGBoost")
        st.caption("Lookback: 60 days")
    
    # Run prediction
    if st.session_state.get('run_prediction'):
        render_predictions(scheme_code, forecast_days, scheme_name)


def render_predictions(scheme_code: str, forecast_days: int, scheme_name: str):
    """Generate and render predictions"""
    
    st.markdown("---")
    st.markdown("### 📊 Prediction Results")
    
    with st.spinner("🤖 Training ML model and generating predictions... This may take 30-60 seconds."):
        try:
            # Prepare prediction request data (as dict, not Pydantic model)
            pred_request_data = {
                "scheme_code": scheme_code,
                "forecast_days": forecast_days
            }
            
            # Call API with proper parameters
            pred_data = api.predict_nav(scheme_code, forecast_days)
            
            if not pred_data:
                st.error("❌ Unable to generate prediction. The scheme may not have enough historical data (need 200+ days).")
                st.session_state['run_prediction'] = False
                return
            
            # Display prediction summary
            st.markdown(f"#### {pred_data.get('scheme_name', scheme_name)}")
            
            col1, col2, col3 = st.columns(3)
            
            prediction = pred_data.get('prediction', {})
            
            with col1:
                st.metric(
                    "Current NAV",
                    f"₹{pred_data['current_nav']:.2f}",
                    help="Latest available NAV"
                )
            
            with col2:
                change_pct = prediction.get('change_percent', 0)
                delta_color = "normal" if change_pct >= 0 else "inverse"
                st.metric(
                    f"Predicted NAV ({forecast_days}d)",
                    f"₹{prediction.get('predicted_nav', 0):.2f}",
                    delta=f"{change_pct:.2f}%",
                    delta_color=delta_color,
                    help=f"Predicted NAV after {forecast_days} days"
                )
            
            with col3:
                confidence = pred_data.get('confidence', 'Medium')
                if confidence == 'High':
                    st.success(f"🎯 Confidence: {confidence}")
                elif confidence == 'Medium':
                    st.info(f"📊 Confidence: {confidence}")
                else:
                    st.warning(f"⚠️ Confidence: {confidence}")
            
            # Change metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Absolute Change", f"₹{prediction.get('change', 0):.2f}")
            
            with col2:
                st.metric("Prediction Date", prediction.get('date', 'N/A'))
            
            with col3:
                st.text("")
            
            # Get sequential predictions
            st.markdown("---")
            st.markdown("### 📈 Sequential Forecast (Next 7 Days)")
            
            with st.spinner("Generating day-by-day predictions..."):
                seq_data = api.predict_sequence(scheme_code, days=7)
                
                if seq_data and seq_data.get('predictions'):
                    render_sequential_predictions(seq_data, pred_data)
                else:
                    st.warning("Sequential predictions not available")
            
            # Reset prediction flag
            st.session_state['run_prediction'] = False
            
        except Exception as e:
            st.error(f"❌ Error generating predictions: {str(e)}")
            st.session_state['run_prediction'] = False


def render_sequential_predictions(seq_data: dict, pred_data: dict):
    """Render sequential predictions chart and table"""
    
    predictions = seq_data.get('predictions', [])
    if not predictions:
        st.warning("No sequential predictions available")
        return
    
    df_seq = pd.DataFrame(predictions)
    
    # Create interactive chart
    fig = go.Figure()
    
    # Add prediction line
    fig.add_trace(go.Scatter(
        x=df_seq['day'],
        y=df_seq['predicted_nav'],
        mode='lines+markers',
        name='Predicted NAV',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=10, symbol='circle'),
        hovertemplate='<b>Day %{x}</b><br>NAV: ₹%{y:.2f}<extra></extra>'
    ))
    
    # Add current NAV line
    fig.add_hline(
        y=seq_data.get('current_nav', 0),
        line_dash="dash",
        line_color="green",
        annotation_text="Current NAV",
        annotation_position="right"
    )
    
    # Add confidence bands (±5%)
    upper_band = df_seq['predicted_nav'] * 1.05
    lower_band = df_seq['predicted_nav'] * 0.95
    
    fig.add_trace(go.Scatter(
        x=df_seq['day'],
        y=upper_band,
        mode='lines',
        name='Upper Band (+5%)',
        line=dict(width=0),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    fig.add_trace(go.Scatter(
        x=df_seq['day'],
        y=lower_band,
        mode='lines',
        name='Lower Band (-5%)',
        line=dict(width=0),
        fillcolor='rgba(31, 119, 180, 0.2)',
        fill='tonexty',
        showlegend=True,
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        title=f"7-Day NAV Forecast - {seq_data.get('scheme_name', 'Scheme')}",
        xaxis_title="Days Ahead",
        yaxis_title="NAV (₹)",
        height=500,
        hovermode='x unified',
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Prediction table
    st.markdown("#### 📋 Day-by-Day Predictions")
    
    # Format table
    display_df = df_seq.copy()
    display_df['predicted_nav'] = display_df['predicted_nav'].round(2)
    display_df['change_percent'] = display_df['change_percent'].round(2)
    display_df['change_from_today'] = display_df['change_from_today'].round(2)
    
    st.dataframe(
        display_df[['day', 'predicted_nav', 'change_from_today', 'change_percent']],
        use_container_width=True,
        hide_index=True,
        column_config={
            "day": st.column_config.NumberColumn("Day", help="Days ahead"),
            "predicted_nav": st.column_config.NumberColumn("Predicted NAV (₹)", format="%.2f"),
            "change_from_today": st.column_config.NumberColumn("Change (₹)", format="%.2f"),
            "change_percent": st.column_config.NumberColumn("Change (%)", format="%.2f")
        }
    )
    
    # Download button
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Predictions CSV",
        data=csv,
        file_name=f"{seq_data.get('scheme_code', 'scheme')}_predictions.csv",
        mime="text/csv",
        key="prediction_download"
    )
    
    # Model info
    with st.expander("ℹ️ About the Prediction Model"):
        st.markdown("""
        **Model Architecture:** XGBoost Regressor
        
        **Features Used:**
        - Historical NAV values (60-day lookback)
        - Rolling statistics (mean, std, min, max)
        - Momentum indicators
        - Volatility measures
        - Time-based features (day of week, month)
        
        **Training Details:**
        - Model trained on scheme-specific historical data
        - Validation split: 20%
        - Feature engineering for time series patterns
        
        **Important Notes:**
        - ⚠️ Predictions are based solely on historical patterns
        - ⚠️ Cannot account for future market events
        - ⚠️ Accuracy decreases for longer time horizons
        - ⚠️ Use for educational purposes only
        - ⚠️ Not financial advice
        
        **Confidence Levels:**
        - **High:** Strong historical patterns, low volatility
        - **Medium:** Moderate patterns, average volatility
        - **Low:** Weak patterns, high volatility
        """)

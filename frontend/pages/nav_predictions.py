"""
NAV Predictions Page - ML-powered forecasting with proper state management
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
    
    st.info("⚠️ **Note:** Predictions are for educational purposes only. Past performance doesn't guarantee future results.")
    
    # Check if scheme selected from home page
    if st.session_state.get('selected_scheme_code'):
        render_prediction_for_selected_scheme()
    else:
        render_scheme_search()


def render_scheme_search():
    """Render scheme search interface"""
    
    st.markdown("### 🔍 Search Scheme for Prediction")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_query = st.text_input(
            "Search by scheme name or code",
            placeholder="e.g., HDFC, SBI, 119551",
            key="predict_search_input"
        )
    
    with col2:
        limit = st.number_input("Max Results", min_value=5, max_value=50, value=20, key="predict_search_limit")
    
    with col3:
        st.write("")
        st.write("")
        search_btn = st.button("🔍 Search", key="predict_search_btn", use_container_width=True)
    
    # Handle search
    if search_btn and search_query and len(search_query) >= 2:
        # Store search query to prevent rerun issues
        st.session_state['predict_last_search'] = search_query
        
        with st.spinner("🔍 Searching..."):
            results = api.search_schemes(search_query, limit)
            st.session_state['predict_search_results'] = results
    
    # Display stored results
    if st.session_state.get('predict_search_results'):
        results = st.session_state['predict_search_results']
        display_search_results_for_prediction(results)


def display_search_results_for_prediction(results: dict):
    """Display search results for prediction"""
    
    st.success(f"✅ Found {results['total_results']} schemes")
    
    schemes_list = results['schemes']
    
    if not schemes_list:
        st.warning("No schemes to display")
        return
    
    st.markdown("---")
    st.markdown("#### 📋 Select a Scheme")
    
    # Create selection options
    scheme_options = {}
    for scheme in schemes_list:
        display_text = f"{scheme['scheme_name'][:40]} - {scheme['scheme_code']}"
        scheme_options[display_text] = scheme
    
    # Display table first
    display_df = pd.DataFrame([
        {
            'Scheme Name': scheme['scheme_name'][:40],
            'Code': scheme['scheme_code'],
            'NAV': f"₹{scheme['current_nav']:.2f}",
            'AMC': scheme['amc'][:20],
            'Date': scheme['nav_date']
        }
        for scheme in schemes_list
    ])
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Select scheme using index (not changing key)
    selected_idx = st.selectbox(
        "Choose a scheme to predict:",
        options=range(len(schemes_list)),
        format_func=lambda x: f"{schemes_list[x]['scheme_name'][:40]} ({schemes_list[x]['scheme_code']})",
        key="predict_scheme_selectbox"
    )
    
    selected_scheme = schemes_list[selected_idx]
    selected_code = selected_scheme['scheme_code']
    
    # Show scheme info
    st.markdown("---")
    st.markdown("#### 📊 Selected Scheme")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Code", selected_code)
    with col2:
        st.metric("NAV", f"₹{selected_scheme['current_nav']:.2f}")
    with col3:
        st.metric("AMC", selected_scheme['amc'][:20])
    with col4:
        st.metric("Date", selected_scheme['nav_date'])
    
    # Select button (NOT rerun-triggering)
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Use This Scheme", use_container_width=True, type="primary", key="predict_select_btn"):
            st.session_state['selected_scheme_code'] = selected_code
            st.session_state['selected_scheme_name'] = selected_scheme['scheme_name']
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear Search", use_container_width=True, key="predict_clear_search"):
            st.session_state['predict_search_results'] = None
            st.session_state['predict_last_search'] = None
            st.rerun()


def render_prediction_for_selected_scheme():
    """Render prediction interface for selected scheme"""
    
    scheme_code = st.session_state['selected_scheme_code']
    scheme_name = st.session_state.get('selected_scheme_name', scheme_code)
    
    st.markdown(f"### 🎯 Selected Scheme: {scheme_name}")
    st.markdown(f"**Code:** {scheme_code}")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("🔄 Change Scheme", use_container_width=True, key="predict_change_scheme"):
            st.session_state['selected_scheme_code'] = None
            st.session_state['selected_scheme_name'] = None
            st.session_state['predict_search_results'] = None
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
            key="predict_forecast_days"
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
            # Get single prediction
            pred_data = api.predict_nav(scheme_code, forecast_days)
            
            if not pred_data:
                st.error("❌ Unable to generate prediction. The scheme may not have enough historical data (need 200+ days).")
                st.session_state['run_prediction'] = False
                return
            
            # Display prediction summary
            st.markdown(f"#### {pred_data['scheme_name']}")
            
            col1, col2, col3 = st.columns(3)
            
            prediction = pred_data['prediction']
            
            with col1:
                st.metric(
                    "Current NAV",
                    f"₹{pred_data['current_nav']:.2f}",
                    help="Latest available NAV"
                )
            
            with col2:
                change_pct = prediction['change_percent']
                delta_color = "normal" if change_pct >= 0 else "inverse"
                st.metric(
                    f"Predicted NAV ({forecast_days}d)",
                    f"₹{prediction['predicted_nav']:.2f}",
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
                st.metric("Absolute Change", f"₹{prediction['change']:.2f}")
            
            with col2:
                st.metric("Prediction Date", prediction['date'])
            
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
    
    predictions = seq_data['predictions']
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
        y=seq_data['current_nav'],
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
        title=f"7-Day NAV Forecast - {seq_data['scheme_name']}",
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
        file_name=f"{seq_data['scheme_code']}_predictions.csv",
        mime="text/csv",
        key="predict_download"
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

"""
FIXED Frontend Metrics Display
Shows ONLY real-time data with proper error handling
NO HARDCODING
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from frontend.utils.api_client import APIClient

api = APIClient()


def display_real_time_hero_metrics():
    """
    Display hero metrics with REAL data only
    Proper error handling - no fake fallbacks
    """
    
    st.markdown("### 📊 Real-time Market Statistics")
    
    with st.spinner("📊 Fetching real-time data..."):
        try:
            # Call new validated API endpoint
            stats = api._make_request(
                "GET",
                f"{api.api_v1}/market/statistics",
                show_error=False
            )
            
            if not stats:
                st.error("❌ Unable to fetch market data. Please check API connection.")
                return
            
            # Display REAL metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Schemes",
                    f"{stats['total_schemes']:,}",
                    help="Live count from AMFI data"
                )
            
            with col2:
                st.metric(
                    "Fund Houses (AMCs)",
                    f"{stats['total_amcs']}",
                    help="Unique AMCs in database"
                )
            
            with col3:
                st.metric(
                    "Categories",
                    f"{stats['total_categories']}",
                    help="Main fund categories"
                )
            
            with col4:
                st.metric(
                    "Latest NAV Date",
                    stats['latest_nav_date'],
                    help="Most recent data available"
                )
            
            # Show AUM if available (real data only)
            if stats.get('total_aum', {}).get('available'):
                st.markdown("---")
                col1, col2 = st.columns(2)
                
                with col1:
                    aum_value = stats['total_aum']['value_crores']
                    st.metric(
                        "Total Industry AUM",
                        f"₹{aum_value:,.0f} Crores",
                        help=stats['total_aum'].get('note', 'Real data')
                    )
                
                with col2:
                    st.info("💡 AUM data from verified external sources (updated weekly)")
            else:
                st.info("ℹ️ Real AUM data not available. Showing scheme counts instead.")
            
            # Data quality indicator
            st.caption(f"🕒 Last updated: {stats['last_updated']}")
        
        except Exception as e:
            st.error(f"❌ Error loading metrics: {str(e)}")
            st.info("💡 Tip: Ensure the backend API is running on http://localhost:8000")


def display_top_amcs_real_data():
    """
    Display top AMCs with REAL data
    Shows scheme count OR real AUM (not fake estimates)
    """
    
    st.markdown("### 🏢 Top Fund Houses")
    
    # Ranking type selector
    col1, col2 = st.columns([3, 1])
    
    with col2:
        ranking_type = st.selectbox(
            "Rank by:",
            options=["Scheme Count", "Real AUM"],
            key="amc_ranking_selector"
        )
    
    with st.spinner("Loading data..."):
        try:
            if ranking_type == "Real AUM":
                # Try to get real AUM data
                aum_data = api._make_request(
                    "GET",
                    f"{api.api_v1}/aum/top_amcs",
                    params={"limit": 10},
                    show_error=False
                )
                
                if aum_data and aum_data.get('available'):
                    # Display real AUM data
                    df_aum = pd.DataFrame(aum_data['data'])
                    
                    fig = go.Figure(data=[
                        go.Bar(
                            y=df_aum['amc'],
                            x=df_aum['aum_crores'],
                            orientation='h',
                            marker_color='#2ca02c',
                            text=[f"₹{val:,.0f} Cr" for val in df_aum['aum_crores']],
                            textposition='outside'
                        )
                    ])
                    
                    fig.update_layout(
                        title="Top 10 AMCs by Real AUM",
                        xaxis_title="AUM (₹ Crores)",
                        yaxis_title="AMC",
                        height=500,
                        yaxis={'categoryorder': 'total ascending'}
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    st.success(f"✅ {aum_data['note']}")
                
                else:
                    # Real AUM not available
                    st.warning("❌ Real AUM data not currently available")
                    st.info(aum_data.get('message', 'Data unavailable'))
                    st.info(f"💡 {aum_data.get('alternative', 'Use scheme count instead')}")
                    
                    # Fallback to scheme count
                    st.markdown("**Showing Scheme Count Ranking Instead:**")
                    display_scheme_count_ranking()
            
            else:
                # Show scheme count ranking
                display_scheme_count_ranking()
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


def display_scheme_count_ranking():
    """Display AMC ranking by scheme count (always available)"""
    
    try:
        # Fetch real scheme data
        search_results = api.search_schemes("Fund", limit=200)
        
        if not search_results or not search_results.get('schemes'):
            st.warning("Unable to load scheme data")
            return
        
        df = pd.DataFrame(search_results['schemes'])
        
        # Count schemes per AMC
        amc_counts = df['amc'].value_counts().head(10)
        
        fig = go.Figure(data=[
            go.Bar(
                y=amc_counts.index,
                x=amc_counts.values,
                orientation='h',
                marker_color='#1f77b4',
                text=[f"{val:,}" for val in amc_counts.values],
                textposition='outside'
            )
        ])
        
        fig.update_layout(
            title="Top 10 AMCs by Number of Schemes",
            xaxis_title="Number of Schemes",
            yaxis_title="AMC",
            height=500,
            yaxis={'categoryorder': 'total ascending'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.info("📌 **Note:** Ranked by number of schemes, not total AUM")
        st.caption("💡 More schemes ≠ larger AUM. This shows product diversity.")
    
    except Exception as e:
        st.error(f"Error: {str(e)}")


def display_prediction_with_confidence():
    """
    Display ML prediction with proper confidence scoring
    Shows model performance metrics
    """
    
    scheme_code = st.session_state.get('selected_scheme_code')
    
    if not scheme_code:
        st.warning("No scheme selected")
        return
    
    st.markdown("### 🤖 ML-Powered NAV Prediction")
    
    # Prediction settings
    col1, col2 = st.columns(2)
    
    with col1:
        forecast_days = st.slider(
            "Forecast Horizon (Days)",
            min_value=7,
            max_value=90,
            value=30,
            step=1
        )
    
    with col2:
        st.write("")
        st.write("")
        if st.button("🔮 Generate Prediction", type="primary"):
            generate_validated_prediction(scheme_code, forecast_days)


def generate_validated_prediction(scheme_code: str, forecast_days: int):
    """Generate prediction with validation and confidence scoring"""
    
    with st.spinner("🤖 Training model and validating... This may take 30-60 seconds."):
        try:
            # Call validated prediction endpoint
            result = api._make_request(
                "POST",
                f"{api.api_v1}/predict/validated",
                params={
                    "scheme_code": scheme_code,
                    "forecast_days": forecast_days
                },
                show_error=False
            )
            
            if not result:
                st.error("❌ Unable to generate prediction. API error.")
                return
            
            if not result.get('success'):
                # Show detailed error
                st.error(f"❌ {result.get('error', 'Prediction failed')}")
                
                if 'details' in result:
                    details = result['details']
                    st.warning(
                        f"**Data Insufficiency:** Need {details['required_days']} days, "
                        f"but only {details['available_days']} available."
                    )
                    st.info(details.get('message', ''))
                
                return
            
            # Display prediction results
            st.success(f"✅ Prediction generated for {result['scheme_name']}")
            
            # Show prediction
            st.markdown("#### 📊 Prediction Results")
            
            col1, col2, col3 = st.columns(3)
            
            prediction = result['prediction']
            
            with col1:
                st.metric("Current NAV", f"₹{result['current_nav']:.2f}")
            
            with col2:
                change_pct = prediction['change_percent']
                delta_color = "normal" if change_pct >= 0 else "inverse"
                st.metric(
                    f"Predicted NAV ({forecast_days}d)",
                    f"₹{prediction['predicted_nav']:.2f}",
                    delta=f"{change_pct:.2f}%",
                    delta_color=delta_color
                )
            
            with col3:
                # Confidence indicator with color
                confidence = result['model_performance']['confidence']
                if confidence == "High":
                    st.success(f"🎯 Confidence: {confidence}")
                elif confidence == "Medium":
                    st.info(f"📊 Confidence: {confidence}")
                else:
                    st.warning(f"⚠️ Confidence: {confidence}")
            
            # Show model performance
            st.markdown("---")
            st.markdown("#### 📈 Model Performance")
            
            perf = result['model_performance']
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Validation Error", perf['validation_mape'])
            
            with col2:
                st.metric("Directional Accuracy", perf['directional_accuracy'])
            
            with col3:
                st.metric("Training Samples", perf['training_samples'])
            
            with col4:
                st.metric("Validation Samples", perf['validation_samples'])
            
            # Show warnings if any
            if result.get('warnings'):
                st.markdown("---")
                st.markdown("#### ⚠️ Important Warnings")
                for warning in result['warnings']:
                    st.warning(warning)
            
            # Data quality info
            with st.expander("ℹ️ Data Quality & Model Details"):
                quality = result['data_quality']
                
                st.markdown(f"""
                **Historical Data:**
                - Total days: {quality['historical_days']}
                - Date range: {quality['date_range']['start']} to {quality['date_range']['end']}
                
                **Model Details:**
                - Algorithm: XGBoost Regressor
                - Features: 60-day lookback with technical indicators
                - Validation: Time-series cross-validation
                - Constraints: ±5% maximum change per prediction
                
                **Interpretation:**
                - **High Confidence**: MAPE < 2%, Good directional accuracy
                - **Medium Confidence**: MAPE 2-5%, Moderate accuracy
                - **Low Confidence**: MAPE > 5%, Use with caution
                """)
            
            # Disclaimer
            st.markdown("---")
            st.error("""
            **⚠️ IMPORTANT DISCLAIMER:**
            - This is a machine learning prediction based on historical patterns only
            - Cannot account for future market events, policy changes, or black swan events
            - NOT financial advice - consult a financial advisor before investing
            - Past performance does not guarantee future results
            - Use for educational purposes only
            """)
        
        except Exception as e:
            st.error(f"❌ Error generating prediction: {str(e)}")


# Export functions
__all__ = [
    'display_real_time_hero_metrics',
    'display_top_amcs_real_data',
    'display_prediction_with_confidence'
]
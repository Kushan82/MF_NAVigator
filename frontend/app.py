"""
MF_NAVigator - Streamlit Frontend
Main dashboard application
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# API Configuration
API_BASE_URL = "http://localhost:8000"
API_V1 = f"{API_BASE_URL}/api/v1"

# Page configuration
st.set_page_config(
    page_title="MF_NAVigator",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border-left: 5px solid #17a2b8;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/profit-report.png", width=80)
    st.markdown("# 📈 MF_NAVigator")
    st.markdown("---")
    
    # Navigation
    page = st.radio(
        "Navigation",
        ["🏠 Home", "📊 Scheme Analysis", "📈 Portfolio Builder", 
         "🤖 NAV Predictions", "⚖️ Compare Schemes"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # API Status
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            st.success("🟢 API Connected")
        else:
            st.error("🔴 API Error")
    except:
        st.error("🔴 API Offline")
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    **MF_NAVigator** is an AI-powered mutual fund analytics platform.
    
    **Features:**
    - 9,000+ Indian mutual funds
    - 23+ financial metrics
    - ML-powered predictions
    - Portfolio optimization
    """)
    
    st.markdown("---")
    st.markdown("**Version:** 1.0.0")
    st.markdown("**Tech:** Python, FastAPI, Streamlit, XGBoost")


# ==========================================
# PAGE: HOME
# ==========================================

if page == "🏠 Home":
    st.markdown('<div class="main-header">🚀 MF_NAVigator</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI-Powered Mutual Fund Analytics & Prediction Platform</div>', unsafe_allow_html=True)
    
    # Hero metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total Schemes", "9,000+", help="Indian mutual fund schemes")
    with col2:
        st.metric("📈 Metrics", "23+", help="Financial & risk metrics")
    with col3:
        st.metric("🤖 ML Models", "XGBoost", help="AI-powered predictions")
    with col4:
        st.metric("⚡ Real-time", "Live Data", help="Updated daily from AMFI")
    
    st.markdown("---")
    
    # Search Section
    st.markdown("### 🔍 Search Mutual Funds")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input(
            "Search by scheme name, AMC, or code",
            placeholder="e.g., HDFC, SBI, Axis..."
        )
    
    with col2:
        limit = st.number_input("Max Results", min_value=5, max_value=50, value=10)
    
    if search_query and len(search_query) >= 2:
        with st.spinner("Searching..."):
            try:
                response = requests.get(
                    f"{API_V1}/schemes/search",
                    params={"query": search_query, "limit": limit}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data['total_results'] > 0:
                        st.success(f"✅ Found {data['total_results']} schemes")
                        
                        # Convert to DataFrame
                        df = pd.DataFrame(data['schemes'])
                        
                        # Display as table
                        st.dataframe(
                            df[['scheme_name', 'amc', 'category', 'current_nav', 'nav_date']],
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Select scheme for quick analysis
                        st.markdown("---")
                        selected_scheme = st.selectbox(
                            "Select a scheme for quick view:",
                            options=df['scheme_code'].tolist(),
                            format_func=lambda x: df[df['scheme_code']==x]['scheme_name'].iloc[0]
                        )
                        
                        if selected_scheme:
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if st.button("📊 View Full Analysis", use_container_width=True):
                                    st.session_state['selected_scheme'] = selected_scheme
                                    st.rerun()
                            
                            with col2:
                                if st.button("🤖 Predict NAV", use_container_width=True):
                                    st.session_state['predict_scheme'] = selected_scheme
                                    st.rerun()
                    else:
                        st.warning("No schemes found. Try a different search term.")
                else:
                    st.error(f"Error: {response.status_code}")
            
            except Exception as e:
                st.error(f"Error connecting to API: {str(e)}")
    
    # Quick Stats
    st.markdown("---")
    st.markdown("### 📊 Platform Capabilities")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        #### 💰 Financial Metrics
        - CAGR (Compound Annual Growth Rate)
        - Sharpe Ratio
        - Sortino Ratio
        - Alpha & Beta
        - Information Ratio
        - Returns (1D, 1W, 1M, 3M, 6M, 1Y, 3Y, 5Y)
        """)
    
    with col2:
        st.markdown("""
        #### ⚠️ Risk Metrics
        - Volatility (Annualized)
        - Maximum Drawdown
        - Value at Risk (VaR)
        - Conditional VaR (CVaR)
        - Downside Deviation
        - Ulcer Index
        - Calmar Ratio
        """)
    
    with col3:
        st.markdown("""
        #### 🎯 Advanced Features
        - Portfolio Analysis
        - Scheme Comparison
        - NAV Predictions (ML)
        - Feature Importance
        - Correlation Matrix
        - Diversification Score
        - Historical Data Access
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>Built with ❤️ using Python, FastAPI, XGBoost, and Streamlit</p>
        <p>Data sources: AMFI India & MFapi.in</p>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# PAGE: SCHEME ANALYSIS
# ==========================================

elif page == "📊 Scheme Analysis":
    st.markdown("# 📊 Scheme Analysis")
    st.markdown("Detailed financial and risk analysis for any mutual fund scheme")
    st.markdown("---")
    
    # Scheme selection
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search = st.text_input("Search Scheme", placeholder="Enter scheme name or AMC")
    
    with col2:
        st.write("")  # Spacer
        search_btn = st.button("🔍 Search", use_container_width=True)
    
    # Search and select scheme
    if search and search_btn:
        try:
            response = requests.get(f"{API_V1}/schemes/search", params={"query": search, "limit": 20})
            
            if response.status_code == 200:
                data = response.json()
                
                if data['total_results'] > 0:
                    df = pd.DataFrame(data['schemes'])
                    
                    selected = st.selectbox(
                        "Select Scheme:",
                        options=df['scheme_code'].tolist(),
                        format_func=lambda x: df[df['scheme_code']==x]['scheme_name'].iloc[0]
                    )
                    
                    st.session_state['analysis_scheme'] = selected
                else:
                    st.warning("No schemes found")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # Analyze if scheme selected
    if 'analysis_scheme' in st.session_state:
        scheme_code = st.session_state['analysis_scheme']
        
        with st.spinner("Fetching comprehensive metrics..."):
            try:
                # Fetch comprehensive metrics
                response = requests.get(f"{API_V1}/metrics/comprehensive/{scheme_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Header
                    st.markdown(f"## {data['scheme_name']}")
                    st.markdown(f"**Scheme Code:** {data['scheme_code']}")
                    
                    st.markdown("---")
                    
                    # Key metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    fm = data['financial_metrics']
                    rm = data['risk_metrics']
                    
                    with col1:
                        st.metric("Current NAV", f"₹{fm['current_nav']:.2f}")
                    
                    with col2:
                        cagr = fm.get('cagr')
                        if cagr:
                            st.metric("CAGR", f"{cagr*100:.2f}%")
                        else:
                            st.metric("CAGR", "N/A")
                    
                    with col3:
                        sharpe = fm.get('sharpe_ratio')
                        if sharpe:
                            st.metric("Sharpe Ratio", f"{sharpe:.3f}")
                        else:
                            st.metric("Sharpe Ratio", "N/A")
                    
                    with col4:
                        st.metric("Volatility", f"{rm['volatility']*100:.2f}%")
                    
                    st.markdown("---")
                    
                    # Tabs for different metrics
                    tab1, tab2, tab3 = st.tabs(["📈 Returns", "⚠️ Risk Metrics", "📊 All Metrics"])
                    
                    with tab1:
                        st.markdown("### Returns Analysis")
                        
                        # Absolute returns
                        abs_ret = fm['absolute_returns']
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### Short-term Returns")
                            if abs_ret.get('1D'):
                                st.metric("1 Day", f"{abs_ret['1D']:.2f}%")
                            if abs_ret.get('1W'):
                                st.metric("1 Week", f"{abs_ret['1W']:.2f}%")
                            if abs_ret.get('1M'):
                                st.metric("1 Month", f"{abs_ret['1M']:.2f}%")
                            if abs_ret.get('3M'):
                                st.metric("3 Months", f"{abs_ret['3M']:.2f}%")
                        
                        with col2:
                            st.markdown("#### Long-term Returns")
                            if abs_ret.get('6M'):
                                st.metric("6 Months", f"{abs_ret['6M']:.2f}%")
                            if abs_ret.get('1Y'):
                                st.metric("1 Year", f"{abs_ret['1Y']:.2f}%")
                            if abs_ret.get('3Y'):
                                st.metric("3 Years", f"{abs_ret['3Y']:.2f}%")
                            if abs_ret.get('5Y'):
                                st.metric("5 Years", f"{abs_ret['5Y']:.2f}%")
                        
                        # Returns chart
                        returns_data = {k: v for k, v in abs_ret.items() if v and not pd.isna(v)}
                        
                        if returns_data:
                            fig = go.Figure(data=[
                                go.Bar(
                                    x=list(returns_data.keys()),
                                    y=list(returns_data.values()),
                                    marker_color='lightblue'
                                )
                            ])
                            
                            fig.update_layout(
                                title="Returns Across Time Periods",
                                xaxis_title="Period",
                                yaxis_title="Return (%)",
                                height=400
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                    
                    with tab2:
                        st.markdown("### Risk Analysis")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("Volatility (Annualized)", f"{rm['volatility']*100:.2f}%")
                            st.metric("Maximum Drawdown", f"{abs(rm['max_drawdown'])*100:.2f}%")
                            st.metric("Downside Deviation", f"{rm['downside_deviation']*100:.2f}%")
                            st.metric("Ulcer Index", f"{rm['ulcer_index']:.4f}")
                        
                        with col2:
                            st.metric("VaR (95%)", f"{rm['var_95']*100:.2f}%")
                            st.metric("CVaR (95%)", f"{rm['cvar_95']*100:.2f}%")
                            
                            calmar = rm.get('calmar_ratio')
                            if calmar and not pd.isna(calmar):
                                st.metric("Calmar Ratio", f"{calmar:.3f}")
                            else:
                                st.metric("Calmar Ratio", "N/A")
                    
                    with tab3:
                        st.markdown("### Complete Metrics Summary")
                        
                        # Create summary DataFrame
                        metrics_summary = []
                        
                        # Financial metrics
                        metrics_summary.append(["Current NAV", f"₹{fm['current_nav']:.2f}"])
                        
                        if fm.get('cagr'):
                            metrics_summary.append(["CAGR", f"{fm['cagr']*100:.2f}%"])
                        
                        metrics_summary.append(["Annualized Return", f"{fm['annualized_return']*100:.2f}%"])
                        
                        if fm.get('sharpe_ratio'):
                            metrics_summary.append(["Sharpe Ratio", f"{fm['sharpe_ratio']:.3f}"])
                        
                        if fm.get('sortino_ratio'):
                            metrics_summary.append(["Sortino Ratio", f"{fm['sortino_ratio']:.3f}"])
                        
                        # Risk metrics
                        metrics_summary.append(["Volatility", f"{rm['volatility']*100:.2f}%"])
                        metrics_summary.append(["Max Drawdown", f"{abs(rm['max_drawdown'])*100:.2f}%"])
                        metrics_summary.append(["Downside Deviation", f"{rm['downside_deviation']*100:.2f}%"])
                        metrics_summary.append(["VaR (95%)", f"{rm['var_95']*100:.2f}%"])
                        metrics_summary.append(["CVaR (95%)", f"{rm['cvar_95']*100:.2f}%"])
                        
                        df_summary = pd.DataFrame(metrics_summary, columns=["Metric", "Value"])
                        
                        st.dataframe(df_summary, use_container_width=True, hide_index=True)
                    
                else:
                    st.error(f"Error fetching data: {response.status_code}")
            
            except Exception as e:
                st.error(f"Error: {str(e)}")


# ==========================================
# PAGE: PORTFOLIO BUILDER
# ==========================================

elif page == "📈 Portfolio Builder":
    st.markdown("# 📈 Portfolio Builder")
    st.markdown("Create and analyze multi-scheme portfolios")
    st.markdown("---")
    
    # Initialize session state
    if 'portfolio_schemes' not in st.session_state:
        st.session_state['portfolio_schemes'] = []
    
    # Add scheme to portfolio
    st.markdown("### Add Schemes to Portfolio")
    
    col1, col2, col3 = st.columns([3, 2, 1])
    
    with col1:
        search = st.text_input("Search Scheme", key="portfolio_search")
    
    with col2:
        weight = st.number_input("Weight (%)", min_value=1, max_value=100, value=20, key="portfolio_weight")
    
    with col3:
        st.write("")  # Spacer
        add_btn = st.button("➕ Add", use_container_width=True)
    
    # Search and add
    if search and add_btn:
        try:
            response = requests.get(f"{API_V1}/schemes/search", params={"query": search, "limit": 10})
            
            if response.status_code == 200:
                data = response.json()
                
                if data['total_results'] > 0:
                    df = pd.DataFrame(data['schemes'])
                    
                    selected = st.selectbox(
                        "Select to add:",
                        options=df['scheme_code'].tolist(),
                        format_func=lambda x: df[df['scheme_code']==x]['scheme_name'].iloc[0],
                        key="portfolio_select"
                    )
                    
                    if st.button("✅ Confirm Add"):
                        scheme_name = df[df['scheme_code']==selected]['scheme_name'].iloc[0]
                        st.session_state['portfolio_schemes'].append({
                            'code': selected,
                            'name': scheme_name,
                            'weight': weight / 100.0
                        })
                        st.success(f"Added {scheme_name}")
                        st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # Display current portfolio
    if st.session_state['portfolio_schemes']:
        st.markdown("---")
        st.markdown("### Current Portfolio")
        
        portfolio_df = pd.DataFrame(st.session_state['portfolio_schemes'])
        total_weight = portfolio_df['weight'].sum()
        
        # Display portfolio
        st.dataframe(
            portfolio_df.assign(weight_pct=portfolio_df['weight']*100)[['name', 'code', 'weight_pct']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "name": "Scheme Name",
                "code": "Code",
                "weight_pct": st.column_config.NumberColumn("Weight (%)", format="%.2f")
            }
        )
        
        # Weight validation
        if abs(total_weight - 1.0) > 0.01:
            st.warning(f"⚠️ Total weight: {total_weight*100:.1f}%. Should be 100%.")
        else:
            st.success("✅ Portfolio weights sum to 100%")
        
        # Actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🗑️ Clear Portfolio", use_container_width=True):
                st.session_state['portfolio_schemes'] = []
                st.rerun()
        
        with col2:
            analyze_btn = st.button("📊 Analyze Portfolio", use_container_width=True, 
                                    disabled=(abs(total_weight - 1.0) > 0.01))
        
        with col3:
            if st.button("💾 Save Portfolio", use_container_width=True):
                st.info("Portfolio save feature coming soon!")
        
        # Analyze portfolio
        if analyze_btn:
            st.markdown("---")
            st.markdown("### Portfolio Analysis")
            
            with st.spinner("Analyzing portfolio..."):
                try:
                    # Prepare request
                    schemes = [
                        {"scheme_code": s['code'], "weight": s['weight']}
                        for s in st.session_state['portfolio_schemes']
                    ]
                    
                    response = requests.post(
                        f"{API_V1}/portfolio/analyze",
                        json={"schemes": schemes}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Display metrics
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Annual Return", f"{data['annualized_return']*100:.2f}%")
                        
                        with col2:
                            st.metric("Volatility", f"{data['volatility']*100:.2f}%")
                        
                        with col3:
                            st.metric("Sharpe Ratio", f"{data['sharpe_ratio']:.3f}")
                        
                        with col4:
                            st.metric("Diversification", f"{data['diversification_score']:.3f}")
                        
                        st.markdown("---")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Sortino Ratio", f"{data['sortino_ratio']:.3f}")
                        
                        with col2:
                            st.metric("Max Drawdown", f"{abs(data['max_drawdown'])*100:.2f}%")
                        
                        with col3:
                            st.metric("VaR (95%)", f"{data['var_95']*100:.2f}%")
                        
                        # Risk-Return Chart
                        st.markdown("---")
                        st.markdown("#### Portfolio Composition")
                        
                        fig = go.Figure(data=[go.Pie(
                            labels=[s['name'] for s in st.session_state['portfolio_schemes']],
                            values=[s['weight'] for s in st.session_state['portfolio_schemes']],
                            hole=.3
                        )])
                        
                        fig.update_layout(title="Portfolio Allocation", height=400)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    else:
                        st.error(f"Error: {response.status_code} - {response.text}")
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    else:
        st.info("👆 Add schemes to your portfolio to get started")


# ==========================================
# PAGES: NAV PREDICTIONS & COMPARE
# ==========================================

elif page == "🤖 NAV Predictions":
    st.markdown("# 🤖 NAV Predictions")
    st.markdown("ML-powered NAV forecasting using XGBoost")
    st.markdown("---")
    
    st.info("⚠️ **Note:** Predictions are for educational purposes only. Past performance doesn't guarantee future results.")
    
    # Scheme selection
    search = st.text_input("Search Scheme for Prediction", placeholder="Enter scheme name")
    
    if search:
        try:
            response = requests.get(f"{API_V1}/schemes/search", params={"query": search, "limit": 10})
            
            if response.status_code == 200:
                data = response.json()
                
                if data['total_results'] > 0:
                    df = pd.DataFrame(data['schemes'])
                    
                    selected = st.selectbox(
                        "Select Scheme:",
                        options=df['scheme_code'].tolist(),
                        format_func=lambda x: df[df['scheme_code']==x]['scheme_name'].iloc[0]
                    )
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        forecast_days = st.slider("Forecast Days", 1, 90, 30)
                    
                    with col2:
                        st.write("")  # Spacer
                        predict_btn = st.button("🔮 Predict", use_container_width=True)
                    
                    if predict_btn:
                        st.markdown("---")
                        
                        with st.spinner("Training ML model and generating predictions..."):
                            try:
                                # Single prediction
                                response = requests.post(
                                    f"{API_V1}/predict/single",
                                    json={"scheme_code": selected, "forecast_days": forecast_days}
                                )
                                
                                if response.status_code == 200:
                                    pred_data = response.json()
                                    
                                    st.markdown(f"### {pred_data['scheme_name']}")
                                    
                                    col1, col2, col3 = st.columns(3)
                                    
                                    with col1:
                                        st.metric("Current NAV", f"₹{pred_data['current_nav']:.2f}")
                                    
                                    with col2:
                                        st.metric(
                                            f"Predicted NAV ({forecast_days}d)",
                                            f"₹{pred_data['prediction']['predicted_nav']:.2f}",
                                            f"{pred_data['prediction']['change_percent']:.2f}%"
                                        )
                                    
                                    with col3:
                                        st.metric("Confidence", pred_data['confidence'])
                                    
                                    # Sequential predictions
                                    st.markdown("---")
                                    st.markdown("### 7-Day Sequential Forecast")
                                    
                                    response2 = requests.post(
                                        f"{API_V1}/predict/sequence?scheme_code={selected}&days=7"
                                    )
                                    
                                    if response2.status_code == 200:
                                        seq_data = response2.json()
                                        
                                        df_seq = pd.DataFrame(seq_data['predictions'])
                                        
                                        # Chart
                                        fig = go.Figure()
                                        
                                        fig.add_trace(go.Scatter(
                                            x=df_seq['day'],
                                            y=df_seq['predicted_nav'],
                                            mode='lines+markers',
                                            name='Predicted NAV',
                                            line=dict(color='blue', width=2)
                                        ))
                                        
                                        fig.add_hline(
                                            y=seq_data['current_nav'],
                                            line_dash="dash",
                                            line_color="green",
                                            annotation_text="Current NAV"
                                        )
                                        
                                        fig.update_layout(
                                            title="7-Day NAV Forecast",
                                            xaxis_title="Day",
                                            yaxis_title="NAV (₹)",
                                            height=400
                                        )
                                        
                                        st.plotly_chart(fig, use_container_width=True)
                                        
                                        # Table
                                        st.dataframe(
                                            df_seq[['day', 'predicted_nav', 'change_percent']],
                                            use_container_width=True,
                                            hide_index=True,
                                            column_config={
                                                "day": "Day",
                                                "predicted_nav": st.column_config.NumberColumn("Predicted NAV (₹)", format="%.2f"),
                                                "change_percent": st.column_config.NumberColumn("Change (%)", format="%.2f")
                                            }
                                        )
                                
                                else:
                                    st.error(f"Prediction failed: {response.status_code}")
                            
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
        
        except Exception as e:
            st.error(f"Error: {str(e)}")

elif page == "⚖️ Compare Schemes":
    st.markdown("# ⚖️ Compare Schemes")
    st.markdown("Side-by-side comparison of multiple mutual funds")
    st.markdown("---")
    
    # Initialize comparison list
    if 'compare_schemes' not in st.session_state:
        st.session_state['compare_schemes'] = []
    
    # Add schemes
    col1, col2 = st.columns([4, 1])
    
    with col1:
        search = st.text_input("Search and add schemes to compare", key="compare_search")
    
    with col2:
        st.write("")  # Spacer
        add_btn = st.button("➕ Add", use_container_width=True)
    
    if search and add_btn:
        try:
            response = requests.get(f"{API_V1}/schemes/search", params={"query": search, "limit": 10})
            
            if response.status_code == 200:
                data = response.json()
                
                if data['total_results'] > 0:
                    df = pd.DataFrame(data['schemes'])
                    
                    selected = st.selectbox(
                        "Select to add:",
                        options=df['scheme_code'].tolist(),
                        format_func=lambda x: df[df['scheme_code']==x]['scheme_name'].iloc[0],
                        key="compare_select"
                    )
                    
                    if st.button("✅ Add to Comparison"):
                        if selected not in st.session_state['compare_schemes']:
                            st.session_state['compare_schemes'].append(selected)
                            st.success("Scheme added!")
                            st.rerun()
                        else:
                            st.warning("Scheme already in comparison")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # Display and compare
    if len(st.session_state['compare_schemes']) >= 2:
        st.markdown("---")
        st.markdown(f"### Comparing {len(st.session_state['compare_schemes'])} Schemes")
        
        # Show list
        for i, code in enumerate(st.session_state['compare_schemes']):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.text(f"{i+1}. {code}")
            with col2:
                if st.button("🗑️", key=f"remove_{i}"):
                    st.session_state['compare_schemes'].remove(code)
                    st.rerun()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Compare Now", use_container_width=True):
                st.session_state['run_comparison'] = True
                st.rerun()
        
        with col2:
            if st.button("🗑️ Clear All", use_container_width=True):
                st.session_state['compare_schemes'] = []
                st.rerun()
        
        # Run comparison
        if st.session_state.get('run_comparison', False):
            st.markdown("---")
            
            with st.spinner("Comparing schemes..."):
                try:
                    response = requests.post(
                        f"{API_V1}/portfolio/compare",
                        json=st.session_state['compare_schemes']
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Create comparison DataFrame
                        df_compare = pd.DataFrame(data['schemes'])
                        
                        st.dataframe(
                            df_compare[['scheme', 'current_nav', 'cagr', 'return_1y', 
                                       'volatility', 'max_drawdown', 'sharpe_ratio']],
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "scheme": "Scheme Name",
                                "current_nav": st.column_config.NumberColumn("Current NAV", format="₹%.2f"),
                                "cagr": st.column_config.NumberColumn("CAGR (%)", format="%.2f"),
                                "return_1y": st.column_config.NumberColumn("1Y Return (%)", format="%.2f"),
                                "volatility": st.column_config.NumberColumn("Volatility (%)", format="%.2f"),
                                "max_drawdown": st.column_config.NumberColumn("Max DD (%)", format="%.2f"),
                                "sharpe_ratio": st.column_config.NumberColumn("Sharpe", format="%.3f")
                            }
                        )
                        
                        st.markdown("---")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.success(f"🏆 **Best by Sharpe Ratio:** {data['best_by_sharpe']}")
                        
                        with col2:
                            st.success(f"📈 **Best by Returns:** {data['best_by_return']}")
                        
                        # Comparison charts
                        st.markdown("---")
                        st.markdown("### Visual Comparison")
                        
                        # Returns chart
                        fig = go.Figure(data=[
                            go.Bar(
                                name='CAGR',
                                x=df_compare['scheme'],
                                y=df_compare['cagr'],
                                marker_color='lightblue'
                            ),
                            go.Bar(
                                name='1Y Return',
                                x=df_compare['scheme'],
                                y=df_compare['return_1y'],
                                marker_color='lightgreen'
                            )
                        ])
                        
                        fig.update_layout(
                            title="Returns Comparison",
                            xaxis_title="Scheme",
                            yaxis_title="Return (%)",
                            barmode='group',
                            height=400
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Risk chart
                        fig2 = go.Figure(data=[
                            go.Bar(
                                x=df_compare['scheme'],
                                y=df_compare['volatility'],
                                name='Volatility',
                                marker_color='orange'
                            )
                        ])
                        
                        fig2.update_layout(
                            title="Volatility Comparison",
                            xaxis_title="Scheme",
                            yaxis_title="Volatility (%)",
                            height=400
                        )
                        
                        st.plotly_chart(fig2, use_container_width=True)
                    
                    else:
                        st.error(f"Comparison failed: {response.status_code}")
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    else:
        st.info("👆 Add at least 2 schemes to compare")

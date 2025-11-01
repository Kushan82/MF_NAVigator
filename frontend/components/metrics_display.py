"""
Reusable components for displaying metrics
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def display_hero_metrics():
    """Display hero metrics on home page"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total Schemes", "9,000+", help="Indian mutual fund schemes")
    
    with col2:
        st.metric("📈 Metrics", "23+", help="Financial & risk metrics")
    
    with col3:
        st.metric("🤖 ML Models", "XGBoost", help="AI-powered predictions")
    
    with col4:
        st.metric("⚡ Real-time", "Live Data", help="Updated daily from AMFI")


def display_key_metrics(data: dict):
    """Display key metrics for a scheme"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    fm = data['financial_metrics']
    rm = data['risk_metrics']
    
    with col1:
        st.metric("Current NAV", f"₹{fm['current_nav']:.2f}")
    
    with col2:
        cagr = fm.get('cagr')
        if cagr and not pd.isna(cagr):
            st.metric("CAGR", f"{cagr*100:.2f}%")
        else:
            st.metric("CAGR", "N/A")
    
    with col3:
        sharpe = fm.get('sharpe_ratio')
        if sharpe and not pd.isna(sharpe):
            st.metric("Sharpe Ratio", f"{sharpe:.3f}")
        else:
            st.metric("Sharpe Ratio", "N/A")
    
    with col4:
        st.metric("Volatility", f"{rm['volatility']*100:.2f}%")


def display_returns_chart(abs_returns: dict):
    """Display returns bar chart"""
    
    # Filter valid returns
    returns_data = {
        k: v for k, v in abs_returns.items()
        if v is not None and not pd.isna(v)
    }
    
    if not returns_data:
        st.warning("No return data available")
        return
    
    fig = go.Figure(data=[
        go.Bar(
            x=list(returns_data.keys()),
            y=list(returns_data.values()),
            marker_color=['green' if v >= 0 else 'red' for v in returns_data.values()]
        )
    ])
    
    fig.update_layout(
        title="Returns Across Time Periods",
        xaxis_title="Period",
        yaxis_title="Return (%)",
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_metric_card(title: str, value: str, delta: str = None, help_text: str = None):
    """Display a custom metric card"""
    
    st.markdown(f"""
    <div class="metric-card">
        <h4>{title}</h4>
        <h2>{value}</h2>
        {f'<p style="color: {"green" if "+" in str(delta) else "red"}">{delta}</p>' if delta else ''}
        {f'<small>{help_text}</small>' if help_text else ''}
    </div>
    """, unsafe_allow_html=True)

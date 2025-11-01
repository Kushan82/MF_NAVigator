"""
Scheme Analysis Page - Detailed metrics for a single scheme
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from frontend.utils.api_client import APIClient
from frontend.components.metrics_display import display_key_metrics, display_returns_chart
from frontend.components.search import render_scheme_search

api = APIClient()

def render():
    """Render scheme analysis page"""
    
    st.markdown("# 📊 Scheme Analysis")
    st.markdown("Detailed financial and risk analysis for any mutual fund scheme")
    st.markdown("---")
    
    # Scheme selection
    selected_scheme = render_scheme_search(key_prefix="analysis")
    
    if selected_scheme:
        st.session_state['analysis_scheme'] = selected_scheme
    
    # Analyze if scheme selected
    if 'analysis_scheme' in st.session_state:
        scheme_code = st.session_state['analysis_scheme']
        render_scheme_details(scheme_code)


def render_scheme_details(scheme_code: str):
    """Render detailed scheme analysis"""
    
    with st.spinner("Fetching comprehensive metrics..."):
        try:
            # Fetch comprehensive metrics
            data = api.get_comprehensive_metrics(scheme_code)
            
            if not data:
                st.error("Unable to fetch scheme data")
                return
            
            # Header
            st.markdown(f"## {data['scheme_name']}")
            st.markdown(f"**Scheme Code:** {data['scheme_code']}")
            st.markdown("---")
            
            # Key metrics row
            display_key_metrics(data)
            
            st.markdown("---")
            
            # Tabs for different metrics
            render_metric_tabs(data)
            
            # Historical data section
            st.markdown("---")
            render_historical_section(scheme_code)
            
        except Exception as e:
            st.error(f"Error: {str(e)}")


def render_metric_tabs(data: dict):
    """Render metric tabs"""
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Returns", 
        "⚠️ Risk Metrics", 
        "📊 All Metrics",
        "📉 Visualizations"
    ])
    
    with tab1:
        render_returns_tab(data['financial_metrics'])
    
    with tab2:
        render_risk_tab(data['risk_metrics'])
    
    with tab3:
        render_all_metrics_tab(data)
    
    with tab4:
        render_visualizations_tab(data)


def render_returns_tab(fm: dict):
    """Render returns analysis tab"""
    
    st.markdown("### Returns Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Short-term Returns")
        abs_ret = fm['absolute_returns']
        
        for period in ['1D', '1W', '1M', '3M']:
            if abs_ret.get(period) and not pd.isna(abs_ret[period]):
                delta_color = "normal" if abs_ret[period] >= 0 else "inverse"
                st.metric(
                    period.replace('D', ' Day').replace('W', ' Week').replace('M', ' Month'),
                    f"{abs_ret[period]:.2f}%",
                    delta=None,
                    delta_color=delta_color
                )
    
    with col2:
        st.markdown("#### Long-term Returns")
        
        for period in ['6M', '1Y', '3Y', '5Y']:
            if abs_ret.get(period) and not pd.isna(abs_ret[period]):
                delta_color = "normal" if abs_ret[period] >= 0 else "inverse"
                st.metric(
                    period.replace('M', ' Months').replace('Y', ' Year').replace('3', '3 ').replace('5', '5 '),
                    f"{abs_ret[period]:.2f}%",
                    delta=None,
                    delta_color=delta_color
                )
    
    # Returns chart
    st.markdown("---")
    display_returns_chart(abs_ret)


def render_risk_tab(rm: dict):
    """Render risk metrics tab"""
    
    st.markdown("### Risk Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Volatility (Annual)", f"{rm['volatility']*100:.2f}%")
        st.metric("Downside Deviation", f"{rm['downside_deviation']*100:.2f}%")
    
    with col2:
        st.metric("Maximum Drawdown", f"{abs(rm['max_drawdown'])*100:.2f}%")
        st.metric("Ulcer Index", f"{rm['ulcer_index']:.4f}")
    
    with col3:
        st.metric("VaR (95%)", f"{rm['var_95']*100:.2f}%")
        st.metric("CVaR (95%)", f"{rm['cvar_95']*100:.2f}%")
    
    # Risk explanation
    with st.expander("ℹ️ Understanding Risk Metrics"):
        st.markdown("""
        **Volatility:** Measures price fluctuations. Higher = more risky.
        
        **Maximum Drawdown:** Largest peak-to-trough decline. Shows worst-case scenario.
        
        **VaR (Value at Risk):** Expected loss in worst 5% of scenarios.
        
        **CVaR (Conditional VaR):** Average loss beyond VaR threshold.
        
        **Ulcer Index:** Measures severity and duration of drawdowns.
        """)


def render_all_metrics_tab(data: dict):
    """Render all metrics summary"""
    
    st.markdown("### Complete Metrics Summary")
    
    fm = data['financial_metrics']
    rm = data['risk_metrics']
    
    # Create comprehensive summary
    metrics_data = []
    
    # Financial metrics
    metrics_data.append(["📊 Financial Metrics", ""])
    metrics_data.append(["Current NAV", f"₹{fm['current_nav']:.2f}"])
    
    if fm.get('cagr') and not pd.isna(fm['cagr']):
        metrics_data.append(["CAGR", f"{fm['cagr']*100:.2f}%"])
    
    metrics_data.append(["Annualized Return", f"{fm['annualized_return']*100:.2f}%"])
    
    if fm.get('sharpe_ratio') and not pd.isna(fm['sharpe_ratio']):
        metrics_data.append(["Sharpe Ratio", f"{fm['sharpe_ratio']:.3f}"])
    
    if fm.get('sortino_ratio') and not pd.isna(fm['sortino_ratio']):
        metrics_data.append(["Sortino Ratio", f"{fm['sortino_ratio']:.3f}"])
    
    # Risk metrics
    metrics_data.append(["", ""])
    metrics_data.append(["⚠️ Risk Metrics", ""])
    metrics_data.append(["Volatility", f"{rm['volatility']*100:.2f}%"])
    metrics_data.append(["Max Drawdown", f"{abs(rm['max_drawdown'])*100:.2f}%"])
    metrics_data.append(["Downside Deviation", f"{rm['downside_deviation']*100:.2f}%"])
    metrics_data.append(["VaR (95%)", f"{rm['var_95']*100:.2f}%"])
    metrics_data.append(["CVaR (95%)", f"{rm['cvar_95']*100:.2f}%"])
    
    if rm.get('calmar_ratio') and not pd.isna(rm['calmar_ratio']):
        metrics_data.append(["Calmar Ratio", f"{rm['calmar_ratio']:.3f}"])
    
    df_summary = pd.DataFrame(metrics_data, columns=["Metric", "Value"])
    
    st.dataframe(
        df_summary,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Metric": st.column_config.TextColumn("Metric", width="large"),
            "Value": st.column_config.TextColumn("Value", width="medium")
        }
    )
    
    # Export button
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        csv = df_summary.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"{data['scheme_code']}_metrics.csv",
            mime="text/csv"
        )
    
    with col2:
        if st.button("📋 Copy to Clipboard"):
            st.info("Copy functionality coming soon!")


def render_visualizations_tab(data: dict):
    """Render visualization tab"""
    
    st.markdown("### Performance Visualizations")
    
    # Risk-Return scatter (placeholder for future implementation)
    st.info("🚧 Advanced visualizations coming soon!")
    st.markdown("""
    **Planned visualizations:**
    - Risk-Return scatter plot
    - Rolling performance chart
    - Drawdown timeline
    - Comparison with benchmark
    """)


def render_historical_section(scheme_code: str):
    """Render historical data section"""
    
    st.markdown("### 📊 Historical NAV Data")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        limit = st.number_input("Records to fetch", min_value=10, max_value=365, value=90)
    
    with col2:
        if st.button("📥 Fetch Historical Data", use_container_width=True):
            st.session_state['fetch_historical'] = True
    
    if st.session_state.get('fetch_historical'):
        with st.spinner("Fetching historical data..."):
            hist_data = api.get_historical_data(scheme_code, limit=limit)
            
            if hist_data:
                df = pd.DataFrame(hist_data['data'])
                
                # Display chart
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df['date'],
                    y=df['nav'],
                    mode='lines',
                    name='NAV',
                    line=dict(color='blue', width=2)
                ))
                
                fig.update_layout(
                    title=f"NAV History - {hist_data['scheme_name']}",
                    xaxis_title="Date",
                    yaxis_title="NAV (₹)",
                    height=400,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display table
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "date": "Date",
                        "nav": st.column_config.NumberColumn("NAV (₹)", format="%.4f")
                    }
                )
                
                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Historical Data",
                    data=csv,
                    file_name=f"{scheme_code}_historical.csv",
                    mime="text/csv"
                )
            else:
                st.error("Unable to fetch historical data")

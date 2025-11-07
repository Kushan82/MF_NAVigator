"""
Compare Schemes Page - Side-by-side comparison with advanced Plotly visualizations
COMPLETE FIX: No timeout, no unnecessary reruns, keeps all Plotly charts
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from frontend.utils.api_client import APIClient
import numpy as np

api = APIClient()


def render():
    """Render compare schemes page with enhanced visualizations"""
    
    st.markdown("# ⚖️ Compare Schemes")
    st.markdown("Side-by-side comparison with advanced analytics")
    st.markdown("---")
    
    # Initialize compare list if doesn't exist
    if 'compare_schemes_list' not in st.session_state:
        st.session_state['compare_schemes_list'] = []
    
    # Initialize show_add_form flag
    if 'show_compare_add_form' not in st.session_state:
        st.session_state['show_compare_add_form'] = False
    
    # Display current list or add interface
    if len(st.session_state['compare_schemes_list']) > 0:
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
    
    # Store search results in session state to prevent loss on rerun
    if search_btn and search_query and len(search_query) >= 2:
        with st.spinner("🔍 Searching..."):
            results = api.search_schemes(search_query, limit)
            if results and results.get('total_results', 0) > 0:
                st.session_state['compare_search_results'] = results
                st.rerun()
            else:
                st.warning("No schemes found")
    
    # Display stored search results
    if st.session_state.get('compare_search_results'):
        display_search_results_for_add(st.session_state['compare_search_results'])


def display_search_results_for_add(results: dict):
    """Display search results for adding to comparison"""
    
    st.success(f"✅ Found {results['total_results']} schemes")
    
    schemes_list = results['schemes']
    
    # Create selection options
    scheme_options = {}
    for scheme in schemes_list:
        display_text = f"{scheme['scheme_name'][:40]} - {scheme['scheme_code']} ({scheme['amc'][:15]})"
        scheme_options[display_text] = scheme
    
    # Initialize selected index in session state to prevent reset
    if 'compare_selected_idx' not in st.session_state:
        st.session_state['compare_selected_idx'] = 0
    
    # Select scheme with persistent index
    selected_idx = st.selectbox(
        "Choose a scheme to add:",
        options=range(len(schemes_list)),
        index=st.session_state['compare_selected_idx'],
        format_func=lambda x: f"{schemes_list[x]['scheme_name'][:40]} - {schemes_list[x]['scheme_code']} ({schemes_list[x]['amc'][:15]})",
        key=f"compare_add_selector_{results['total_results']}"
    )
    
    # Update session state
    st.session_state['compare_selected_idx'] = selected_idx
    
    selected_scheme = schemes_list[selected_idx]
    selected_code = selected_scheme['scheme_code']
    
    # Display info
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Code", selected_code)
    with col2:
        st.metric("NAV", f"₹{selected_scheme['current_nav']:.2f}")
    with col3:
        st.metric("AMC", selected_scheme['amc'][:20])
    with col4:
        st.metric("Date", selected_scheme['nav_date'])
    
    # Add buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Add to Comparison", use_container_width=True, type="primary", key="compare_add_btn"):
            if selected_code not in st.session_state['compare_schemes_list']:
                st.session_state['compare_schemes_list'].append(selected_code)
                st.success(f"✅ Added! Total: {len(st.session_state['compare_schemes_list'])}")
                # DON'T RERUN HERE - just show success message
            else:
                st.warning("⚠️ Already in comparison list")
    
    with col2:
        if st.button("🔄 Add & Search More", use_container_width=True, key="compare_add_continue"):
            if selected_code not in st.session_state['compare_schemes_list']:
                st.session_state['compare_schemes_list'].append(selected_code)
            # Clear search to allow new search
            st.session_state['compare_search_results'] = None
            st.session_state['compare_selected_idx'] = 0
            st.rerun()
    
    with col3:
        if st.button("❌ Cancel", use_container_width=True, key="compare_cancel_btn"):
            st.session_state['compare_search_results'] = None
            st.session_state['compare_selected_idx'] = 0
            st.rerun()


def render_comparison_interface():
    """Render comparison interface with persistent list"""
    
    st.markdown(f"### 📊 Schemes Selected ({len(st.session_state['compare_schemes_list'])})")
    
    # Display current list with actions
    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
    col1.write("**Scheme Code**")
    col2.write("**View**")
    col3.write("**Predict**")
    col4.write("**Portfolio**")
    col5.write("**Remove**")
    
    st.markdown("---")
    
    for i, code in enumerate(st.session_state['compare_schemes_list']):
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
        
        with col1:
            st.text(f"{i+1}. {code}")
        
        with col2:
            if st.button("📊", key=f"comp_view_{i}_{code}", help="View Details"):
                st.session_state['selected_scheme_code'] = code
                st.session_state['navigate_to'] = '📊 Scheme Analysis'
                st.rerun()
        
        with col3:
            if st.button("🤖", key=f"comp_predict_{i}_{code}", help="Predict"):
                st.session_state['selected_scheme_code'] = code
                st.session_state['navigate_to'] = '🤖 NAV Predictions'
                st.rerun()
        
        with col4:
            if st.button("💼", key=f"comp_port_{i}_{code}", help="Add to Portfolio"):
                add_to_portfolio(code)
        
        with col5:
            if st.button("🗑️", key=f"comp_remove_{i}_{code}", help="Remove"):
                st.session_state['compare_schemes_list'].remove(code)
                st.rerun()
    
    st.markdown("---")
    
    # Action buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # FIXED: Toggle flag instead of setting it
        if st.button("➕ Add More", use_container_width=True, key="comp_add_more"):
            st.session_state['show_compare_add_form'] = not st.session_state.get('show_compare_add_form', False)
            # DON'T RERUN - let it display naturally
    
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
            st.session_state['compare_search_results'] = None
            st.session_state['show_compare_add_form'] = False
            st.rerun()
    
    with col4:
        if st.button("📥 Export CSV", use_container_width=True, key="comp_export"):
            export_comparison_csv()
    
    # Show add form if flag is True (without rerun)
    if st.session_state.get('show_compare_add_form'):
        st.markdown("---")
        st.markdown("### ➕ Add More Schemes")
        render_add_scheme_interface()
        
        # Add a close button
        if st.button("❌ Close Add Form", use_container_width=True, key="comp_close_add_form"):
            st.session_state['show_compare_add_form'] = False
            st.rerun()
    
    # Run comparison
    if st.session_state.get('run_comparison'):
        st.markdown("---")
        render_comparison_results()


def add_to_portfolio(scheme_code: str):
    """Add scheme to portfolio"""
    if 'portfolio_schemes_list' not in st.session_state:
        st.session_state['portfolio_schemes_list'] = []
    
    try:
        scheme_info = api.get_scheme_details(scheme_code)
        if scheme_info:
            if not any(s['code'] == scheme_code for s in st.session_state['portfolio_schemes_list']):
                st.session_state['portfolio_schemes_list'].append({
                    'code': scheme_code,
                    'name': scheme_info.get('scheme_name', scheme_code),
                    'weight': 0.2
                })
                st.success(f"✅ Added to portfolio!")
            else:
                st.warning("Already in portfolio")
    except:
        st.error("Unable to add to portfolio")


def export_comparison_csv():
    """Export comparison list as CSV"""
    df = pd.DataFrame({
        'Scheme Code': st.session_state['compare_schemes_list']
    })
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download List",
        data=csv,
        file_name="comparison_list.csv",
        mime="text/csv",
        key="comp_download_list"
    )


def render_comparison_results():
    """Render enhanced comparison results with visualizations"""
    
    st.markdown("### 📊 Comparison Results & Analytics")
    
    with st.spinner("📊 Comparing schemes... This may take a minute."):
        try:
            data = api.compare_schemes(st.session_state['compare_schemes_list'])
            
            if not data or not data.get('schemes'):
                st.error("❌ Unable to compare schemes. Please try again.")
                st.session_state['run_comparison'] = False
                return
            
            # Display results
            df_compare = pd.DataFrame(data['schemes'])
            
            # Clean data
            df_compare = df_compare.fillna(0)
            
            # Create tabs for different views
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📋 Summary Table",
                "📈 Returns Analysis",
                "⚠️ Risk Analysis",
                "🎯 Risk-Return Profile",
                "📊 Radar Chart"
            ])
            
            with tab1:
                render_summary_table(df_compare, data)
            
            with tab2:
                render_returns_analysis(df_compare)
            
            with tab3:
                render_risk_analysis(df_compare)
            
            with tab4:
                render_risk_return_scatter(df_compare)
            
            with tab5:
                render_radar_chart(df_compare)
            
            st.session_state['run_comparison'] = False
        
        except Exception as e:
            st.error(f"❌ Error during comparison: {str(e)}")
            st.session_state['run_comparison'] = False


def render_summary_table(df: pd.DataFrame, data: dict):
    """Render summary table with key metrics"""
    
    st.markdown("#### 📋 Comprehensive Comparison Table")
    
    # Display table
    display_df = df[[
        'scheme_code', 'scheme_name', 'current_nav', 'cagr',
        'sharpe_ratio', 'volatility', 'max_drawdown'
    ]].copy()
    
    # Format columns
    display_df['current_nav'] = display_df['current_nav'].apply(lambda x: f"₹{x:.2f}")
    display_df['cagr'] = display_df['cagr'].apply(lambda x: f"{x*100:.2f}%" if x != 0 else "N/A")
    display_df['sharpe_ratio'] = display_df['sharpe_ratio'].apply(lambda x: f"{x:.3f}" if x != 0 else "N/A")
    display_df['volatility'] = display_df['volatility'].apply(lambda x: f"{x*100:.2f}%")
    display_df['max_drawdown'] = display_df['max_drawdown'].apply(lambda x: f"{abs(x)*100:.2f}%")
    
    # Rename columns for display
    display_df.columns = ['Code', 'Scheme Name', 'NAV', 'CAGR', 'Sharpe Ratio', 'Volatility', 'Max Drawdown']
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Best performers
    st.markdown("---")
    st.markdown("#### 🏆 Best Performers")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if data.get('best_by_sharpe'):
            st.success(f"**🎯 Best Sharpe Ratio**\n\n{data['best_by_sharpe']}")
    
    with col2:
        if data.get('best_by_return'):
            st.success(f"**📈 Highest Returns**\n\n{data['best_by_return']}")
    
    with col3:
        # Find lowest volatility
        min_vol_idx = df['volatility'].idxmin()
        st.success(f"**🛡️ Lowest Risk**\n\n{df.loc[min_vol_idx, 'scheme_code']}")
    
    # Download
    st.markdown("---")
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download Full Comparison CSV",
        data=csv,
        file_name="scheme_comparison_full.csv",
        mime="text/csv",
        key="comp_download_results"
    )


def render_returns_analysis(df: pd.DataFrame):
    """Render returns analysis with visualizations"""
    
    st.markdown("#### 📈 Returns Analysis")
    
    # 1. CAGR Comparison - Bar Chart
    fig1 = go.Figure()
    cagr_data = df[df['cagr'] != 0].copy()
    
    if len(cagr_data) > 0:
        colors = ['green' if x > 0 else 'red' for x in cagr_data['cagr']]
        
        fig1.add_trace(go.Bar(
            x=cagr_data['scheme_code'],
            y=cagr_data['cagr'] * 100,
            marker_color=colors,
            text=[f"{x:.2f}%" for x in cagr_data['cagr'] * 100],
            textposition='outside',
            name='CAGR',
            hovertemplate='%{x}<br>CAGR: %{y:.2f}%<extra></extra>'
        ))
        
        fig1.update_layout(
            title="Compound Annual Growth Rate (CAGR) Comparison",
            xaxis_title="Scheme Code",
            yaxis_title="CAGR (%)",
            height=450,
            showlegend=False,
            hovermode='x unified',
            xaxis_tickangle=-45
        )
        
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.warning("CAGR data not available for comparison")
    
    # 2. Annualized Returns vs Sharpe Ratio - Grouped Bar
    st.markdown("---")
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig2.add_trace(
        go.Bar(
            name='Annualized Return (%)',
            x=df['scheme_code'],
            y=df['annualized_return'] * 100,
            marker_color='lightblue',
            hovertemplate='Return: %{y:.2f}%<extra></extra>'
        ),
        secondary_y=False
    )
    
    sharpe_data = df[df['sharpe_ratio'] != 0]
    if len(sharpe_data) > 0:
        fig2.add_trace(
            go.Scatter(
                name='Sharpe Ratio',
                x=sharpe_data['scheme_code'],
                y=sharpe_data['sharpe_ratio'],
                marker_color='orange',
                mode='lines+markers',
                marker=dict(size=10),
                hovertemplate='Sharpe: %{y:.3f}<extra></extra>'
            ),
            secondary_y=True
        )
    
    fig2.update_layout(
        title="Returns vs Risk-Adjusted Returns (Sharpe Ratio)",
        height=450,
        hovermode='x unified',
        xaxis_tickangle=-45
    )
    
    fig2.update_xaxes(title_text="Scheme Code")
    fig2.update_yaxes(title_text="Annualized Return (%)", secondary_y=False)
    fig2.update_yaxes(title_text="Sharpe Ratio", secondary_y=True)
    
    st.plotly_chart(fig2, use_container_width=True)
    
    # 3. Performance Ranking
    st.markdown("---")
    st.markdown("#### 🏅 Performance Ranking")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**By CAGR (Highest to Lowest):**")
        cagr_ranked = df[df['cagr'] != 0].sort_values('cagr', ascending=False)
        if len(cagr_ranked) > 0:
            for i, (idx, row) in enumerate(cagr_ranked.iterrows(), 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔹"
                st.write(f"{emoji} **{i}.** {row['scheme_code']}: **{row['cagr']*100:.2f}%**")
        else:
            st.info("No CAGR data available")
    
    with col2:
        st.markdown("**By Sharpe Ratio (Best Risk-Adjusted):**")
        sharpe_ranked = df[df['sharpe_ratio'] != 0].sort_values('sharpe_ratio', ascending=False)
        if len(sharpe_ranked) > 0:
            for i, (idx, row) in enumerate(sharpe_ranked.iterrows(), 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔹"
                st.write(f"{emoji} **{i}.** {row['scheme_code']}: **{row['sharpe_ratio']:.3f}**")
        else:
            st.info("No Sharpe Ratio data available")


def render_risk_analysis(df: pd.DataFrame):
    """Render risk analysis with visualizations"""
    
    st.markdown("#### ⚠️ Risk Analysis")
    
    # 1. Volatility Comparison
    fig1 = go.Figure()
    
    fig1.add_trace(go.Bar(
        x=df['scheme_code'],
        y=df['volatility'] * 100,
        marker_color='orange',
        text=[f"{x:.2f}%" for x in df['volatility'] * 100],
        textposition='outside',
        name='Volatility',
        hovertemplate='%{x}<br>Volatility: %{y:.2f}%<extra></extra>'
    ))
    
    fig1.update_layout(
        title="Volatility (Risk) Comparison - Lower is Better",
        xaxis_title="Scheme Code",
        yaxis_title="Volatility (%)",
        height=450,
        showlegend=False,
        xaxis_tickangle=-45
    )
    
    st.plotly_chart(fig1, use_container_width=True)
    
    # 2. Maximum Drawdown Comparison
    st.markdown("---")
    fig2 = go.Figure()
    
    fig2.add_trace(go.Bar(
        x=df['scheme_code'],
        y=df['max_drawdown'].abs() * 100,
        marker_color='red',
        text=[f"{x:.2f}%" for x in df['max_drawdown'].abs() * 100],
        textposition='outside',
        name='Max Drawdown',
        hovertemplate='%{x}<br>Max Drawdown: %{y:.2f}%<extra></extra>'
    ))
    
    fig2.update_layout(
        title="Maximum Drawdown (Worst Loss) - Lower is Better",
        xaxis_title="Scheme Code",
        yaxis_title="Max Drawdown (%)",
        height=450,
        showlegend=False,
        xaxis_tickangle=-45
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    
    # 3. Multi-metric Risk Heatmap
    st.markdown("---")
    st.markdown("#### 🔥 Risk Metrics Heatmap")
    
    # Prepare data for heatmap
    risk_metrics = df[['scheme_code', 'volatility', 'max_drawdown', 'downside_deviation', 'var_95']].copy()
    risk_metrics['max_drawdown'] = risk_metrics['max_drawdown'].abs()
    risk_metrics['var_95'] = risk_metrics['var_95'].abs()
    risk_metrics = risk_metrics.set_index('scheme_code')
    
    # Normalize to 0-100 scale
    normalized = (risk_metrics - risk_metrics.min()) / (risk_metrics.max() - risk_metrics.min()) * 100
    
    fig3 = go.Figure(data=go.Heatmap(
        z=normalized.values.T,
        x=normalized.index,
        y=['Volatility', 'Max Drawdown', 'Downside Dev', 'VaR 95%'],
        colorscale='Reds',
        text=risk_metrics.values.T,
        texttemplate='%{text:.4f}',
        textfont={"size": 10},
        colorbar=dict(title="Risk Level"),
        hovertemplate='%{y}<br>%{x}<br>Value: %{text:.4f}<extra></extra>'
    ))
    
    fig3.update_layout(
        title="Risk Metrics Heatmap (Darker Red = Higher Risk)",
        height=400
    )
    
    st.plotly_chart(fig3, use_container_width=True)
    
    st.info("💡 **Tip:** Look for schemes with lighter colors across all metrics for lower overall risk.")


def render_risk_return_scatter(df: pd.DataFrame):
    """Render risk-return scatter plot"""
    
    st.markdown("#### 🎯 Risk vs Return Profile")
    st.markdown("*Ideal schemes are in the top-left quadrant (high return, low risk)*")
    
    # Filter data
    scatter_data = df[
        (df['cagr'] != 0) &
        (df['volatility'] != 0)
    ].copy()
    
    if len(scatter_data) == 0:
        st.warning("Insufficient data for risk-return analysis")
        return
    
    # Create scatter plot
    fig = go.Figure()
    
    # Add scatter points
    fig.add_trace(go.Scatter(
        x=scatter_data['volatility'] * 100,
        y=scatter_data['cagr'] * 100,
        mode='markers+text',
        marker=dict(
            size=15,
            color=scatter_data['sharpe_ratio'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Sharpe<br>Ratio"),
            line=dict(width=2, color='white')
        ),
        text=scatter_data['scheme_code'],
        textposition='top center',
        name='Schemes',
        hovertemplate='<b>%{text}</b><br>Risk: %{x:.2f}%<br>Return: %{y:.2f}%<br>Sharpe: %{marker.color:.3f}<extra></extra>'
    ))
    
    # Add quadrant lines
    avg_return = scatter_data['cagr'].mean() * 100
    avg_risk = scatter_data['volatility'].mean() * 100
    
    fig.add_hline(y=avg_return, line_dash="dash", line_color="gray", annotation_text="Avg Return", annotation_position="right")
    fig.add_vline(x=avg_risk, line_dash="dash", line_color="gray", annotation_text="Avg Risk", annotation_position="top")
    
    # Add quadrant labels
    fig.add_annotation(x=avg_risk*0.5, y=avg_return*1.5, text="🎯 Best<br>(Low Risk, High Return)", showarrow=False, font=dict(size=10, color="green"))
    fig.add_annotation(x=avg_risk*1.5, y=avg_return*1.5, text="📈 Aggressive<br>(High Risk, High Return)", showarrow=False, font=dict(size=10))
    fig.add_annotation(x=avg_risk*0.5, y=avg_return*0.5, text="🛡️ Conservative<br>(Low Risk, Low Return)", showarrow=False, font=dict(size=10))
    fig.add_annotation(x=avg_risk*1.5, y=avg_return*0.5, text="⚠️ Avoid<br>(High Risk, Low Return)", showarrow=False, font=dict(size=10, color="red"))
    
    fig.update_layout(
        title="Risk vs Return Analysis with Sharpe Ratio",
        xaxis_title="Risk (Volatility %)",
        yaxis_title="Return (CAGR %)",
        height=600,
        showlegend=True,
        hovermode='closest'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Interpretation guide
    st.markdown("---")
    st.markdown("#### 📖 Interpretation Guide")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Quadrant Analysis:**
        - **🎯 Top-Left:** High return, low risk (Best schemes)
        - **📈 Top-Right:** High return, high risk (Aggressive)
        - **🛡️ Bottom-Left:** Low return, low risk (Conservative)
        - **⚠️ Bottom-Right:** Low return, high risk (Avoid these)
        """)
    
    with col2:
        st.markdown("""
        **Color Coding (Sharpe Ratio):**
        - **Yellow/Bright:** Better risk-adjusted returns
        - **Dark Blue:** Poorer risk-adjusted returns
        - Higher Sharpe = More return per unit of risk
        - Look for bright colors in top-left quadrant
        """)


def render_radar_chart(df: pd.DataFrame):
    """Render radar chart for multi-dimensional comparison"""
    
    st.markdown("#### 📊 Multi-Dimensional Radar Chart")
    st.markdown("*Compare schemes across multiple metrics simultaneously*")
    
    # Prepare data
    metrics_to_plot = ['cagr', 'sharpe_ratio', 'sortino_ratio', 'volatility', 'max_drawdown']
    available_metrics = [m for m in metrics_to_plot if m in df.columns]
    
    if len(available_metrics) < 3:
        st.warning("Insufficient metrics for radar chart")
        return
    
    # Create radar chart
    fig = go.Figure()
    
    for idx, row in df.iterrows():
        values = []
        labels = []
        
        for metric in available_metrics:
            val = row[metric]
            if val != 0 and not pd.isna(val):
                # Normalize to 0-100
                col_min = df[metric].min()
                col_max = df[metric].max()
                
                if col_max != col_min:
                    # Invert for risk metrics (lower is better)
                    if metric in ['volatility', 'max_drawdown']:
                        normalized = 100 - ((val - col_min) / (col_max - col_min) * 100)
                    else:
                        normalized = (val - col_min) / (col_max - col_min) * 100
                    
                    values.append(normalized)
                    labels.append(metric.replace('_', ' ').title())
        
        if len(values) > 0:
            # Close the radar chart
            values.append(values[0])
            labels.append(labels[0])
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=labels,
                fill='toself',
                name=row['scheme_code'],
                hovertemplate='%{theta}<br>Score: %{r:.1f}<extra></extra>'
            ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True,
        title="Multi-Metric Comparison (Higher = Better Performance)",
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Legend
    st.info("""
    **📌 How to Read:**
    - All metrics normalized to 0-100 scale
    - Risk metrics (volatility, drawdown) inverted: lower risk = higher score
    - Larger area = Better overall performance
    - Look for schemes with balanced large polygons
    """)

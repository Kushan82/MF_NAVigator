"""
Analytics Dashboard Page - With Power BI Market Overview Integration
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit.components.v1 as components
from frontend.utils.api_client import APIClient
from pathlib import Path

api = APIClient()

def render():
    """Render analytics dashboard page"""
    
    st.markdown("# 📊 Analytics Dashboard")
    st.markdown("Advanced data analytics and market insights")
    st.markdown("---")
    
    # Dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Market Overview (Power BI)",
        "🔥 Top Performers",
        "📊 Category Analysis",
        "🎯 Advanced Analytics"
    ])
    
    with tab1:
        render_market_overview_powerbi()
    
    with tab2:
        render_top_performers()
    
    with tab3:
        render_category_analysis()
    
    with tab4:
        render_advanced_analytics()


def render_market_overview_powerbi():
    """Render Power BI market overview with data export"""
    
    st.markdown("### 📊 Market Overview Dashboard")
    
    # Check if Power BI data exists
    powerbi_dir = Path("powerbi_data")
    
    if not powerbi_dir.exists() or not list(powerbi_dir.glob("*.csv")):
        st.warning("⚠️ Power BI data not exported yet!")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if st.button("📊 Export Data for Power BI", use_container_width=True, type="primary"):
                export_powerbi_data()
        
        with col2:
            st.info("Click to generate datasets for Power BI dashboard")
        
        st.markdown("---")
        render_powerbi_instructions()
    
    else:
        # Show integration options
        st.success("✅ Power BI data is ready!")
        
        integration_type = st.radio(
            "Select Display Mode:",
            ["📸 Preview (Static)", "🔗 Embedded Dashboard", "📊 Live Data View"],
            horizontal=True
        )
        
        if integration_type == "📸 Preview (Static)":
            render_static_powerbi_preview()
        
        elif integration_type == "🔗 Embedded Dashboard":
            render_embedded_powerbi()
        
        elif integration_type == "📊 Live Data View":
            render_live_data_view()


def export_powerbi_data():
    """Export data for Power BI"""
    
    with st.spinner("📊 Exporting data for Power BI..."):
        try:
            # Import and run exporter
            import sys
            sys.path.append(str(Path(__file__).parent.parent.parent))
            
            from models.powerbi_exporter import PowerBIDataExporter
            
            exporter = PowerBIDataExporter()
            exported_files = exporter.export_all_datasets()
            
            st.success("✅ Data exported successfully!")
            st.info(f"📂 Files saved to: powerbi_data/")
            
            # Show exported files
            st.markdown("**Exported Files:**")
            for name, path in exported_files.items():
                st.write(f"- {name}: `{path.name}`")
            
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error exporting data: {str(e)}")


def render_powerbi_instructions():
    """Render Power BI setup instructions"""
    
    st.markdown("### 📋 Power BI Dashboard Setup")
    
    with st.expander("📖 How to Create the Dashboard", expanded=True):
        st.markdown("""
        #### Step 1: Export Data
        Click the "Export Data for Power BI" button above to generate CSV files.
        
        #### Step 2: Open Power BI Desktop
        - Download Power BI Desktop (free) from Microsoft
        - Install and open the application
        
        #### Step 3: Import Data
        1. Click **Get Data** → **Text/CSV**
        2. Navigate to the `powerbi_data` folder
        3. Import these files:
           - `amc_market_share.csv`
           - `category_distribution.csv`
           - `amc_category_matrix.csv`
           - `market_statistics.csv`
           - `all_schemes_master.csv`
        
        #### Step 4: Create Visualizations
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Total AUM Card:**
            - Visual: Card
            - Field: SUM(Estimated_AUM_Cr)
            
            **Top AMCs Chart:**
            - Visual: Bar Chart
            - X-axis: AMC
            - Y-axis: Market_Share_Pct
            - Sort: Descending
            """)
        
        with col2:
            st.markdown("""
            **Category Distribution:**
            - Visual: Donut Chart
            - Legend: Category
            - Values: Total_Schemes
            
            **Sector Allocation:**
            - Visual: Matrix Heatmap
            - Rows: AMC
            - Columns: Category
            - Values: Scheme_Count
            """)
        
        st.markdown("""
        #### Step 5: Publish & Embed
        1. **Publish to Web** (Public):
           - File → Publish to web
           - Copy embed URL
           - Paste URL in the "Embedded Dashboard" tab above
        
        2. **Embed Securely** (Requires Power BI Pro):
           - File → Embed → For your organization
           - Configure Azure AD authentication
           - Use embedded code in Streamlit
        """)
    
    with st.expander("📊 Dashboard Features"):
        st.markdown("""
        The Market Overview dashboard will include:
        
        ✅ **Total AUM across all funds**
        - Aggregated estimated AUM by AMC
        - Visual: Large metric card with trend
        
        ✅ **Top AMCs by market share**
        - Horizontal bar chart showing top 10 AMCs
        - Pie chart for market share distribution
        - Drill-down capability
        
        ✅ **Category distribution**
        - Donut chart showing scheme distribution
        - Treemap for hierarchical view
        - Percentage breakdowns
        
        ✅ **Market trends**
        - NAV distribution histogram
        - Time series analysis (if historical data loaded)
        - Growth indicators
        
        ✅ **Sector allocation**
        - AMC-Category matrix heatmap
        - Concentration analysis
        - Diversification metrics
        """)


def render_static_powerbi_preview():
    """Show static preview of Power BI data"""
    
    st.markdown("### 📸 Power BI Data Preview")
    
    powerbi_dir = Path("powerbi_data")
    
    # Load and display key datasets
    try:
        # 1. Market Statistics
        stats_df = pd.read_csv(powerbi_dir / "market_statistics.csv")
        
        st.markdown("#### 📊 Market Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_schemes = stats_df[stats_df['Metric'] == 'Total Schemes']['Value'].iloc[0]
            st.metric("Total Schemes", f"{total_schemes:,.0f}")
        
        with col2:
            avg_nav = stats_df[stats_df['Metric'] == 'Average NAV']['Value'].iloc[0]
            st.metric("Avg NAV", f"₹{avg_nav:.2f}")
        
        with col3:
            total_amcs = stats_df[stats_df['Metric'] == 'Total AMCs']['Value'].iloc[0]
            st.metric("Total AMCs", f"{total_amcs:.0f}")
        
        with col4:
            total_cats = stats_df[stats_df['Metric'] == 'Total Categories']['Value'].iloc[0]
            st.metric("Categories", f"{total_cats:.0f}")
        
        st.markdown("---")
        
        # 2. Top AMCs
        amc_df = pd.read_csv(powerbi_dir / "amc_market_share.csv")
        
        st.markdown("#### 🏆 Top 10 AMCs by Market Share")
        
        top_10_amc = amc_df.head(10)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=top_10_amc['Market_Share_Pct'],
            y=top_10_amc['AMC'],
            orientation='h',
            marker_color='lightblue',
            text=[f"{x:.1f}%" for x in top_10_amc['Market_Share_Pct']],
            textposition='outside'
        ))
        
        fig.update_layout(
            title="Top 10 AMCs by Market Share",
            xaxis_title="Market Share (%)",
            yaxis_title="AMC",
            height=500,
            yaxis={'categoryorder': 'total ascending'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show data table
        with st.expander("📋 View Full AMC Data"):
            st.dataframe(
                amc_df[['AMC', 'Total_Schemes', 'Market_Share_Pct', 'Estimated_AUM_Cr']],
                use_container_width=True,
                hide_index=True
            )
        
        st.markdown("---")
        
        # 3. Category Distribution
        cat_df = pd.read_csv(powerbi_dir / "category_distribution.csv")
        
        st.markdown("#### 📊 Category Distribution")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie chart
            fig_pie = go.Figure(data=[go.Pie(
                labels=cat_df['Category'],
                values=cat_df['Total_Schemes'],
                hole=.3
            )])
            
            fig_pie.update_layout(
                title="Schemes by Category",
                height=400
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Bar chart
            fig_bar = go.Figure(data=[go.Bar(
                x=cat_df['Category'],
                y=cat_df['Total_Schemes'],
                marker_color='orange'
            )])
            
            fig_bar.update_layout(
                title="Number of Schemes",
                xaxis_title="Category",
                yaxis_title="Count",
                height=400,
                xaxis={'tickangle': -45}
            )
            
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # Show data table
        with st.expander("📋 View Category Details"):
            st.dataframe(
                cat_df[['Category', 'Total_Schemes', 'Percentage', 'Avg_NAV']],
                use_container_width=True,
                hide_index=True
            )
        
        st.markdown("---")
        
        # 4. Sector Allocation Heatmap
        matrix_df = pd.read_csv(powerbi_dir / "amc_category_matrix.csv")
        
        st.markdown("#### 🔥 Sector Allocation Heatmap")
        
        # Create pivot table
        pivot = matrix_df.pivot_table(
            index='AMC',
            columns='Category',
            values='Scheme_Count',
            fill_value=0
        )
        
        # Show top 15 AMCs
        pivot_top = pivot.head(15)
        
        fig_heat = go.Figure(data=go.Heatmap(
            z=pivot_top.values,
            x=pivot_top.columns,
            y=pivot_top.index,
            colorscale='Blues',
            text=pivot_top.values,
            texttemplate='%{text}',
            textfont={"size": 8},
            colorbar=dict(title="Schemes")
        ))
        
        fig_heat.update_layout(
            title="AMC-Category Scheme Distribution (Top 15 AMCs)",
            xaxis_title="Category",
            yaxis_title="AMC",
            height=600
        )
        
        st.plotly_chart(fig_heat, use_container_width=True)
        
    except FileNotFoundError as e:
        st.error(f"❌ Data file not found: {e}")
        st.info("Please export Power BI data first")
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")


def render_embedded_powerbi():
    """Render embedded Power BI dashboard"""
    
    st.markdown("### 🔗 Embedded Power BI Dashboard")
    
    # Input for Power BI embed URL
    embed_url = st.text_input(
        "Enter Power BI Embed URL:",
        placeholder="https://app.powerbi.com/view?r=...",
        help="Get this from Power BI: File → Publish to web"
    )
    
    if embed_url:
        # Embed iframe
        iframe_html = f"""
        <iframe 
            width="100%" 
            height="800" 
            src="{embed_url}"
            frameborder="0" 
            allowFullScreen="true">
        </iframe>
        """
        
        components.html(iframe_html, height=820, scrolling=True)
    else:
        st.info("""
        **To embed your Power BI dashboard:**
        
        1. Open your report in Power BI Desktop
        2. Click **File** → **Publish to web (public)**
        3. Click **Create embed code**
        4. Copy the URL from the embed code
        5. Paste it in the text box above
        
        ⚠️ **Note:** This will make your dashboard publicly accessible
        """)


def render_live_data_view():
    """Show live data from Power BI files with refresh"""
    
    st.markdown("### 📊 Live Data View")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🔄 Refresh Data", use_container_width=True):
            export_powerbi_data()
    
    with col2:
        auto_refresh = st.checkbox("Auto-refresh (30s)")
    
    if auto_refresh:
        st.info("🔄 Auto-refresh enabled")
        import time
        time.sleep(30)
        st.rerun()
    
    # Show timestamp
    powerbi_dir = Path("powerbi_data")
    if powerbi_dir.exists():
        stats_file = powerbi_dir / "market_statistics.csv"
        if stats_file.exists():
            import os
            mod_time = os.path.getmtime(stats_file)
            from datetime import datetime
            dt = datetime.fromtimestamp(mod_time)
            st.caption(f"Last updated: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
    
    st.markdown("---")
    
    # Display current data
    render_static_powerbi_preview()


def render_top_performers():
    """Render top performers section"""
    
    st.markdown("### 🔥 Top Performers")
    
    st.info("🚧 Top performers analysis coming soon!")
    
    st.markdown("""
    **Will display:**
    - Top 10 gainers (daily/weekly/monthly)
    - Top 10 losers
    - Most volatile funds
    - Highest volume traded
    - Best risk-adjusted returns (Sharpe)
    """)


def render_category_analysis():
    """Render category analysis section"""
    
    st.markdown("### 📊 Category Analysis")
    
    st.info("🚧 Category analysis coming soon!")
    
    st.markdown("""
    **Planned visualizations:**
    - Performance by category
    - Category-wise distribution
    - Risk-return by category
    - Top schemes in each category
    - Category trends over time
    """)


def render_advanced_analytics():
    """Render advanced analytics section"""
    
    st.markdown("### 🎯 Advanced Analytics")
    
    st.info("🚧 Advanced analytics tools coming soon!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Statistical Analysis:**
        - Correlation heatmap
        - Distribution analysis
        - Rolling statistics
        - Regression analysis
        - Factor analysis
        """)
    
    with col2:
        st.markdown("""
        **Predictive Analytics:**
        - Batch predictions
        - Trend detection
        - Anomaly detection
        - Pattern recognition
        - Sentiment analysis
        """)
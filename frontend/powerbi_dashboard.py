"""
Analytics Dashboard Page - FIXED VERSION
Maintains original function names, adds Power BI integration
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))


def render():
    """Render analytics dashboard page"""
    
    st.markdown("# 📊 Analytics Dashboard")
    st.markdown("Market insights and Power BI data export")
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs([
        "📈 Market Overview",
        "📊 Power BI Export",
        "🔧 Power BI Setup Guide"
    ])
    
    with tab1:
        render_market_overview()
    
    with tab2:
        render_powerbi_export()
    
    with tab3:
        render_powerbi_guide()


def render_market_overview():
    """Render market overview with filters"""
    
    st.markdown("### 📊 Market Overview")
    
    powerbi_dir = Path("powerbi_data")
    
    # Check if data exists
    if not powerbi_dir.exists() or not list(powerbi_dir.glob("*.csv")):
        st.warning("⚠️ No data available. Please export data first.")
        
        if st.button("📊 Export Data Now", type="primary"):
            export_powerbi_data()
            st.rerun()
        
        return
    
    # Load data
    try:
        df_stats = pd.read_csv(powerbi_dir / "market_statistics.csv")
        df_amc = pd.read_csv(powerbi_dir / "amc_market_share.csv")
        df_category = pd.read_csv(powerbi_dir / "category_distribution.csv")
        df_performance = pd.read_csv(powerbi_dir / "amc_performance.csv")
        
        # Category filter (DROPDOWN)
        st.markdown("#### 🎯 Filter by Category")
        
        categories = ['All'] + sorted(df_category['Category'].unique().tolist())
        selected_category = st.selectbox(
            "Select Category:",
            options=categories,
            key="market_category_filter"
        )
        
        st.markdown("---")
        
        # Market Statistics KPIs
        st.markdown("#### 📈 Market Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_schemes = df_stats[df_stats['Metric'] == 'Total Schemes']['Value'].iloc[0]
            st.metric("Total Schemes", f"{int(total_schemes):,}")
        
        with col2:
            total_amcs = df_stats[df_stats['Metric'] == 'Total AMCs']['Value'].iloc[0]
            st.metric("Fund Houses", f"{int(total_amcs)}")
        
        with col3:
            avg_nav = df_stats[df_stats['Metric'] == 'Average NAV']['Value'].iloc[0]
            st.metric("Avg NAV", f"₹{float(avg_nav):.2f}")
        
        with col4:
            latest_date = df_stats[df_stats['Metric'] == 'Latest Data Date']['Value'].iloc[0]
            st.metric("Data Date", latest_date)
        
        st.markdown("---")
        
        # Filter data by category if selected
        if selected_category != 'All':
            # Filter performance data
            df_performance_filtered = df_performance[
                df_performance['AMC'].isin(
                    df_category[df_category['Category'] == selected_category]['AMC'].values
                )
            ] if 'Category' in df_category.columns else df_performance
            
            st.info(f"📊 Showing data for category: **{selected_category}**")
        else:
            df_performance_filtered = df_performance
        
        # Top 10 AMCs by CAGR (Bar Chart)
        st.markdown("#### 🏆 Top 10 AMCs by Average CAGR")
        
        top_amc_cagr = df_performance_filtered.nlargest(10, 'Avg_CAGR')
        
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=top_amc_cagr['AMC'],
            y=top_amc_cagr['Avg_CAGR'],
            marker_color='lightblue',
            text=[f"{x:.2f}%" for x in top_amc_cagr['Avg_CAGR']],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>CAGR: %{y:.2f}%<extra></extra>'
        ))
        
        fig_bar.update_layout(
            title="Top 10 Fund Houses by Average CAGR",
            xaxis_title="AMC",
            yaxis_title="Average CAGR (%)",
            height=450,
            xaxis_tickangle=-45,
            showlegend=False
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
        
        st.markdown("---")
        
        # Top 10 AMCs by Market Share (Pie Chart)
        st.markdown("#### 💼 Top 10 AMCs by Market Share (AUM)")
        
        top_amc_aum = df_amc.nlargest(10, 'Market_Share_Pct')
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=top_amc_aum['AMC'],
            values=top_amc_aum['Market_Share_Pct'],
            hole=.3,
            hovertemplate='<b>%{label}</b><br>Share: %{value:.2f}%<extra></extra>'
        )])
        
        fig_pie.update_layout(
            title="Market Share Distribution (Top 10 AMCs)",
            height=500
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
        
        st.markdown("---")
        
        # Performance Heatmap
        st.markdown("#### 🔥 AMC Performance Heatmap (Top 15)")
        
        # Prepare data for heatmap
        top_15_amc = df_performance_filtered.nlargest(15, 'Avg_CAGR')
        
        heatmap_data = top_15_amc[['AMC', 'Avg_CAGR', 'Avg_Return_1Y', 'Avg_Sharpe']].set_index('AMC')
        
        fig_heat = go.Figure(data=go.Heatmap(
            z=heatmap_data.values.T,
            x=heatmap_data.index,
            y=['Avg CAGR (%)', 'Avg 1Y Return (%)', 'Avg Sharpe Ratio'],
            colorscale='RdYlGn',
            text=heatmap_data.values.T,
            texttemplate='%{text:.2f}',
            textfont={"size": 10},
            hovertemplate='%{y}<br>%{x}<br>Value: %{z:.2f}<extra></extra>'
        ))
        
        fig_heat.update_layout(
            title="Performance Metrics Heatmap (Top 15 AMCs by CAGR)",
            xaxis_title="AMC",
            height=400
        )
        
        st.plotly_chart(fig_heat, use_container_width=True)
        
        # Data quality info
        st.markdown("---")
        st.info(f"""
        **📊 Data Coverage:**
        - Total AMCs analyzed: {len(df_amc)}
        - AMCs with performance data: {len(df_performance)}
        - Categories: {len(df_category)}
        
        **🔄 Last Updated:** {latest_date}
        """)
        
    except FileNotFoundError as e:
        st.error(f"❌ Data file not found: {e}")
        st.info("Please export Power BI data first")
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")


def render_powerbi_export():
    """Render Power BI data export interface"""
    
    st.markdown("### 📊 Export Data for Power BI")
    
    st.info("""
    **What this does:**
    - Fetches latest scheme data from AMFI
    - Calculates CAGR and returns for 500 sample schemes
    - Generates 7 CSV files for Power BI import
    - Exports to `powerbi_data/` folder
    """)
    
    # Export settings
    col1, col2 = st.columns(2)
    
    with col1:
        sample_size = st.number_input(
            "Number of schemes to analyze:",
            min_value=100,
            max_value=2000,
            value=500,
            step=100,
            help="More schemes = more data but longer processing time"
        )
    
    with col2:
        force_refresh = st.checkbox(
            "Force refresh data",
            value=True,
            help="Fetch fresh data from AMFI"
        )
    
    st.markdown("---")
    
    # Export button
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("📊 Export Data", type="primary", use_container_width=True):
            export_powerbi_data(sample_size, force_refresh)
    
    with col2:
        if st.button("🔄 Refresh Preview", use_container_width=True):
            st.rerun()
    
    # Show existing files
    st.markdown("---")
    st.markdown("### 📂 Exported Files")
    
    powerbi_dir = Path("powerbi_data")
    
    if powerbi_dir.exists():
        csv_files = list(powerbi_dir.glob("*.csv"))
        
        if csv_files:
            st.success(f"✅ Found {len(csv_files)} exported files")
            
            for file in csv_files:
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"📄 {file.name}")
                
                with col2:
                    size_kb = file.stat().st_size / 1024
                    st.caption(f"{size_kb:.1f} KB")
                
                with col3:
                    # Download button
                    with open(file, 'rb') as f:
                        st.download_button(
                            label="📥",
                            data=f,
                            file_name=file.name,
                            mime="text/csv",
                            key=f"download_{file.name}"
                        )
        else:
            st.warning("No files exported yet")
    else:
        st.warning("Export folder not created yet")


def export_powerbi_data(sample_size: int = 500, force_refresh: bool = True):
    """Export data using PowerBIDataExporter"""
    
    with st.spinner(f"📊 Exporting data (analyzing {sample_size} schemes)... This may take 2-5 minutes."):
        try:
            from models.export_for_powerbi import PowerBIDataExporter
            
            exporter = PowerBIDataExporter()
            exported = exporter.export_all_datasets(
                force_refresh=force_refresh,
                sample_size=sample_size
            )
            
            st.success("✅ Data exported successfully!")
            
            # Show exported files
            st.markdown("**Exported files:**")
            for name, path in exported.items():
                st.write(f"- {path.name}")
            
            st.info(f"📂 Files saved to: `powerbi_data/`")
            
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Export failed: {str(e)}")
            import traceback
            st.code(traceback.format_exc())


def render_powerbi_guide():
    """Render comprehensive Power BI setup guide"""
    
    st.markdown("### 📖 Power BI Dashboard Setup Guide")
    
    st.info("""
    **📋 Prerequisites:**
    - Power BI Desktop (free download from Microsoft)
    - Exported CSV files from the "Power BI Export" tab
    """)
    
    # Step-by-step guide
    with st.expander("📥 Step 1: Download & Install Power BI Desktop", expanded=True):
        st.markdown("""
        1. Go to: https://powerbi.microsoft.com/desktop/
        2. Click **Download Free**
        3. Install Power BI Desktop
        4. Launch the application
        """)
    
    with st.expander("📂 Step 2: Import CSV Files"):
        st.markdown("""
        **Import the following 7 CSV files:**
        
        1. Click **Get Data** → **Text/CSV**
        2. Navigate to `powerbi_data/` folder in your project
        3. Import these files one by one:
           - `market_statistics.csv`
           - `amc_market_share.csv`
           - `amc_performance.csv`
           - `category_distribution.csv`
           - `amc_category_matrix.csv`
           - `schemes_with_performance.csv`
           - `schemes_master.csv`
        4. Click **Load** for each file
        
        **Note:** Files will appear in the **Fields** pane on the right
        """)
    
    with st.expander("🎨 Step 3: Create Visualizations"):
        st.markdown("""
        ### 📊 **Visualization 1: Category Dropdown Filter (Slicer)**
        
        1. Click **Slicer** icon in Visualizations pane
        2. From **category_distribution** table, drag **Category** to the slicer
        3. Click the dropdown arrow on the slicer
        4. Select **Dropdown** style
        5. Position at top of dashboard
        
        ---
        
        ### 📈 **Visualization 2: Market Statistics Cards**
        
        **Card 1: Total Schemes**
        1. Click **Card** icon
        2. From **market_statistics**, drag **Value** field
        3. Add filter: Metric = "Total Schemes"
        4. Format number with thousands separator
        
        **Card 2: Total AMCs**
        1. Create new Card
        2. From **market_statistics**, drag **Value**
        3. Add filter: Metric = "Total AMCs"
        
        **Card 3: Average NAV**
        1. Create new Card
        2. From **market_statistics**, drag **Value**
        3. Add filter: Metric = "Average NAV"
        4. Format as currency (₹)
        
        **Card 4: Latest Date**
        1. Create new Card
        2. From **market_statistics**, drag **Value**
        3. Add filter: Metric = "Latest Data Date"
        
        ---
        
        ### 📊 **Visualization 3: Top 10 AMCs by CAGR (Bar Chart)**
        
        1. Click **Clustered Bar Chart** icon
        2. Y-axis: **AMC** from `amc_performance`
        3. X-axis: **Avg_CAGR** from `amc_performance`
        4. Click on the visual → **Filters** pane
        5. Add filter: **Top N** → Top 10 by Avg_CAGR
        6. Format:
           - Data labels: On
           - Sort by: Avg_CAGR descending
           - Title: "Top 10 AMCs by Average CAGR"
        
        ---
        
        ### 🥧 **Visualization 4: Top 10 AMCs by Market Share (Pie Chart)**
        
        1. Click **Pie Chart** icon
        2. Legend: **AMC** from `amc_market_share`
        3. Values: **Market_Share_Pct** from `amc_market_share`
        4. Add filter: **Top N** → Top 10 by Market_Share_Pct
        5. Format:
           - Show data labels: Percentage
           - Title: "Market Share Distribution (Top 10 AMCs)"
        
        ---
        
        ### 🔥 **Visualization 5: Performance Heatmap**
        
        1. Click **Matrix** icon
        2. Rows: **AMC** from `amc_performance`
        3. Columns: Create a custom column with these metrics:
           - Avg_CAGR
           - Avg_Return_1Y
           - Avg_Sharpe
        4. Values: The metric values
        5. Format:
           - Conditional formatting → Color scales
           - Green (high) → Red (low)
           - Add filter: Top 15 AMCs by Avg_CAGR
        
        **Alternative (simpler):**
        - Use **Table** visualization instead
        - Show AMC, Avg_CAGR, Avg_Return_1Y, Avg_Sharpe
        - Apply conditional formatting to each column
        
        ---
        
        ### 📈 **Visualization 6: Top 10 Schemes by CAGR (Pie Chart)**
        
        1. Click **Pie Chart** icon
        2. Legend: **Scheme_Name** from `schemes_with_performance`
        3. Values: **CAGR** from `schemes_with_performance`
        4. Add filter: **Top N** → Top 10 by CAGR
        5. Format:
           - Data labels: Category and percentage
           - Title: "Top 10 Performing Funds by CAGR"
        
        ---
        
        ### 📊 **Visualization 7: NAV Trend Line Chart (Optional)**
        
        1. Click **Line Chart** icon
        2. X-axis: **Date** from `schemes_master`
        3. Y-axis: **NAV** from `schemes_master`
        4. Legend: **Scheme_Name**
        5. Add filter: Select specific schemes
        6. Format:
           - Show markers: Yes
           - Title: "NAV Trend Comparison"
        """)
    
    with st.expander("🔗 Step 4: Connect Visualizations with Category Filter"):
        st.markdown("""
        **Make the category dropdown filter all visuals:**
        
        1. Click on the **Category slicer**
        2. Go to **Format** pane → **Edit interactions**
        3. Ensure all visuals show a **filter icon** (not "None")
        4. Click off "Edit interactions"
        5. Now when you select a category, all charts update
        
        **Testing:**
        - Select "Equity" → All charts show only equity data
        - Select "Debt" → All charts show only debt data
        - Select "All" → Shows complete data
        """)
    
    with st.expander("🎨 Step 5: Dashboard Layout & Formatting"):
        st.markdown("""
        **Recommended Layout:**
        
        ```
        ┌─────────────────────────────────────────────────┐
        │ [Category Filter: Dropdown]                     │
        ├──────────┬──────────┬──────────┬───────────────┤
        │ Schemes  │   AMCs   │ Avg NAV  │  Data Date    │
        │  Card    │   Card   │  Card    │    Card       │
        ├──────────┴──────────┴──────────┴───────────────┤
        │  Top 10 AMCs by CAGR (Bar Chart)               │
        │                                                 │
        ├────────────────────────┬───────────────────────┤
        │ Top 10 AMCs by Market  │  Performance Heatmap  │
        │ Share (Pie Chart)      │  (Matrix/Table)       │
        │                        │                        │
        ├────────────────────────┴───────────────────────┤
        │  Top 10 Schemes by CAGR (Pie Chart)            │
        │                                                 │
        └─────────────────────────────────────────────────┘
        ```
        
        **Formatting Tips:**
        - Use consistent colors (blue theme)
        - Add borders to visuals
        - Align elements using guides
        - Use canvas background color: Light gray (#F5F5F5)
        """)
    
    with st.expander("💾 Step 6: Save & Publish"):
        st.markdown("""
        **Save Dashboard:**
        1. Click **File** → **Save As**
        2. Name: `MF_NAVigator_Dashboard.pbix`
        3. Save to your project folder
        
        **Publish to Web (Optional):**
        1. Click **File** → **Publish to web (public)**
        2. ⚠️ **Warning:** This makes data publicly accessible
        3. Click **Create embed code**
        4. Copy the URL
        5. Paste URL in Analytics Dashboard → "Embedded Dashboard" tab
        
        **Publish to Power BI Service (Enterprise):**
        1. Sign in to Power BI Service
        2. Click **Publish** → Select workspace
        3. Configure security and sharing
        4. Share link with team
        """)
    
    with st.expander("🔧 Troubleshooting"):
        st.markdown("""
        **Issue: Data not loading**
        - Ensure CSV files are in `powerbi_data/` folder
        - Check file permissions
        - Re-export data from "Power BI Export" tab
        
        **Issue: Filters not working**
        - Enable "Edit interactions"
        - Ensure filter relationships are set
        - Check if correct fields are selected
        
        **Issue: Empty visuals**
        - Verify data has values (not all NaN)
        - Check filters (remove "Top N" temporarily)
        - Inspect data in Data view
        
        **Issue: Incorrect CAGR values**
        - CAGR is calculated for schemes with 1+ year history
        - Values are percentages (e.g., 15.5 = 15.5%)
        - Check `schemes_with_performance.csv` for raw data
        
        **Issue: Category filter not working**
        - Ensure slicer is using correct field
        - Check if relationships between tables exist
        - Try creating calculated column for category
        """)
    
    # Video tutorial placeholder
    st.markdown("---")
    st.info("""
    **🎥 Video Tutorial:**
    For a visual walkthrough, search YouTube for:
    - "Power BI Dashboard Tutorial for Beginners"
    - "Power BI Create Dashboard from CSV"
    """)
    
    # Download sample template
    st.markdown("---")
    st.markdown("### 📥 Download Sample Dashboard Template")
    
    st.info("""
    **Coming Soon:**
    - Pre-built `.pbix` template file
    - Drag-and-drop ready dashboard
    - Just replace data sources
    """)


# Main render function
if __name__ == "__main__":
    render()
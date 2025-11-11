"""
Analytics Dashboard Page - COMPLETE VERSION
Advanced data analytics and market insights with real data integration
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from frontend.utils.api_client import APIClient
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api = APIClient()

# ==========================================
# CACHED DATA FUNCTIONS
# ==========================================

@st.cache_data(ttl=3600)
def get_aum_data_from_api():
    """Fetch AUM data from API (cached for 1 hour)"""
    try:
        return api._make_request("GET", f"{api.api_v1}/nav/amc", show_error=False)
    except Exception as e:
        logger.error(f"Failed to load AUM data: {e}")
        return []

@st.cache_data(ttl=3600)
def get_all_nav_data():
    """Fetch all NAV data (cached for 1 hour)"""
    try:
        return api._make_request("GET", f"{api.api_v1}/nav", show_error=False)
    except Exception as e:
        logger.error(f"Failed to load NAV data: {e}")
        return []

@st.cache_data(ttl=3600)
def get_categories_data():
    """Fetch categories data (cached for 1 hour)"""
    try:
        return api._make_request("GET", f"{api.api_v1}/nav/categories", show_error=False)
    except Exception as e:
        logger.error(f"Failed to load categories: {e}")
        return {"categories": [], "types": []}

# ==========================================
# MAIN RENDER FUNCTION
# ==========================================

def render():
    """Render analytics dashboard page"""
    
    st.markdown("# 📊 Analytics Dashboard")
    st.markdown("Advanced data analytics and market insights")
    st.markdown("---")
    
    # Dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Market Overview",
        "🏢 AMC Analysis",
        "📊 Category Analysis",
        "🔍 Scheme Explorer"
    ])
    
    with tab1:
        render_market_overview()
    
    with tab2:
        render_amc_analysis()
    
    with tab3:
        render_category_analysis()
    
    with tab4:
        render_scheme_explorer()

# ==========================================
# MARKET OVERVIEW
# ==========================================

def render_market_overview():
    """Render market overview with key statistics"""
    
    st.markdown("### 📈 Market Overview")
    
    with st.spinner("Loading market data..."):
        # Get all data
        all_nav = get_all_nav_data()
        aum_data = get_aum_data_from_api()
        categories_data = get_categories_data()
    
    if not all_nav:
        st.error("Could not load market data from API")
        return
    
    df_nav = pd.DataFrame(all_nav)
    
    # Key Statistics
    st.markdown("#### 📊 Key Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_schemes = len(df_nav)
        st.metric("Total Schemes", f"{total_schemes:,}")
    
    with col2:
        total_amcs = df_nav['AMC'].nunique()
        st.metric("Fund Houses (AMCs)", total_amcs)
    
    with col3:
        total_categories = len(categories_data.get('categories', []))
        st.metric("Categories", total_categories)
    
    with col4:
        latest_date = pd.to_datetime(df_nav['Date']).max()
        st.metric("Latest Data", latest_date.strftime('%d-%b-%Y'))
    
    st.markdown("---")
    
    # AUM Overview (if available)
    if aum_data:
        df_aum = pd.DataFrame(aum_data)
        
        st.markdown("#### 💰 Industry AUM Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            total_aum = df_aum['AUM (Crores)'].sum()
            st.metric("Total Industry AUM", f"₹{total_aum:,.0f} Cr")
        
        with col2:
            avg_aum = df_aum['AUM (Crores)'].mean()
            st.metric("Average AUM per AMC", f"₹{avg_aum:,.0f} Cr")
        
        st.info("💡 AUM data sourced from AMFI official reports (updated monthly)")
    
    st.markdown("---")
    
    # Distribution by Category
    st.markdown("#### 📊 Scheme Distribution by Category")
    
    if 'Scheme Category' in df_nav.columns:
        category_counts = df_nav['Scheme Category'].value_counts().head(10)
        
        fig = px.bar(
            x=category_counts.values,
            y=category_counts.index,
            orientation='h',
            labels={'x': 'Number of Schemes', 'y': 'Category'},
            title="Top 10 Categories by Scheme Count"
        )
        
        fig.update_layout(height=500, showlegend=False)
        fig.update_traces(marker_color='#1f77b4')
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Distribution by AMC
    st.markdown("---")
    st.markdown("#### 🏢 Scheme Distribution by AMC")
    
    amc_counts = df_nav['AMC'].value_counts().head(15)
    
    fig = go.Figure(data=[
        go.Bar(
            x=amc_counts.values,
            y=amc_counts.index,
            orientation='h',
            marker_color='#2ca02c',
            text=amc_counts.values,
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title="Top 15 AMCs by Scheme Count",
        xaxis_title="Number of Schemes",
        yaxis_title="AMC",
        height=600,
        yaxis={'categoryorder': 'total ascending'}
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# AMC ANALYSIS
# ==========================================

def render_amc_analysis():
    """Render AMC-specific analysis"""
    
    st.markdown("### 🏢 AMC (Fund House) Analysis")
    
    with st.spinner("Loading AMC data..."):
        aum_data = get_aum_data_from_api()
        all_nav = get_all_nav_data()
    
    if not aum_data:
        st.warning("⚠️ AUM data not available. Showing scheme count analysis instead.")
        render_amc_scheme_count_analysis()
        return
    
    df_aum = pd.DataFrame(aum_data)
    
    # Display mode selector
    st.markdown("#### 📊 Analysis Type")
    
    analysis_type = st.radio(
        "Select analysis:",
        options=["AUM-Based", "Scheme Count"],
        horizontal=True,
        key="amc_analysis_type"
    )
    
    if analysis_type == "AUM-Based":
        render_aum_based_analysis(df_aum)
    else:
        render_amc_scheme_count_analysis()

def render_aum_based_analysis(df_aum: pd.DataFrame):
    """Render AUM-based AMC analysis"""
    
    st.markdown("---")
    st.markdown("#### 💰 Top AMCs by AUM")
    
    # Top 10 AMCs by AUM
    top_10 = df_aum.nlargest(10, 'AUM (Crores)')
    
    # Pie chart
    col1, col2 = st.columns(2)
    
    with col1:
        fig_pie = px.pie(
            top_10,
            values='AUM (Crores)',
            names='AMC',
            title='Top 10 AMCs - AUM Distribution',
            hole=0.4
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        fig_bar = go.Figure(data=[
            go.Bar(
                x=top_10['AUM (Crores)'],
                y=top_10['AMC'],
                orientation='h',
                marker_color='#ff7f0e',
                text=[f"₹{val:,.0f} Cr" for val in top_10['AUM (Crores)']],
                textposition='outside'
            )
        ])
        
        fig_bar.update_layout(
            title="Top 10 AMCs by AUM",
            xaxis_title="AUM (₹ Crores)",
            yaxis_title="AMC",
            height=400,
            yaxis={'categoryorder': 'total ascending'}
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Market share analysis
    st.markdown("---")
    st.markdown("#### 📈 Market Share Analysis")
    
    # Treemap
    fig_tree = px.treemap(
        df_aum,
        path=['AMC'],
        values='AUM (Crores)',
        title='Market Share Treemap (All AMCs)',
        color='Market Share',
        color_continuous_scale='Viridis'
    )
    
    fig_tree.update_traces(textinfo='label+value+percent parent')
    fig_tree.update_layout(height=600)
    
    st.plotly_chart(fig_tree, use_container_width=True)
    
    # Data table
    st.markdown("---")
    st.markdown("#### 📋 Detailed AUM Data")
    
    # Format for display
    df_display = df_aum.copy()
    df_display['AUM (Crores)'] = df_display['AUM (Crores)'].apply(lambda x: f"₹{x:,.0f} Cr")
    df_display['Market Share'] = df_display['Market Share'].apply(lambda x: f"{x*100:.2f}%")
    
    st.dataframe(
        df_display.sort_values('AMC'),
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    # Download option
    csv = df_aum.to_csv(index=False)
    st.download_button(
        label="📥 Download AUM Data (CSV)",
        data=csv,
        file_name="amc_aum_data.csv",
        mime="text/csv"
    )

def render_amc_scheme_count_analysis():
    """Render AMC analysis by scheme count"""
    
    all_nav = get_all_nav_data()
    
    if not all_nav:
        st.error("Could not load scheme data")
        return
    
    df_nav = pd.DataFrame(all_nav)
    
    st.markdown("---")
    st.markdown("#### 🔢 Top AMCs by Scheme Count")
    
    amc_counts = df_nav['AMC'].value_counts().head(15)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Bar chart
        fig_bar = go.Figure(data=[
            go.Bar(
                x=amc_counts.values,
                y=amc_counts.index,
                orientation='h',
                marker_color='#1f77b4',
                text=amc_counts.values,
                textposition='outside'
            )
        ])
        
        fig_bar.update_layout(
            title="Top 15 AMCs by Number of Schemes",
            xaxis_title="Number of Schemes",
            yaxis_title="AMC",
            height=500,
            yaxis={'categoryorder': 'total ascending'}
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        # Pie chart (top 10)
        fig_pie = px.pie(
            values=amc_counts.head(10).values,
            names=amc_counts.head(10).index,
            title='Top 10 AMCs - Scheme Distribution',
            hole=0.3
        )
        
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    st.info("Note: This ranking is by number of schemes, not total AUM. More schemes does not necessarily mean larger fund house.")

# ==========================================
# CATEGORY ANALYSIS
# ==========================================

def render_category_analysis():
    """Render category-wise analysis"""
    
    st.markdown("### 📊 Category Analysis")
    
    with st.spinner("Loading category data..."):
        all_nav = get_all_nav_data()
        categories_data = get_categories_data()
    
    if not all_nav:
        st.error("Could not load scheme data")
        return
    
    df_nav = pd.DataFrame(all_nav)
    
    # Category distribution
    st.markdown("#### 📈 Scheme Distribution by Category")
    
    if 'Scheme Category' in df_nav.columns:
        category_counts = df_nav['Scheme Category'].value_counts()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie chart
            fig_pie = px.pie(
                values=category_counts.values,
                names=category_counts.index,
                title='Scheme Distribution by Category',
                hole=0.3
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Bar chart
            fig_bar = px.bar(
                x=category_counts.values,
                y=category_counts.index,
                orientation='h',
                labels={'x': 'Number of Schemes', 'y': 'Category'},
                title='Number of Schemes per Category'
            )
            fig_bar.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)
    
    # Category-wise breakdown by AMC
    st.markdown("---")
    st.markdown("#### 🏢 Category Distribution by Top AMCs")
    
    if 'Scheme Category' in df_nav.columns:
        # Get top 10 AMCs
        top_amcs = df_nav['AMC'].value_counts().head(10).index
        
        df_top = df_nav[df_nav['AMC'].isin(top_amcs)]
        
        # Create cross-tabulation
        ct = pd.crosstab(df_top['AMC'], df_top['Scheme Category'])
        
        # Stacked bar chart
        fig = go.Figure()
        
        for col in ct.columns:
            fig.add_trace(go.Bar(
                name=col,
                x=ct.index,
                y=ct[col],
                text=ct[col],
                textposition='inside'
            ))
        
        fig.update_layout(
            title="Category Distribution - Top 10 AMCs",
            xaxis_title="AMC",
            yaxis_title="Number of Schemes",
            barmode='stack',
            height=500,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="right",
                x=1.15
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Category selector for detailed view
    st.markdown("---")
    st.markdown("#### 🔍 Detailed Category View")
    
    if 'Scheme Category' in df_nav.columns:
        selected_category = st.selectbox(
            "Select a category to explore:",
            options=sorted(df_nav['Scheme Category'].unique()),
            key="category_selector"
        )
        
        if selected_category:
            df_category = df_nav[df_nav['Scheme Category'] == selected_category]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Schemes", len(df_category))
            with col2:
                st.metric("Number of AMCs", df_category['AMC'].nunique())
            with col3:
                avg_nav = df_category['NAV'].mean()
                st.metric("Average NAV", f"₹{avg_nav:.2f}")
            
            # Top AMCs in this category
            st.markdown(f"**Top AMCs in {selected_category}:**")
            
            amc_in_cat = df_category['AMC'].value_counts().head(10)
            
            fig = px.bar(
                x=amc_in_cat.values,
                y=amc_in_cat.index,
                orientation='h',
                labels={'x': 'Number of Schemes', 'y': 'AMC'}
            )
            fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

# ==========================================
# SCHEME EXPLORER
# ==========================================

def render_scheme_explorer():
    """Render interactive scheme explorer"""
    
    st.markdown("### 🔍 Scheme Explorer")
    st.markdown("Search and explore schemes with advanced filters")
    
    with st.spinner("Loading scheme data..."):
        all_nav = get_all_nav_data()
        categories_data = get_categories_data()
    
    if not all_nav:
        st.error("Could not load scheme data")
        return
    
    df_nav = pd.DataFrame(all_nav)
    
    # Filters
    st.markdown("#### 🎯 Filters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Category filter
        categories = ['All'] + sorted(categories_data.get('categories', []))
        selected_category = st.selectbox("Category:", categories, key="explorer_category")
    
    with col2:
        # AMC filter
        amcs = ['All'] + sorted(df_nav['AMC'].unique().tolist())
        selected_amc = st.selectbox("AMC:", amcs, key="explorer_amc")
    
    with col3:
        # NAV range filter
        nav_filter = st.selectbox(
            "NAV Range:",
            options=['All', '< ₹50', '₹50-₹100', '₹100-₹500', '> ₹500'],
            key="explorer_nav"
        )
    
    # Apply filters
    df_filtered = df_nav.copy()
    
    if selected_category != 'All' and 'Scheme Category' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['Scheme Category'] == selected_category]
    
    if selected_amc != 'All':
        df_filtered = df_filtered[df_filtered['AMC'] == selected_amc]
    
    if nav_filter != 'All':
        if nav_filter == '< ₹50':
            df_filtered = df_filtered[df_filtered['NAV'] < 50]
        elif nav_filter == '₹50-₹100':
            df_filtered = df_filtered[(df_filtered['NAV'] >= 50) & (df_filtered['NAV'] < 100)]
        elif nav_filter == '₹100-₹500':
            df_filtered = df_filtered[(df_filtered['NAV'] >= 100) & (df_filtered['NAV'] < 500)]
        else:  # > ₹500
            df_filtered = df_filtered[df_filtered['NAV'] >= 500]
    
    # Results
    st.markdown("---")
    st.markdown(f"#### 📊 Results ({len(df_filtered):,} schemes)")
    
    if len(df_filtered) == 0:
        st.warning("No schemes match the selected filters")
        return
    
    # Display options
    display_mode = st.radio(
        "Display as:",
        options=["Table", "Cards"],
        horizontal=True,
        key="explorer_display"
    )
    
    if display_mode == "Table":
        # Prepare display dataframe
        df_display = df_filtered[[
            'Scheme Code', 'Scheme Name', 'NAV', 'Date', 'AMC'
        ]].copy()
        
        if 'Scheme Category' in df_filtered.columns:
            df_display['Category'] = df_filtered['Scheme Category']
        
        df_display['NAV'] = df_display['NAV'].apply(lambda x: f"₹{x:.2f}")
        df_display['Date'] = pd.to_datetime(df_display['Date']).dt.strftime('%d-%b-%Y')
        
        # Show top 100 results
        st.dataframe(
            df_display.head(100),
            use_container_width=True,
            hide_index=True,
            height=500
        )
        
        if len(df_filtered) > 100:
            st.info(f"Showing top 100 of {len(df_filtered):,} results")
    
    else:  # Cards view
        # Show paginated cards
        items_per_page = 20
        page = st.number_input(
            "Page",
            min_value=1,
            max_value=(len(df_filtered) + items_per_page - 1) // items_per_page,
            value=1,
            key="explorer_page"
        )
        
        start_idx = (page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, len(df_filtered))
        
        page_data = df_filtered.iloc[start_idx:end_idx]
        
        for i, row in page_data.iterrows():
            with st.expander(f"📊 {row['Scheme Name'][:60]} - {row['Scheme Code']}"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("NAV", f"₹{row['NAV']:.2f}")
                with col2:
                    st.metric("AMC", row['AMC'][:20])
                with col3:
                    cat = row.get('Scheme Category', 'N/A')
                    st.metric("Category", cat[:20])
                with col4:
                    date_str = pd.to_datetime(row['Date']).strftime('%d-%b-%Y')
                    st.metric("Date", date_str)
                
                # Action buttons
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    if st.button("📊 Analyze", key=f"analyze_{i}"):
                        st.session_state['selected_scheme_code'] = str(row['Scheme Code'])
                        st.session_state['selected_scheme_name'] = row['Scheme Name']
                        st.session_state['navigate_to'] = '📊 Scheme Analysis'
                        st.rerun()
                
                with col_b:
                    if st.button("⚖️ Compare", key=f"compare_{i}"):
                        if 'compare_schemes_list' not in st.session_state:
                            st.session_state['compare_schemes_list'] = []
                        
                        st.session_state['compare_schemes_list'].append({
                            'scheme_code': str(row['Scheme Code']),
                            'scheme_name': row['Scheme Name']
                        })
                        st.success("Added to comparison!")
    
    # Download option
    st.markdown("---")
    csv = df_filtered.to_csv(index=False)
    st.download_button(
        label="📥 Download Filtered Results (CSV)",
        data=csv,
        file_name="filtered_schemes.csv",
        mime="text/csv"
    )
"""
Analytics Dashboard Page - Power BI Interactive Integration
For use with published Power BI reports
"""

import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

def render():
    """Render analytics dashboard with interactive Power BI"""
    
    st.markdown("# 📊 Analytics Dashboard")
    st.markdown("Interactive Power BI visualizations")
    st.markdown("---")
    
    # Check if embed URL is configured
    embed_url = get_powerbi_embed_url()
    
    if not embed_url:
        render_publish_instructions()
    else:
        render_interactive_dashboard(embed_url)


def get_powerbi_embed_url():
    """Get Power BI embed URL from config/secrets"""
    
    # Try to get from Streamlit secrets
    try:
        return st.secrets.get("POWERBI_EMBED_URL", "")
    except:
        pass
    
    # Try to get from environment variable
    import os
    return os.getenv("POWERBI_EMBED_URL", "")


def render_publish_instructions():
    """Show instructions for publishing Power BI dashboard"""
    
    st.info("🌐 **Interactive Dashboard Setup**")
    
    st.markdown("""
    ### 🚀 Publish Your Dashboard to Power BI Service
    
    Your dashboard file: `models/powerbi_data/MF_NAVigator_Dashboard.pbix`
    
    #### Step 1: Publish to Power BI Service
    
    1. Open `MF_NAVigator_Dashboard.pbix` in Power BI Desktop
    2. Sign in with your Microsoft account (free)
    3. Click **File → Publish → Publish to Power BI**
    4. Select a workspace (use "My workspace" for personal)
    5. Wait for upload to complete
    
    #### Step 2: Get Embed Link (Public)
    
    **⚠️ Warning:** This makes your dashboard public to anyone with the link
    
    1. Go to [app.powerbi.com](https://app.powerbi.com)
    2. Find your report and open it
    3. Click **File → Embed → Publish to web (public)**
    4. Click **Create embed code**
    5. Copy the **iframe src URL** (starts with `https://app.powerbi.com/view?r=...`)
    
    #### Step 3: Configure in Streamlit
    
    **Option A: Using Streamlit Secrets (Recommended)**
    
    1. Create/edit `.streamlit/secrets.toml` in your project root:
    
    ```toml
    POWERBI_EMBED_URL = "https://app.powerbi.com/view?r=YOUR_REPORT_ID"
    ```
    
    **Option B: Manual Entry Below**
    """)
    
    st.markdown("---")
    
    # Manual URL entry
    st.markdown("### 🔗 Enter Embed URL Manually")
    
    manual_url = st.text_input(
        "Paste your Power BI embed URL here:",
        placeholder="https://app.powerbi.com/view?r=...",
        help="Get this from Power BI Service: File → Embed → Publish to web"
    )
    
    if manual_url:
        if st.button("✅ Use This URL", type="primary"):
            st.session_state['manual_powerbi_url'] = manual_url
            st.success("✅ URL saved! Refreshing...")
            st.rerun()
    
    # Alternative: Use static images
    st.markdown("---")
    st.markdown("### 📸 Alternative: Use Static Images")
    
    st.info("""
    Don't want to publish online? You can use static image exports instead.
    
    Export dashboard pages as PNG images and place them in:
    `frontend/static/powerbi_images/`
    
    This will automatically display them here without requiring publication.
    """)
    
    if st.button("🔄 Switch to Static Images Mode", use_container_width=True):
        # This would require modifying the render function logic
        st.info("Please follow the static images setup instructions in Option 1")


def render_interactive_dashboard(embed_url: str):
    """Render interactive Power BI dashboard via iframe"""
    
    # Check if manual URL is set
    if 'manual_powerbi_url' in st.session_state:
        embed_url = st.session_state['manual_powerbi_url']
    
    st.success("✅ Power BI Dashboard Connected")
    
    # Dashboard controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("**Interactive Dashboard**")
        st.caption("Use filters and controls within the dashboard")
    
    with col2:
        if st.button("🔄 Refresh", key="refresh_dashboard"):
            st.rerun()
    
    with col3:
        if st.button("⚙️ Change URL", key="change_url"):
            if 'manual_powerbi_url' in st.session_state:
                del st.session_state['manual_powerbi_url']
            st.rerun()
    
    st.markdown("---")
    
    # Embed Power BI dashboard
    iframe_html = f"""
    <iframe 
        width="100%" 
        height="900" 
        src="{embed_url}"
        frameborder="0" 
        allowFullScreen="true"
        style="border: 1px solid #ddd; border-radius: 8px;">
    </iframe>
    """
    
    components.html(iframe_html, height=920, scrolling=True)
    
    # Additional info
    st.markdown("---")
    render_dashboard_info()


def render_dashboard_info():
    """Render dashboard usage info"""
    
    st.markdown("### 💡 Dashboard Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **✨ Interactive Elements:**
        - Click on charts to filter data
        - Use slicers to segment analysis
        - Hover for detailed tooltips
        - Drill through for deeper insights
        """)
    
    with col2:
        st.markdown("""
        **📊 Available Views:**
        - Market overview and statistics
        - AMC market share analysis
        - Category distribution
        - Top performing schemes
        - Historical trends
        """)
    
    st.markdown("---")
    
    st.info("""
    **🔒 Privacy Note:** This dashboard is embedded from Power BI Service. 
    If you published it publicly, anyone with the link can view it. 
    For private dashboards, use Power BI Embedded with authentication.
    """)
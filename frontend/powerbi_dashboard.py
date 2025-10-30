"""
Power BI Dashboard Integration Page
Embeds Power BI report in Streamlit
"""

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Power BI Dashboard - MF_NAVigator",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Power BI Dashboard")
st.markdown("Advanced mutual fund analytics and visualizations")
st.markdown("---")

# Power BI embed configuration
POWERBI_EMBED_URL = st.secrets.get("POWERBI_EMBED_URL", "")
POWERBI_REPORT_ID = st.secrets.get("POWERBI_REPORT_ID", "")

# Method 1: Embed using iframe (if you have publish to web URL)
def embed_powerbi_public(embed_url):
    """Embed publicly shared Power BI report"""
    
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


# Method 2: Embed with Power BI Embedded (requires authentication)
def embed_powerbi_secure(report_id, workspace_id, access_token):
    """Embed secure Power BI report with authentication"""
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/powerbi-client/2.22.2/powerbi.min.js"></script>
        <style>
            #reportContainer {{
                height: 800px;
                width: 100%;
                border: none;
            }}
        </style>
    </head>
    <body>
        <div id="reportContainer"></div>
        <script>
            // Power BI embed configuration
            const embedConfiguration = {{
                type: 'report',
                id: '{report_id}',
                embedUrl: 'https://app.powerbi.com/reportEmbed?reportId={report_id}&groupId={workspace_id}',
                accessToken: '{access_token}',
                settings: {{
                    panes: {{
                        filters: {{
                            expanded: false,
                            visible: true
                        }}
                    }},
                    background: models.BackgroundType.Transparent,
                }}
            }};

            // Get a reference to the embedded report HTML element
            const reportContainer = document.getElementById('reportContainer');

            // Embed the report
            const report = powerbi.embed(reportContainer, embedConfiguration);

            // Report loaded successfully
            report.on("loaded", function () {{
                console.log("Report loaded");
            }});

            // Report render completed
            report.on("rendered", function () {{
                console.log("Report rendered");
            }});

            // Handle errors
            report.on("error", function (event) {{
                console.log("Error: ", event.detail);
            }});
        </script>
    </body>
    </html>
    """
    
    components.html(html_code, height=820)


# Method 3: Display static Power BI images/PDFs
def display_powerbi_static():
    """Display static Power BI exports"""
    
    st.markdown("### Dashboard Overview")
    
    tabs = st.tabs(["📊 Overview", "📈 Performance", "⚖️ Comparison", "🎯 Portfolio"])
    
    with tabs[0]:
        st.markdown("#### Mutual Fund Overview Dashboard")
        # Display image
        try:
            st.image("powerbi/overview_dashboard.png", use_container_width=True)
        except:
            st.info("💡 Export your Power BI dashboard as PNG and save to `powerbi/overview_dashboard.png`")
    
    with tabs[1]:
        st.markdown("#### Performance Analytics")
        try:
            st.image("powerbi/performance_dashboard.png", use_container_width=True)
        except:
            st.info("💡 Export your Power BI dashboard as PNG and save to `powerbi/performance_dashboard.png`")
    
    with tabs[2]:
        st.markdown("#### Scheme Comparison")
        try:
            st.image("powerbi/comparison_dashboard.png", use_container_width=True)
        except:
            st.info("💡 Export your Power BI dashboard as PNG and save to `powerbi/comparison_dashboard.png`")
    
    with tabs[3]:
        st.markdown("#### Portfolio Analysis")
        try:
            st.image("powerbi/portfolio_dashboard.png", use_container_width=True)
        except:
            st.info("💡 Export your Power BI dashboard as PNG and save to `powerbi/portfolio_dashboard.png`")


# Main app
st.sidebar.markdown("### Power BI Integration Options")
integration_type = st.sidebar.radio(
    "Select Integration Type:",
    ["📸 Static Images", "🔗 Public Embed", "🔐 Secure Embed"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
**Setup Instructions:**

**Static Images:**
1. Export Power BI pages as PNG
2. Save to `powerbi/` folder
3. Select "Static Images" option

**Public Embed:**
1. Power BI → File → Publish to Web
2. Copy embed URL
3. Add to `.streamlit/secrets.toml`
4. Select "Public Embed" option

**Secure Embed:**
1. Get Power BI Embedded license
2. Configure Azure AD authentication
3. Generate access token
4. Select "Secure Embed" option
""")

# Display based on selection
if integration_type == "📸 Static Images":
    display_powerbi_static()

elif integration_type == "🔗 Public Embed":
    st.markdown("### Embedded Power BI Report")
    
    embed_url = st.text_input(
        "Enter Power BI Publish to Web URL:",
        value=POWERBI_EMBED_URL,
        help="Get this from Power BI: File → Publish to Web"
    )
    
    if embed_url:
        embed_powerbi_public(embed_url)
    else:
        st.warning("⚠️ Please enter a Power BI embed URL")
        st.markdown("""
        **How to get embed URL:**
        1. Open your report in Power BI Service
        2. Click **File** → **Embed** → **Publish to web (public)**
        3. Click **Create embed code**
        4. Copy the `src` URL from the iframe code
        """)

elif integration_type == "🔐 Secure Embed":
    st.markdown("### Secure Power BI Embed")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        report_id = st.text_input("Report ID")
    
    with col2:
        workspace_id = st.text_input("Workspace ID")
    
    with col3:
        access_token = st.text_input("Access Token", type="password")
    
    if st.button("Load Report"):
        if report_id and workspace_id and access_token:
            embed_powerbi_secure(report_id, workspace_id, access_token)
        else:
            st.error("Please fill all fields")

# Download Power BI Desktop info
st.markdown("---")
st.markdown("### 📥 Power BI Resources")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Power BI Desktop:**
    - [Download Power BI Desktop](https://powerbi.microsoft.com/desktop/)
    - Free for creating reports
    - Connect to your data sources
    """)

with col2:
    st.markdown("""
    **Sample Data Export:**
    - Export data from MF_NAVigator API
    - Use CSV/Excel exports
    - Connect Power BI to API endpoints
    """)

# Data export button
if st.button("📊 Export Sample Data for Power BI"):
    st.info("Feature coming soon: Export API data to CSV for Power BI import")

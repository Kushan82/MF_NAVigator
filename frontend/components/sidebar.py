"""
Reusable sidebar component
"""

import streamlit as st
import requests

def render_sidebar():
    """Render sidebar navigation and return selected page"""
    
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/000000/profit-report.png", width=80)
        st.markdown("# 📈 MF_NAVigator")
        st.markdown("---")
        
        # Navigation
        page = st.radio(
            "Navigation",
            [
                "🏠 Home",
                "📊 Scheme Analysis",
                "📈 Portfolio Builder",
                "🤖 NAV Predictions",
                "⚖️ Compare Schemes",
                "📊 Analytics Dashboard",
                "📰 Market News"
            ],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # API Status
        api_status = check_api_status()
        if api_status:
            st.success("🟢 API Connected")
        else:
            st.error("🔴 API Offline")
        
        st.markdown("---")
        render_about_section()
        
        return page


def check_api_status():
    """Check if API is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def render_about_section():
    """Render about section in sidebar"""
    st.markdown("### About")
    st.markdown("""
    **MF_NAVigator** is an AI-powered mutual fund analytics platform.
    
    **Features:**
    - 9,000+ Indian mutual funds
    - 23+ financial metrics
    - ML-powered predictions
    - Portfolio optimization
    - Advanced analytics
    """)
    
    st.markdown("---")
    st.markdown("**Version:** 1.0.0")
    st.markdown("**Tech:** Python, FastAPI, Streamlit, XGBoost")

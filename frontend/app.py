"""
MF_NAVigator - Streamlit Frontend
Main application entry point with page routing
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Page configuration
st.set_page_config(
    page_title="MF_NAVigator",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# HIDE DEFAULT STREAMLIT NAVIGATION
# ==========================================
hide_streamlit_nav = """
<style>
    /* Hide the default Streamlit page navigation */
    [data-testid="stSidebarNav"] {
        display: none;
    }
    
    /* Hide the default page links list */
    section[data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    /* Alternative: Hide entire nav section */
    .css-1544g2n {
        display: none;
    }
</style>
"""
st.markdown(hide_streamlit_nav, unsafe_allow_html=True)

# ==========================================
# Initialize Session State
# ==========================================

if 'compare_schemes_list' not in st.session_state:
    st.session_state['compare_schemes_list'] = []

if 'portfolio_schemes_list' not in st.session_state:
    st.session_state['portfolio_schemes_list'] = []

if 'navigate_to' not in st.session_state:
    st.session_state['navigate_to'] = None

if 'selected_scheme_code' not in st.session_state:
    st.session_state['selected_scheme_code'] = None

if 'selected_scheme_name' not in st.session_state:
    st.session_state['selected_scheme_name'] = None

if 'show_add_form' not in st.session_state:
    st.session_state['show_add_form'] = False

if 'run_comparison' not in st.session_state:
    st.session_state['run_comparison'] = False

if 'run_analysis' not in st.session_state:
    st.session_state['run_analysis'] = False

if 'run_prediction' not in st.session_state:
    st.session_state['run_prediction'] = False

# ==========================================
# Load Components
# ==========================================

from frontend.components.sidebar import render_sidebar
from frontend.utils.config import load_custom_css

# Import pages
from frontend.pages import (
    home,
    scheme_analysis,
    portfolio_builder,
    nav_predictions,
    compare_schemes,
    analytics_dashboard
)

# Load custom styling
load_custom_css()

# ==========================================
# Page Routing
# ==========================================

PAGE_MAP = {
    "🏠 Home": home,
    "📊 Scheme Analysis": scheme_analysis,
    "📈 Portfolio Builder": portfolio_builder,
    "🤖 NAV Predictions": nav_predictions,
    "⚖️ Compare Schemes": compare_schemes,
    "📊 Analytics Dashboard": analytics_dashboard
}

# Determine which page to show
if st.session_state.get('navigate_to'):
    page = st.session_state['navigate_to']
else:
    page = render_sidebar()

# Render selected page
if page in PAGE_MAP:
    PAGE_MAP[page].render()
    
    if st.session_state.get('navigate_to') == page:
        st.session_state['navigate_to'] = None
else:
    st.error(f"❌ Page not found: '{page}'")

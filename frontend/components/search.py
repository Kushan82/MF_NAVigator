"""
Reusable search component
"""

import streamlit as st
import pandas as pd
from frontend.utils.api_client import APIClient

api = APIClient()


def render_scheme_search(key_prefix: str = "search", label: str = "Search Scheme"):
    """
    Render scheme search component
    
    Args:
        key_prefix: Prefix for session state keys
        label: Label for search input
    
    Returns:
        Selected scheme code or None
    """
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input(
            label,
            key=f"{key_prefix}_query",
            placeholder="Enter scheme name or AMC"
        )
    
    with col2:
        st.write("")  # Spacer
        st.write("")  # Spacer
        search_btn = st.button("🔍 Search", key=f"{key_prefix}_btn", use_container_width=True)
    
    if search_query and search_btn:
        results = api.search_schemes(search_query, limit=20)
        
        if results and results['total_results'] > 0:
            df = pd.DataFrame(results['schemes'])
            
            selected = st.selectbox(
                "Select Scheme:",
                options=df['scheme_code'].tolist(),
                format_func=lambda x: df[df['scheme_code']==x]['scheme_name'].iloc[0],
                key=f"{key_prefix}_select"
            )
            
            return selected
        else:
            st.warning("No schemes found")
    
    return None

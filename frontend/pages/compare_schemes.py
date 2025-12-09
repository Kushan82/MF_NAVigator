"""
Compare Schemes Page - COMPLETE FIXED VERSION
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from frontend.utils.api_client import APIClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api = APIClient()

# =========================
# MAIN RENDER FUNCTION
# =========================

def render():
    """Main render function"""
    st.markdown("# ⚖️ Compare Schemes")
    st.markdown("Side-by-side comparison with advanced analytics")
    st.markdown("---")
    
    # Initialize session state
    if "compare_schemes_list" not in st.session_state:
        st.session_state["compare_schemes_list"] = []
    
    # Clean up any string entries
    clean_schemes = []
    for item in st.session_state["compare_schemes_list"]:
        if isinstance(item, dict) and "scheme_code" in item:
            clean_schemes.append(item)
        elif isinstance(item, str):
            clean_schemes.append({"scheme_code": item, "scheme_name": item})
    
    st.session_state["compare_schemes_list"] = clean_schemes
    
    # Render appropriate interface
    num_schemes = len(st.session_state["compare_schemes_list"])
    
    if num_schemes >= 2:
        render_comparison_interface()
    elif num_schemes == 1:
        st.info("👆 Added 1 scheme. Add at least one more to compare.")
        render_add_scheme_interface()
    else:
        st.info("👆 No schemes added yet. Add at least 2 schemes to compare.")
        render_add_scheme_interface()

# =========================
# ADD SCHEME INTERFACE
# =========================

def render_add_scheme_interface():
    """Render add scheme interface"""
    st.markdown("### ➕ Add Schemes to Compare")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_query = st.text_input(
            "Search by scheme name or AMC:",
            placeholder="Type at least 2 characters",
            key="compare_search_input"
        )
    
    with col2:
        limit = st.number_input("Max Results", min_value=5, max_value=50, value=20, key="compare_search_limit")
    
    with col3:
        st.write("")
        st.write("")
        search_btn = st.button("🔍 Search", key="compare_search_btn", use_container_width=True)
    
    # Handle search
    if search_btn and search_query and len(search_query.strip()) >= 2:
        with st.spinner("Searching..."):
            try:
                results = api.search_schemes(search_query.strip(), limit=limit)
                schemes = []
                
                if isinstance(results, dict) and results.get("total_results", 0) > 0:
                    schemes = results.get("schemes", [])
                
                if schemes:
                    st.session_state["compare_search_results"] = schemes
                    st.success(f"✅ Found {len(schemes)} schemes")
                else:
                    st.warning("No schemes found")
            
            except Exception as e:
                st.error(f"Search failed: {e}")
                logger.error(f"Search error: {e}", exc_info=True)
    
    # Display search results
    results = st.session_state.get("compare_search_results", [])
    
    if results:
        st.markdown("---")
        st.markdown("#### 📋 Search Results")
        
        for i, item in enumerate(results):
            scheme_code = str(item.get("scheme_code", "") or item.get("Scheme Code", ""))
            scheme_name = item.get("scheme_name", "") or item.get("Scheme Name", "N/A")
            current_nav = item.get("current_nav", None) or item.get("NAV", None)
            amc = item.get("amc", "") or item.get("AMC", "N/A")
            
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            
            with c1:
                st.text(f"{scheme_name[:60]}...")
            
            with c2:
                if current_nav is not None and pd.notna(current_nav):
                    st.text(f"₹{float(current_nav):.2f}")
                else:
                    st.text("₹N/A")
            
            with c3:
                st.text(amc[:18])
            
            with c4:
                # Check if already added
                already = any(
                    (s.get("scheme_code") if isinstance(s, dict) else s) == scheme_code
                    for s in st.session_state["compare_schemes_list"]
                )
                
                if already:
                    st.button("✓ Added", key=f"added_{i}", disabled=True, use_container_width=True)
                else:
                    if st.button("➕ Add", key=f"add_{i}", use_container_width=True):
                        st.session_state["compare_schemes_list"].append({
                            "scheme_code": scheme_code,
                            "scheme_name": scheme_name
                        })
                        st.rerun()

# =========================
# COMPARISON INTERFACE
# =========================

def render_comparison_interface():
    """Render comparison interface"""
    schemes = st.session_state["compare_schemes_list"]
    
    # Extract scheme codes safely
    scheme_codes = []
    for s in schemes:
        if isinstance(s, dict):
            code = s.get("scheme_code", "")
            if code:
                scheme_codes.append(code)
        elif isinstance(s, str):
            scheme_codes.append(s)
    
    if not scheme_codes:
        st.error("❌ No valid scheme codes found")
        return
    
    st.markdown(f"### Comparing {len(scheme_codes)} Schemes")
    
    # Display scheme buttons
    max_cols = min(len(schemes) + 1, 6)
    cols = st.columns(max_cols)
    
    for i, s in enumerate(schemes):
        col_idx = i % 5 if len(schemes) < 5 else i % max_cols
        
        with cols[col_idx]:
            # Get name safely
            if isinstance(s, dict):
                name = s.get("scheme_name", s.get("scheme_code", "Unknown"))
            else:
                name = s
            
            if st.button(f"❌ {name[:20]}", key=f"remove_{i}", use_container_width=True):
                st.session_state["compare_schemes_list"].pop(i)
                st.rerun()
    
    # Add more button
    last_col_idx = len(schemes) % 5 if len(schemes) < 5 else max_cols - 1
    with cols[last_col_idx]:
        if st.button("➕ Add More", key="add_more_btn", use_container_width=True):
            st.session_state["show_add_form"] = True
    
    # Show add form if requested
    if st.session_state.get("show_add_form"):
        st.markdown("---")
        render_add_scheme_interface()
        
        if st.button("❌ Close Add Form", key="close_add_form"):
            st.session_state["show_add_form"] = False
            st.rerun()
    
    st.markdown("---")
    
    # Fetch comparison data
    with st.spinner("📊 Fetching comparison data..."):
        comp_data = fetch_comparison_data(scheme_codes)
        
        if not comp_data or not isinstance(comp_data, dict):
            st.error("❌ Could not fetch comparison data from API")
            st.info("💡 Ensure backend is running")
            return
        
        if not comp_data.get("comparison"):
            st.warning("⚠️ No comparison data available")
            return
    
    # Display comparison tabs
    tab1, tab2 = st.tabs(["📊 Metrics Table", "📈 Performance Chart"])
    
    with tab1:
        render_metrics_table(comp_data)
    
    with tab2:
        render_performance_chart(scheme_codes)

# =========================
# FETCH COMPARISON DATA
# =========================

def fetch_comparison_data(scheme_codes: list):
    """Fetch comparison data from API"""
    try:
        # Try POST
        res = api._make_request(
            "POST",
            f"{api.api_v1}/analytics/compare",
            json=scheme_codes,
            show_error=False
        )
        
        if isinstance(res, dict) and res.get("comparison"):
            return res
        
        # Fallback to GET
        res = api._make_request(
            "GET",
            f"{api.api_v1}/analytics/compare",
            params={"scheme_codes": scheme_codes},
            show_error=False
        )
        
        if isinstance(res, dict) and res.get("comparison"):
            return res
    
    except Exception as e:
        logger.error(f"Comparison fetch error: {e}", exc_info=True)
    
    return None

# =========================
# METRICS TABLE
# =========================

def render_metrics_table(comp_data: dict):
    """Render metrics comparison table"""
    st.markdown("### 📋 Performance Metrics Comparison")
    
    comparison = comp_data.get("comparison", [])
    
    if not comparison:
        st.warning("No comparison data available")
        return
    
    try:
        df = pd.DataFrame(comparison)
        
        # Get scheme names
        scheme_names = {}
        for s in st.session_state.get("compare_schemes_list", []):
            if isinstance(s, dict):
                scheme_names[s.get("scheme_code", "")] = s.get("scheme_name", "Unknown")
        
        if "scheme_code" in df.columns:
            df["Scheme Name"] = df["scheme_code"].map(lambda x: scheme_names.get(x, x)[:40])
        
        # Select columns
        preferred_cols = [
            "Scheme Name", "current_nav", "cagr", "annualized_return",
            "sharpe_ratio", "sortino_ratio", "volatility", "max_drawdown"
        ]
        
        display_cols = [c for c in preferred_cols if c in df.columns]
        
        if not display_cols:
            st.warning("No metrics to display")
            return
        
        df_display = df[display_cols].copy()
        
        # Format columns
        if "current_nav" in df_display.columns:
            df_display["current_nav"] = df_display["current_nav"].apply(
                lambda x: f"₹{x:.2f}" if pd.notna(x) else "N/A"
            )
        
        for col in ["cagr", "annualized_return", "volatility", "max_drawdown"]:
            if col in df_display.columns:
                df_display[col] = df_display[col].apply(
                    lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A"
                )
        
        for col in ["sharpe_ratio", "sortino_ratio"]:
            if col in df_display.columns:
                df_display[col] = df_display[col].apply(
                    lambda x: f"{x:.3f}" if pd.notna(x) else "N/A"
                )
        
        # Rename headers
        rename_map = {
            "Scheme Name": "Scheme",
            "current_nav": "Current NAV",
            "cagr": "CAGR",
            "annualized_return": "Ann. Return",
            "sharpe_ratio": "Sharpe",
            "sortino_ratio": "Sortino",
            "volatility": "Volatility",
            "max_drawdown": "Max DD"
        }
        
        df_display = df_display.rename(columns=rename_map)
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    except Exception as e:
        st.error(f"Error displaying metrics: {e}")
        logger.error(f"Metrics error: {e}", exc_info=True)

# =========================
# PERFORMANCE CHART
# =========================

def render_performance_chart(scheme_codes: list):
    """Render normalized performance chart"""
    st.markdown("### 📈 Normalized Performance")
    
    # Get scheme names
    scheme_names = {}
    for s in st.session_state.get("compare_schemes_list", []):
        if isinstance(s, dict):
            scheme_names[s.get("scheme_code", "")] = s.get("scheme_name", "Unknown")
    
    fig = go.Figure()
    colors = px.colors.qualitative.Plotly
    
    for i, code in enumerate(scheme_codes):
        try:
            res = api.get_historical_data(code, days=365)
            
            if not res:
                continue
            
            # Handle both response formats
            if isinstance(res, dict) and "history" in res:
                data = res["history"]
            elif isinstance(res, list):
                data = res
            else:
                continue
            
            df = pd.DataFrame(data)
            
            # Normalize column names
            if "Date" in df.columns:
                df = df.rename(columns={"Date": "date"})
            if "NAV" in df.columns:
                df = df.rename(columns={"NAV": "nav"})
            
            if "date" not in df.columns or "nav" not in df.columns:
                continue
            
            df = df.dropna(subset=["date", "nav"])
            
            if df.empty or df["nav"].iloc[0] == 0:
                continue
            
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")
            
            df["normalized_nav"] = (df["nav"] / df["nav"].iloc[0]) * 100.0
            
            fig.add_trace(go.Scatter(
                x=df["date"],
                y=df["normalized_nav"],
                mode="lines",
                name=scheme_names.get(code, code)[:30],
                line=dict(width=2, color=colors[i % len(colors)])
            ))
        
        except Exception as e:
            logger.warning(f"Failed to load history for {code}: {e}")
            continue
    
    if not fig.data:
        st.warning("Could not load historical data")
        return
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Normalized Value (Base = 100)",
        hovermode="x unified",
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Entry point
if __name__ == "__main__":
    render()

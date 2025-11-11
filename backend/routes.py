"""
API routes for MF_NAVigator
All REST API endpoints for the application
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict
from datetime import datetime
import pandas as pd
import json
import uuid
from pathlib import Path
from pydantic import BaseModel
import logging # Added logging

# --- Robust Path Setup ---
# This ensures that we can import from the 'data' module
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)
# --- End Path Setup ---

# --- FIXED DATA IMPORTS ---
# We are REMOVING the old, problematic fetchers
# from data.fetch_aum_data import RealAUMDataFetcher
# from data.fetch_data import MutualFundDataFetcher
#
# And ADDING the new, centralized data_fetcher functions
try:
    from data.data_fetcher import (
        get_enhanced_nav_data,  # Replaces mf_data_fetcher.get_all_nav()
        get_nav_history,        # Replaces mf_data_fetcher.get_nav_history()
        get_aum_data            # Replaces aum_fetcher.get_aum_data()
    )
    logging.info("Successfully imported from data.data_fetcher")
except ImportError as e:
    logging.error(f"Failed to import from data.data_fetcher: {e}")
    logging.info(f"Python Path: {sys.path}")
    # This will stop the server if the crucial data module can't be found
    raise e
# --- END FIXED DATA IMPORTS ---


# --- ORIGINAL IMPORTS (Unchanged) ---
# We keep all your other imports to preserve functionality
from backend.schemas import *
from analytics.financial_metrics import FinancialMetricsCalculator
from analytics.risk_metrics import RiskMetricsCalculator
from analytics.portfolio_analysis import PortfolioAnalyzer
from analytics.comparison import SchemeComparator
from models.predictor import NAVPredictor
from backend.agents.news_agent import NewsAgent
# =========================================


# =========================================
# PORTFOLIO MODELS (Pydantic) - (Unchanged)
# =========================================

class PortfolioScheme(BaseModel):
    scheme_code: str
    scheme_name: str
    weight: float


class PortfolioRequest(BaseModel):
    name: str
    description: str = ""
    schemes: List[PortfolioScheme]
    created_at: str
    total_weight: float


class PortfolioResponse(BaseModel):
    success: bool
    portfolio_id: str = None
    message: str = ""
    error: str = None

class PredictionRequestModel(BaseModel):
    scheme_code: str
    forecast_days: int = 30

# =========================================
# ROUTER & CLASS INSTANTIATIONS
# =========================================
router = APIRouter()

# --- REMOVED OLD FETCHERS ---
# mf_data_fetcher = MutualFundDataFetcher()
# aum_fetcher = RealAUMDataFetcher()
# --- END REMOVED ---

# --- KEPT ORIGINAL CLASSES ---
# These are kept so your analytics routes continue to work
metrics_calculator = FinancialMetricsCalculator()
risk_calculator = RiskMetricsCalculator()
comparator = SchemeComparator()
predictor = NAVPredictor()
news_agent = NewsAgent()
# --- END KEPT ---


# Portfolio storage (Unchanged)
PORTFOLIO_DIR = Path(__file__).parent / "data" / "portfolios"
PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)


# =========================================
# NAV DATA ENDPOINTS (Refactored)
# =========================================

@router.get("/nav", response_model=List[dict], summary="Get latest NAV for all schemes")
async def get_all_nav():
    """
    Get the latest NAV for all mutual fund schemes.
    --- FIXED ---
    This now uses `get_enhanced_nav_data()` to include categories
    and returns a JSON list, just like the old endpoint.
    """
    try:
        # --- FIXED ---
        # nav_data = mf_data_fetcher.get_all_nav() # Old code
        nav_data_df = get_enhanced_nav_data() # New code
        # --- END FIX ---

        if nav_data_df.empty:
            return []
        
        # Convert date to string for JSON compatibility
        nav_data_df['Date'] = nav_data_df['Date'].astype(str)
        nav_data = nav_data_df.to_dict('records')
        return nav_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nav/history/{scheme_code}", response_model=List[dict], summary="Get NAV history")
async def get_scheme_nav_history(scheme_code: str):
    """
    Get the NAV history for a specific scheme.
    --- FIXED ---
    This now uses `get_nav_history()` from the new data fetcher.
    It returns a JSON list, just like the old endpoint.
    """
    try:
        # --- FIXED ---
        # history = mf_data_fetcher.get_nav_history(scheme_code) # Old code
        history_df = get_nav_history(scheme_code) # New code
        # --- END FIX ---
        
        if history_df.empty:
            raise HTTPException(status_code=404, detail="NAV history not found")
        
        # Convert date to string for JSON compatibility
        history_df['date'] = history_df['date'].astype(str)
        history = history_df.to_dict('records')
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nav/amc", response_model=List[dict], summary="Get AUM data for all AMCs")
async def get_aum_data_all_amcs():
    """
    Get the latest AUM data for all AMCs.
    --- FIXED ---
    This now uses `get_aum_data()` to fetch *correct*, reported AUM.
    """
    try:
        # --- FIXED ---
        # aum_data = aum_fetcher.get_aum_data() # Old code
        aum_data_df = get_aum_data() # New code
        # --- END FIX ---

        if aum_data_df.empty:
            raise HTTPException(status_code=404, detail="AUM data not found")
        
        return aum_data_df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nav/categories", response_model=dict, summary="Get scheme categories and types")
async def get_scheme_categories_and_types():
    """
    Get all unique scheme categories and types.
    --- FIXED ---
    This now reads from `get_enhanced_nav_data()` to find
    all unique, real categories.
    """
    try:
        # --- FIXED ---
        # categories = mf_data_fetcher.get_categories_and_types() # Old code
        nav_data_df = get_enhanced_nav_data() # This is cached
        if nav_data_df.empty:
             raise HTTPException(status_code=404, detail="No scheme data found")

        categories = nav_data_df['Scheme Category'].dropna().unique().tolist()
        types = nav_data_df['Scheme Type'].dropna().unique().tolist()
        categories_data = {"categories": sorted(categories), "types": sorted(types)}
        # --- END FIX ---
        
        if not categories_data["categories"]:
            raise HTTPException(status_code=404, detail="Categories not found")
        return categories_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nav/search", response_model=List[dict], summary="Search for schemes")
async def search_schemes(q: str = Query(..., min_length=3)):
    """
    Search for schemes by name.
    --- FIXED ---
    This now searches the DataFrame from `get_enhanced_nav_data()`.
    """
    try:
        # --- FIXED ---
        # results = mf_data_fetcher.search_schemes(q) # Old code
        nav_data_df = get_enhanced_nav_data()
        if q:
            results = nav_data_df[
                nav_data_df['Scheme Name'].str.contains(q, case=False, na=False)
            ][['Scheme Code', 'Scheme Name']].to_dict('records')
        else:
            results = []
        # --- END FIX ---
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =========================================
# ANALYTICS ENDPOINTS (Refactored)
# =========================================

@router.get("/analytics/cagr/{scheme_code}", response_model=dict, summary="Get CAGR")
async def get_scheme_cagr(scheme_code: str, years: int = Query(3, ge=1, le=10)):
    """
    Calculate CAGR for a scheme.
    --- FIXED ---
    Uses the new `get_nav_history()` which returns a DataFrame
    that is compatible with your `FinancialMetricsCalculator`.
    """
    try:
        # --- FIXED ---
        # history = mf_data_fetcher.get_nav_history(scheme_code) # Old code
        history_df = get_nav_history(scheme_code) # New code
        # --- END FIX ---

        if history_df.empty:
            raise HTTPException(status_code=404, detail="NAV history not found")
        
        # We pass the DataFrame directly to the calculator
        cagr = metrics_calculator.calculate_cagr(history_df, years=years)
        if cagr is None:
            raise HTTPException(status_code=400, detail=f"Not enough data to calculate {years}-year CAGR")
        
        return {"scheme_code": scheme_code, "years": years, "cagr": cagr}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/risk/{scheme_code}", response_model=dict, summary="Get risk metrics")
async def get_scheme_risk_metrics(scheme_code: str):
    """
    Calculate risk metrics (Std Dev, Sharpe Ratio) for a scheme.
    --- FIXED ---
    Uses the new `get_nav_history()` which returns a DataFrame
    that is compatible with your `RiskMetricsCalculator`.
    """
    try:
        # --- FIXED ---
        # history = mf_data_fetcher.get_nav_history(scheme_code) # Old code
        history_df = get_nav_history(scheme_code) # New code
        # --- END FIX ---

        if history_df.empty:
            raise HTTPException(status_code=404, detail="NAV history not found")
        
        # We pass the DataFrame directly to the calculator
        risk_metrics = risk_calculator.calculate_risk_metrics(history_df)
        risk_metrics["scheme_code"] = scheme_code
        return risk_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analytics/compare", response_model=dict, summary="Compare schemes")
async def compare_schemes_performance(scheme_codes: List[str]):
    """
    Compare performance metrics for multiple schemes.
    --- FIXED ---
    Re-implements the `get_nav_history_bulk` logic by looping
    over the new `get_nav_history` function.
    """
    try:
        # --- FIXED ---
        # schemes_data = mf_data_fetcher.get_nav_history_bulk(scheme_codes) # Old code
        schemes_data = {}
        for code in scheme_codes:
            history_df = get_nav_history(code)
            if not history_df.empty:
                schemes_data[code] = history_df # Add the DataFrame
        # --- END FIX ---

        if not schemes_data:
            raise HTTPException(status_code=404, detail="No valid scheme data found")
        
        comparison = comparator.compare_schemes(schemes_data)
        
        # Convert DataFrames in response to JSON
        if 'normalized_performance' in comparison and isinstance(comparison['normalized_performance'], pd.DataFrame):
            comparison['normalized_performance'] = comparison['normalized_performance'].to_dict()
            
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analytics/portfolio", response_model=dict, summary="Analyze portfolio")
async def analyze_portfolio(portfolio: PortfolioRequest):
    """
    Analyze a given portfolio (Unchanged, but benefits from new data).
    """
    try:
        schemes = {s.scheme_code: s.weight for s in portfolio.schemes}
        
        # --- FIXED ---
        # This will now use the new `get_nav_history` function
        # to fetch data for the portfolio analysis.
        analyzer = PortfolioAnalyzer(schemes, data_fetcher_func=get_nav_history)
        # --- END FIX ---

        analysis = analyzer.analyze()
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =========================================
# PREDICTION ENDPOINT (Refactored)
# =========================================

@router.post("/predict", summary="Predict NAV")
async def predict_nav_endpoint(req: PredictionRequestModel):
    """
    Predict NAV for a given scheme.
    --- FIXED ---
    Uses the new `get_nav_history()` which returns a DataFrame
    that is compatible with your `NAVPredictor`.
    """
    try:
        # --- FIXED ---
        # history = mf_data_fetcher.get_nav_history(req.scheme_code) # Old code
        history_df = get_nav_history(req.scheme_code) # New code
        # --- END FIX ---

        if history_df.empty:
            raise HTTPException(status_code=404, detail="NAV history not found")
        
        # We pass the DataFrame directly to the predictor
        forecast = predictor.predict(history_df, days=req.forecast_days)
        
        if forecast is None:
            raise HTTPException(status_code=500, detail="Prediction model failed")
        
        # Convert forecast (which is a DataFrame) to JSON
        forecast['ds'] = forecast['ds'].astype(str)
        return forecast.to_dict('records')
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =========================================
# PORTFOLIO CRUD ENDPOINTS (Unchanged)
# =========================================

@router.post("/portfolio", response_model=PortfolioResponse, summary="Save portfolio")
async def save_portfolio(portfolio: PortfolioRequest):
    """
    Save a user-defined portfolio.
    """
    try:
        portfolio_id = str(uuid.uuid4())
        file_path = PORTFOLIO_DIR / f"{portfolio_id}.json"
        
        with open(file_path, "w") as f:
            json.dump(portfolio.model_dump(), f, indent=2)
            
        return PortfolioResponse(
            success=True, 
            portfolio_id=portfolio_id, 
            message="Portfolio saved successfully"
        )
    except Exception as e:
        return PortfolioResponse(success=False, error=str(e))


@router.get("/portfolio/{portfolio_id}", response_model=PortfolioRequest, summary="Get portfolio")
async def get_portfolio(portfolio_id: str):
    """
    Get a saved portfolio by ID.
    """
    try:
        file_path = PORTFOLIO_DIR / f"{portfolio_id}.json"
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        with open(file_path, "r") as f:
            data = json.load(f)
            
        return PortfolioRequest(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =========================================
# NEWS ENDPOINTS (Unchanged)
# =========================================

@router.get("/news", summary="Get analyzed news")
async def get_analyzed_market_news(query: str = Query("latest market news", description="Topic to analyze")):
    """
    Get market news analysis.
    Query can be a general topic (e.g., "latest market news")
    or a specific question (e.g., "What's happening in Indian equity markets?")
    """
    try:
        if not news_agent:
            raise HTTPException(status_code=503, detail="News agent not available")
        
        result = news_agent.get_analyzed_news(query=query)
        
        return {
            "success": True,
            "query": query,
            "analysis": result.get('analysis', ''),
            "articles": result['articles'],
            "total_articles": result['total_articles'],
            "mode": result['mode']
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/news/sources")
async def get_news_sources():
    """Get list of news sources being used"""
    return {
        "success": True,
        "sources": [
            {
                "name": "NewsAPI",
                "type": "API",
                "status": "active" if os.getenv('NEWS_API_KEY') else "inactive"
            },
            {
                "name": "Economic Times RSS",
                "type": "RSS Feed",
                "status": "active"
            },
            {
                "name": "MoneyControl RSS",
                "type": "RSS Feed",
                "status": "active"
            },
        ]
    }
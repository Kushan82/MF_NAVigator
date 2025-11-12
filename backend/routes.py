"""
API Routes for MF_NAVigator - COMPREHENSIVE FIXED VERSION
All REST API endpoints including:
- Scheme Search & Details
- Portfolio Management
- Analytics & Metrics
- NAV Predictions
- News & Market Data
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict
from datetime import datetime
import pandas as pd
import json
import uuid
from pathlib import Path
from pydantic import BaseModel
import logging
import sys
import os

# ==========================================
# LOGGING CONFIGURATION
# ==========================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==========================================
# IMPORTS - Data Fetcher (Primary)
# ==========================================
try:
    from data.data_fetcher import get_enhanced_nav_data, get_nav_history, get_aum_data
    logger.info("✅ Data fetcher functions imported")
except ImportError as e:
    logger.error(f"❌ Failed to import data fetcher: {e}")
    raise e

# ==========================================
# IMPORTS - Analytics
# ==========================================
try:
    from analytics.financial_metrics import FinancialMetricsCalculator
    from analytics.risk_metrics import RiskMetricsCalculator
    from analytics.portfolio_analysis import PortfolioAnalyzer
    from analytics.comparison import SchemeComparator
    logger.info("✅ Analytics modules imported")
except Exception as e:
    logger.warning(f"⚠️ Analytics modules not available: {e}")
    FinancialMetricsCalculator = None
    RiskMetricsCalculator = None
    PortfolioAnalyzer = None
    SchemeComparator = None

# ==========================================
# IMPORTS - Prediction & News
# ==========================================
try:
    from models.predictor import NAVPredictor
    logger.info("✅ NAV Predictor imported")
except Exception as e:
    logger.warning(f"⚠️ NAV Predictor not available: {e}")
    NAVPredictor = None

try:
    from backend.agents.news_agent import NewsAgent
    news_agent = NewsAgent()
    logger.info("✅ News Agent initialized")
except Exception as e:
    logger.warning(f"⚠️ News Agent not available: {e}")
    news_agent = None

# ==========================================
# PYDANTIC MODELS
# ==========================================
class PortfolioScheme(BaseModel):
    scheme_code: str
    scheme_name: str
    weight: float

class PortfolioRequest(BaseModel):
    name: str
    description: str
    schemes: List[PortfolioScheme]
    created_at: Optional[str] = None
    total_weight: float = 100.0

class PortfolioResponse(BaseModel):
    success: bool
    portfolio_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None

class PredictionRequest(BaseModel):
    scheme_code: str
    forecast_days: int = 30

# ==========================================
# ROUTERS
# ==========================================
router = APIRouter(prefix="/api/v1", tags=["api"])
health_router = APIRouter(tags=["health"])

# ==========================================
# INITIALIZE COMPONENTS
# ==========================================
try:
    metrics_calculator = FinancialMetricsCalculator() if FinancialMetricsCalculator else None
    risk_calculator = RiskMetricsCalculator() if RiskMetricsCalculator else None
    portfolio_analyzer = PortfolioAnalyzer() if PortfolioAnalyzer else None
    comparator = SchemeComparator() if SchemeComparator else None
except Exception as e:
    logger.warning(f"⚠️ Component initialization failed: {e}")
    metrics_calculator = risk_calculator = portfolio_analyzer = comparator = None

# ==========================================
# PORTFOLIO STORAGE
# ==========================================
PORTFOLIO_DIR = Path(__file__).parent.parent / "data" / "portfolios"
PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================
# NAV DATA CACHE
# ==========================================
_nav_cache = None
_cache_timestamp = None
CACHE_DURATION = 3600  # 1 hour

def get_cached_nav_data(force_refresh=False):
    """Get cached NAV data or fetch fresh - FIXED VERSION"""
    global _nav_cache, _cache_timestamp
    import time
    
    now = time.time()
    cache_expired = (now - (_cache_timestamp or 0) > CACHE_DURATION)
    
    # Fetch if: no cache, cache expired, force refresh, or cache is empty
    should_fetch = (
        _nav_cache is None or 
        force_refresh or 
        cache_expired or 
        (_nav_cache is not None and _nav_cache.empty)
    )
    
    if should_fetch:
        logger.info("📡 Fetching NAV data from AMFI...")
        try:
            new_data = get_enhanced_nav_data()
            
            # Only update cache if we got valid data
            if new_data is not None and not new_data.empty:
                _nav_cache = new_data
                _cache_timestamp = now
                logger.info(f"✅ Loaded {len(_nav_cache)} schemes")
                return _nav_cache
            else:
                logger.error("❌ Fetched data is empty!")
                # Return old cache if available, otherwise empty DataFrame
                if _nav_cache is not None and not _nav_cache.empty:
                    logger.warning("⚠️ Using stale cache data")
                    return _nav_cache
                else:
                    logger.error("❌ No cache available, returning empty")
                    return pd.DataFrame()
                    
        except Exception as e:
            logger.error(f"❌ Error fetching data: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Return old cache if available
            if _nav_cache is not None and not _nav_cache.empty:
                logger.warning("⚠️ Using stale cache due to error")
                return _nav_cache
            else:
                return pd.DataFrame()
    
    # Return existing cache
    return _nav_cache if _nav_cache is not None else pd.DataFrame()

# ==========================================
# HEALTH CHECK
# ==========================================
@health_router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        df = get_cached_nav_data()
        return {
            "status": "healthy",
            "schemes_loaded": len(df) if df is not None else 0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

# ==========================================
# SCHEME SEARCH & DETAILS ROUTES
# ==========================================

@router.get("/schemes/search")
async def search_schemes(
    query: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=200)
):
    """Search schemes by name, AMC, or code"""
    try:
        logger.info(f"🔍 Searching: {query}")
        df = get_cached_nav_data()
        
        if df is None or len(df) == 0:
            logger.warning("⚠️ No data available for search")
            return {"total_results": 0, "schemes": []}
        
        logger.info(f"   Available columns: {list(df.columns)}")
        # Search
        query_lower = query.lower()
        
        mask = (
                df['Scheme Name'].str.lower().str.contains(query_lower, na=False) |
                df['Scheme Code'].astype(str).str.contains(query_lower, na=False) |
                df['AMC'].str.lower().str.contains(query_lower, na=False)
            )
        
        results = df[mask].head(limit)
        logger.info(f"   Found {len(results)} matches")
        
        schemes = []
        
        for _, row in results.iterrows():
            try:
                scheme_entry = {
                    "scheme_code": str(row['Scheme Code']),
                    "scheme_name": str(row['Scheme Name']),
                    "amc": str(row['AMC']),
                    "category": str(row.get('Scheme Category','Other')),
                    "current_nav": float(row['NAV']),
                    "nav_date": str(row['Date'])[:10],
                }
                schemes.append(scheme_entry)
            except Exception as e:
                logger.warning(f"⚠️ Skipping row: {e}")
                continue
        
        logger.info(f"✅ Found {len(schemes)} schemes")
        return {"total_results": len(schemes), "schemes": schemes}
    
    except Exception as e:
        logger.error(f"❌ Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schemes/{scheme_code}")
async def get_scheme_details(scheme_code: str):
    """Get detailed information for a scheme"""
    try:
        logger.info(f"📊 Getting details for: {scheme_code}")
        df = get_cached_nav_data()
        
        if df is None or len(df) == 0:
            raise HTTPException(status_code=503, detail="No data available")
        
        scheme = df[df['Scheme Code'] == scheme_code]
        if scheme.empty:
            scheme = df[df['Scheme Code'].astype(str) == str(scheme_code)]
        
        
        if scheme.empty:
            raise HTTPException(status_code=404, detail="Scheme not found")
        
        row = scheme.iloc[0]
        return {
            "scheme_code": str(row['Scheme Code']),
            "scheme_name": str(row['Scheme Name']),
            "amc": str(row['AMC']),
            "category": str(row.get('Scheme Category', 'Other')),
            "current_nav": float(row['NAV']),
            "nav_date": str(row['Date'])[:10],
            "isin_div": str(row.get('ISIN Div Payout', 'N/A')),
            "isin_growth": str(row.get('ISIN Div Reinvestment', 'N/A')),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Detail error: {e}",exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# NAV & HISTORY ROUTES
# ==========================================

@router.get("/nav")
async def get_all_nav():
    """Get latest NAV for all schemes"""
    try:
        df = get_cached_nav_data()
        if df is None or df.empty:
            return []
        
        result = []
        for _, row in df.iterrows():
            result.append({
                "Scheme Code": str(row['Scheme Code']),
                "Scheme Name": str(row['Scheme Name']),
                "NAV": float(row['NAV']),
                "Date": str(row['Date'])[:10],
                "AMC": str(row['AMC']),
                "Scheme Category": str(row.get('Scheme Category', 'Other'))
            })
        
        return result
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/nav/search")
async def search_nav(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=200)
):
    """
    Alternative search endpoint (used by some frontend code)
    """
    # Redirect to main search
    return await search_schemes(query=q, limit=limit)

@router.get("/schemes/{scheme_code}/history")
async def get_scheme_history(
    scheme_code: str,
    days: int = Query(365, ge=1, le=3650)
):
    """Get NAV history for a scheme"""
    try:
        logger.info(f"📈 Getting {days} days history for: {scheme_code}")
        
        history = get_nav_history(scheme_code)
        if history is None or history.empty:
            raise HTTPException(status_code=404, detail="History not found")
        
        history = history.tail(days)
        history_list = []
        for _, row in history.iterrows():
            history_list.append({
                "date": str(row['Date'])[:10],
                "nav": float(row['NAV'])
            })        
        logger.info(f"✅ Returned {len(history)} history records")
        return history_list
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ History error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/aum")
async def get_aum_data_all():
    """Get AUM data for all AMCs"""
    try:
        logger.info("💰 Fetching AUM data...")
        
        aum_df = get_aum_data()
        if aum_df is None or aum_df.empty:
            raise HTTPException(status_code=404, detail="AUM data not found")
        
        aum_df['Date'] = aum_df['Date'].astype(str)
        return aum_df.to_dict('records')
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ AUM error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# ANALYTICS ROUTES
# ==========================================

@router.get("/analytics/cagr/{scheme_code}")
async def get_scheme_cagr(
    scheme_code: str,
    years: int = Query(3, ge=1, le=10)
):
    """Calculate CAGR for a scheme"""
    try:
        if metrics_calculator is None:
            raise HTTPException(status_code=503, detail="Analytics not available")
        
        logger.info(f"📊 Calculating {years}Y CAGR for: {scheme_code}")
        
        history = get_nav_history(scheme_code)
        if history is None or history.empty:
            raise HTTPException(status_code=404, detail="History not found")
        
        nav_series = pd.Series(history['NAV'].values)
        cagr = metrics_calculator.calculate_cagr_from_nav(nav_series, years)
        
        if cagr is None or pd.isna(cagr):
            raise HTTPException(status_code=400, detail="Not enough data")
        
        logger.info(f"✅ CAGR: {cagr:.2f}%")
        return {
            "scheme_code": scheme_code,
            "years": years,
            "cagr": float(cagr)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ CAGR error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/risk/{scheme_code}")
async def get_scheme_risk_metrics(scheme_code: str):
    """Get risk metrics for a scheme"""
    try:
        if risk_calculator is None:
            raise HTTPException(status_code=503, detail="Analytics not available")
        
        logger.info(f"📊 Calculating risk metrics for: {scheme_code}")
        
        history = get_nav_history(scheme_code)
        if history is None or history.empty:
            raise HTTPException(status_code=404, detail="History not found")
        
        nav_series = pd.Series(history['NAV'].values)
        risk_metrics = risk_calculator.get_comprehensive_risk_metrics(nav_series)
        
        logger.info(f"✅ Risk metrics calculated")
        return {
            "scheme_code": scheme_code,
            "volatility": float(risk_metrics.get('volatility', 0)),
            "downside_deviation": float(risk_metrics.get('downside_deviation', 0)),
            "max_drawdown": float(risk_metrics.get('max_drawdown', 0)),
            "var_95": float(risk_metrics.get('var_95', 0)),
            "cvar_95": float(risk_metrics.get('cvar_95', 0))
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Risk error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/comprehensive/{scheme_code}")
async def get_comprehensive_metrics(scheme_code: str):
    """Get all financial and risk metrics"""
    try:
        if metrics_calculator is None or risk_calculator is None:
            raise HTTPException(status_code=503, detail="Analytics not available")
        
        logger.info(f"📊 Getting comprehensive metrics for: {scheme_code}")
        
        history = get_nav_history(scheme_code)
        if history is None or history.empty:
            raise HTTPException(status_code=404, detail="History not found")
        
        nav_series = pd.Series(history['NAV'].values)
        fin_metrics = metrics_calculator.get_comprehensive_metrics(nav_series)
        risk_metrics = risk_calculator.get_comprehensive_risk_metrics(nav_series)
        
        logger.info(f"✅ Comprehensive metrics calculated")
        return {
            "scheme_code": scheme_code,
            "financial_metrics": fin_metrics,
            "risk_metrics": risk_metrics
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Comprehensive error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# COMPARISON ROUTES
# ==========================================

@router.post("/analytics/compare")
async def compare_schemes(scheme_codes: List[str] = Query(...)):
    """Compare performance of multiple schemes"""
    try:
        if comparator is None:
            raise HTTPException(status_code=503, detail="Comparator not available")
        
        if len(scheme_codes) < 2:
            raise HTTPException(status_code=400, detail="Need at least 2 schemes")
        
        logger.info(f"📊 Comparing {len(scheme_codes)} schemes")
        
        comparison_data = {}
        for code in scheme_codes:
            history = get_nav_history(code)
            if history is not None and not history.empty:
                comparison_data[code] = pd.Series(history['NAV'].values)
        
        if len(comparison_data) < 2:
            raise HTTPException(status_code=404, detail="Could not load data")
        
        result = comparator.compare_schemes(list(comparison_data.keys()), comparison_data)
        
        logger.info(f"✅ Comparison complete")
        return {
            "comparison": result.to_dict() if hasattr(result, 'to_dict') else result,
            "schemes_compared": len(comparison_data)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Comparison error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# PORTFOLIO ROUTES
# ==========================================

@router.post("/portfolio/analyze")
async def analyze_portfolio(portfolio: PortfolioRequest):
    """Analyze a portfolio of schemes"""
    try:
        if portfolio_analyzer is None:
            raise HTTPException(status_code=503, detail="Portfolio analyzer not available")
        
        logger.info(f"📊 Analyzing portfolio: {portfolio.name}")
        
        weights = {s.scheme_code: s.weight for s in portfolio.schemes}
        schemes_data = {}
        
        for scheme in portfolio.schemes:
            history = get_nav_history(scheme.scheme_code)
            if history is not None and not history.empty:
                schemes_data[scheme.scheme_code] = pd.Series(history['NAV'].values)
        
        if not schemes_data:
            raise HTTPException(status_code=404, detail="Could not load data")
        
        metrics = portfolio_analyzer.calculate_portfolio_metrics(schemes_data, weights)
        
        logger.info(f"✅ Portfolio analyzed")
        return {
            "portfolio_name": portfolio.name,
            "total_schemes": len(portfolio.schemes),
            "metrics": metrics
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Portfolio analyze error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/portfolio/save")
async def save_portfolio(portfolio: PortfolioRequest):
    """Save a portfolio"""
    try:
        logger.info(f"💾 Saving portfolio: {portfolio.name}")
        
        portfolio_id = str(uuid.uuid4())
        filepath = PORTFOLIO_DIR / f"{portfolio_id}.json"
        
        portfolio_data = {
            "id": portfolio_id,
            **portfolio.model_dump()
        }
        
        with open(filepath, 'w') as f:
            json.dump(portfolio_data, f, indent=2)
        
        logger.info(f"✅ Saved portfolio: {portfolio_id}")
        return PortfolioResponse(
            success=True,
            portfolio_id=portfolio_id,
            message="Portfolio saved successfully"
        )
    
    except Exception as e:
        logger.error(f"❌ Save error: {e}")
        return PortfolioResponse(success=False, error=str(e))

@router.get("/portfolio/{portfolio_id}")
async def get_portfolio(portfolio_id: str):
    """Get a saved portfolio"""
    try:
        logger.info(f"📂 Loading portfolio: {portfolio_id}")
        
        filepath = PORTFOLIO_DIR / f"{portfolio_id}.json"
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        logger.info(f"✅ Loaded portfolio")
        return data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portfolio")
async def list_portfolios():
    """List all saved portfolios"""
    try:
        logger.info("📂 Listing portfolios")
        
        portfolios = []
        for filepath in PORTFOLIO_DIR.glob("*.json"):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                portfolios.append({
                    "id": data.get("id"),
                    "name": data.get("name"),
                    "schemes_count": len(data.get("schemes", []))
                })
            except:
                continue
        
        logger.info(f"✅ Found {len(portfolios)} portfolios")
        return portfolios
    
    except Exception as e:
        logger.error(f"❌ List error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/portfolio/{portfolio_id}")
async def delete_portfolio(portfolio_id: str):
    """Delete a portfolio"""
    try:
        logger.info(f"🗑️ Deleting portfolio: {portfolio_id}")
        
        filepath = PORTFOLIO_DIR / f"{portfolio_id}.json"
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        filepath.unlink()
        
        logger.info(f"✅ Deleted portfolio")
        return PortfolioResponse(success=True, message="Portfolio deleted")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Delete error: {e}")
        return PortfolioResponse(success=False, error=str(e))

# ==========================================
# PREDICTION ROUTES
# ==========================================

@router.post("/predict/single")
async def predict_nav_endpoint(req: PredictionRequest):
    """Predict NAV for a scheme"""
    try:
        if NAVPredictor is None:
            raise HTTPException(status_code=503, detail="Predictor not available")
        
        logger.info(f"🔮 Predicting NAV for: {req.scheme_code}")
        
        history = get_nav_history(req.scheme_code)
        if history is None or history.empty:
            raise HTTPException(status_code=404, detail="History not found")
        
        if len(history) < 200:
            raise HTTPException(status_code=400, detail="Not enough historical data")
        
        nav_series = pd.Series(history['NAV'].values)
        predictor_instance = NAVPredictor(lookback_days=60, forecast_days=req.forecast_days)
        metrics = predictor_instance.train(nav_series, validation_split=0.2)
        prediction_df = predictor_instance.predict(nav_series)
        
        logger.info(f"✅ Prediction generated")
        return {
            "scheme_code": req.scheme_code,
            "current_nav": float(nav_series.iloc[-1]),
            "predicted_nav": float(prediction_df['PredictedNAV'].iloc[0]),
            "confidence": "High" if metrics.get('val_mape', 100) < 2 else "Medium",
            "model_performance": metrics
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predict/sequence/{scheme_code}")
async def predict_sequence(
    scheme_code: str,
    days: int = Query(7, ge=1, le=30)
):
    """Get sequential NAV predictions"""
    try:
        if NAVPredictor is None:
            raise HTTPException(status_code=503, detail="Predictor not available")
        
        logger.info(f"🔮 Getting {days}-day sequence for: {scheme_code}")
        
        history = get_nav_history(scheme_code)
        if history is None or history.empty:
            raise HTTPException(status_code=404, detail="History not found")
        
        if len(history) < 200:
            raise HTTPException(status_code=400, detail="Not enough historical data")
        
        nav_series = pd.Series(history['NAV'].values)
        predictor_instance = NAVPredictor(lookback_days=60, forecast_days=1)
        predictor_instance.train(nav_series, validation_split=0.2)
        seq_predictions = predictor_instance.predict_sequence(nav_series, n_days=days)
        
        logger.info(f"✅ Sequence generated")
        return {
            "scheme_code": scheme_code,
            "predictions": seq_predictions.to_dict('records') if hasattr(seq_predictions, 'to_dict') else seq_predictions
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Sequence error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# NEWS ROUTES
# ==========================================

@router.get("/news/market")
async def get_market_news(
    topic: str = Query("equity mutual funds"),
    limit: int = Query(20, ge=5, le=50)
):
    """Get market news"""
    try:
        if news_agent is None:
            raise HTTPException(status_code=503, detail="News not available")
        
        logger.info(f"📰 Fetching news: {topic}")
        result = news_agent.get_market_news(topic=topic, limit=limit)
        
        logger.info(f"✅ Fetched {len(result.get('articles', []))} articles")
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ News error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/news/sources")
async def get_news_sources():
    """Get news sources"""
    return {
        "success": True,
        "sources": [
            {"name": "NewsAPI", "type": "API", "status": "active" if os.getenv('NEWS_API_KEY') else "inactive"},
            {"name": "Economic Times RSS", "type": "RSS Feed", "status": "active"},
            {"name": "MoneyControl RSS", "type": "RSS Feed", "status": "active"},
            {"name": "LiveMint RSS", "type": "RSS Feed", "status": "active"}
        ]
    }

# ==========================================
# DATA MANAGEMENT ROUTES
# ==========================================

@router.post("/data/refresh")
async def refresh_data():
    """Force refresh of cached data"""
    try:
        logger.info("🔄 Refreshing data...")
        get_cached_nav_data(force_refresh=True)
        logger.info("✅ Data refreshed")
        return {"success": True, "message": "Data refreshed"}
    except Exception as e:
        logger.error(f"❌ Refresh error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

logger.info("=" * 50)
logger.info("🚀 MF_NAVigator Backend Routes Initialized")
logger.info("=" * 50)

"""
API routes for MF_NAVigator - COMPLETE VERSION
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
import logging

# --- Robust Path Setup ---
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DATA IMPORTS - Using new centralized fetcher ---
try:
    from data.data_fetcher import (
        get_enhanced_nav_data,
        get_nav_history,
        get_aum_data
    )
    logger.info("Successfully imported from data.data_fetcher")
except ImportError as e:
    logger.error(f"Failed to import from data.data_fetcher: {e}")
    raise e

# --- OTHER IMPORTS ---
from backend.schemas import *
from analytics.financial_metrics import FinancialMetricsCalculator
from analytics.risk_metrics import RiskMetricsCalculator
from analytics.portfolio_analysis import PortfolioAnalyzer
from analytics.comparison import SchemeComparator
from models.predictor import NAVPredictor
from backend.agents.news_agent import NewsAgent

# =========================================
# PYDANTIC MODELS
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
# ROUTER & INSTANCES
# =========================================
router = APIRouter()
health_router = APIRouter()

metrics_calculator = FinancialMetricsCalculator()
risk_calculator = RiskMetricsCalculator()
comparator = SchemeComparator()
predictor = NAVPredictor()
news_agent = NewsAgent()

# Portfolio storage
PORTFOLIO_DIR = Path(__file__).parent / "data" / "portfolios"
PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)

# =========================================
# HEALTH CHECK
# =========================================

@health_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

# =========================================
# NAV DATA ENDPOINTS
# =========================================

@router.get("/nav", response_model=List[dict], summary="Get latest NAV for all schemes")
async def get_all_nav():
    """Get the latest NAV for all mutual fund schemes with categories"""
    try:
        nav_data_df = get_enhanced_nav_data()
        
        if nav_data_df.empty:
            return []
        
        # Convert date to string for JSON compatibility
        nav_data_df['Date'] = nav_data_df['Date'].astype(str)
        nav_data = nav_data_df.to_dict('records')
        
        logger.info(f"Returned {len(nav_data)} NAV records")
        return nav_data
    except Exception as e:
        logger.error(f"Error in get_all_nav: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/nav/history/{scheme_code}", response_model=List[dict], summary="Get NAV history")
async def get_scheme_nav_history(scheme_code: str):
    """Get the NAV history for a specific scheme"""
    try:
        history_df = get_nav_history(scheme_code)
        
        if history_df.empty:
            raise HTTPException(status_code=404, detail="NAV history not found")
        
        # Convert date to string for JSON compatibility
        history_df['date'] = history_df['date'].astype(str)
        history = history_df.to_dict('records')
        
        logger.info(f"Returned {len(history)} history records for {scheme_code}")
        return history
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_scheme_nav_history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/nav/amc", response_model=List[dict], summary="Get AUM data for all AMCs")
async def get_aum_data_all_amcs():
    """Get the latest AUM data for all AMCs"""
    try:
        aum_data_df = get_aum_data()
        
        if aum_data_df.empty:
            raise HTTPException(status_code=404, detail="AUM data not found")
        
        logger.info(f"Returned AUM data for {len(aum_data_df)} AMCs")
        return aum_data_df.to_dict('records')
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_aum_data_all_amcs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/nav/categories", response_model=dict, summary="Get scheme categories and types")
async def get_scheme_categories_and_types():
    """Get all unique scheme categories and types"""
    try:
        nav_data_df = get_enhanced_nav_data()
        
        if nav_data_df.empty:
            raise HTTPException(status_code=404, detail="No scheme data found")
        
        categories = nav_data_df['Scheme Category'].dropna().unique().tolist()
        types = nav_data_df['Scheme Type'].dropna().unique().tolist()
        
        categories_data = {
            "categories": sorted(categories),
            "types": sorted(types)
        }
        
        logger.info(f"Returned {len(categories)} categories and {len(types)} types")
        return categories_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_scheme_categories_and_types: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/nav/search", response_model=List[dict], summary="Search for schemes")
async def search_schemes(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=200, description="Maximum results")
):
    """Search for schemes by name, AMC, or code"""
    try:
        nav_data_df = get_enhanced_nav_data()
        
        if nav_data_df.empty:
            return []
        
        # Search in Scheme Name, AMC, and Scheme Code
        mask = (
            nav_data_df['Scheme Name'].str.contains(q, case=False, na=False) |
            nav_data_df['AMC'].str.contains(q, case=False, na=False) |
            nav_data_df['Scheme Code'].astype(str).str.contains(q, case=False, na=False)
        )
        
        results = nav_data_df[mask].head(limit)
        
        # Format results
        output = []
        for _, row in results.iterrows():
            output.append({
                'Scheme Code': str(row['Scheme Code']),
                'Scheme Name': row['Scheme Name'],
                'current_nav': float(row['NAV']),
                'nav_date': str(row['Date']),
                'amc': row['AMC'],
                'category': row.get('Scheme Category', 'N/A'),
                'scheme_type': row.get('Scheme Type', 'N/A')
            })
        
        logger.info(f"Search '{q}' returned {len(output)} results")
        return output
    except Exception as e:
        logger.error(f"Error in search_schemes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =========================================
# SCHEME DETAILS ENDPOINTS
# =========================================

@router.get("/schemes/{scheme_code}", response_model=dict, summary="Get scheme details")
async def get_scheme_details(scheme_code: str):
    """Get detailed information for a specific scheme"""
    try:
        nav_data_df = get_enhanced_nav_data()
        
        # Find the scheme
        scheme_data = nav_data_df[nav_data_df['Scheme Code'].astype(str) == str(scheme_code)]
        
        if scheme_data.empty:
            raise HTTPException(status_code=404, detail=f"Scheme {scheme_code} not found")
        
        scheme = scheme_data.iloc[0]
        
        details = {
            'scheme_code': str(scheme['Scheme Code']),
            'scheme_name': scheme['Scheme Name'],
            'current_nav': float(scheme['NAV']),
            'nav_date': str(scheme['Date']),
            'amc': scheme['AMC'],
            'category': scheme.get('Scheme Category', 'N/A'),
            'scheme_type': scheme.get('Scheme Type', 'N/A'),
            'isin_div': scheme.get('ISIN Div Payout', ''),
            'isin_growth': scheme.get('ISIN Div Reinvestment', '')
        }
        
        logger.info(f"Returned details for scheme {scheme_code}")
        return details
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_scheme_details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =========================================
# ANALYTICS ENDPOINTS
# =========================================

@router.get("/analytics/cagr/{scheme_code}", response_model=dict, summary="Get CAGR")
async def get_scheme_cagr(
    scheme_code: str,
    years: int = Query(3, ge=1, le=10, description="Number of years")
):
    """Calculate CAGR for a scheme"""
    try:
        history_df = get_nav_history(scheme_code)
        
        if history_df.empty:
            raise HTTPException(status_code=404, detail="NAV history not found")
        
        # Convert to pandas Series with date index
        nav_series = pd.Series(
            history_df['nav'].values,
            index=pd.to_datetime(history_df['date'])
        )
        
        # Calculate CAGR
        cagr = metrics_calculator.calculate_cagr_from_nav(
            nav_series,
            date_series=pd.Series(nav_series.index)
        )
        
        if cagr is None or pd.isna(cagr):
            raise HTTPException(
                status_code=400,
                detail=f"Not enough data to calculate {years}-year CAGR"
            )
        
        logger.info(f"Calculated CAGR for {scheme_code}: {cagr*100:.2f}%")
        return {
            "scheme_code": scheme_code,
            "years": years,
            "cagr": float(cagr)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_scheme_cagr: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/risk/{scheme_code}", response_model=dict, summary="Get risk metrics")
async def get_scheme_risk_metrics(scheme_code: str):
    """Calculate risk metrics for a scheme"""
    try:
        history_df = get_nav_history(scheme_code)
        
        if history_df.empty:
            raise HTTPException(status_code=404, detail="NAV history not found")
        
        # Convert to pandas Series with date index
        nav_series = pd.Series(
            history_df['nav'].values,
            index=pd.to_datetime(history_df['date'])
        )
        
        # Calculate risk metrics
        risk_metrics = risk_calculator.get_comprehensive_risk_metrics(
            nav_series,
            date_series=pd.Series(nav_series.index)
        )
        
        # Format response
        response = {
            "scheme_code": scheme_code,
            "volatility": float(risk_metrics['volatility']),
            "downside_deviation": float(risk_metrics['downside_deviation']),
            "max_drawdown": float(risk_metrics['max_drawdown']),
            "var_95": float(risk_metrics['var_95']),
            "cvar_95": float(risk_metrics['cvar_95']),
            "calmar_ratio": float(risk_metrics.get('calmar_ratio', 0)),
            "ulcer_index": float(risk_metrics.get('ulcer_index', 0))
        }
        
        logger.info(f"Calculated risk metrics for {scheme_code}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_scheme_risk_metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/comprehensive/{scheme_code}", response_model=dict, summary="Get all metrics")
async def get_comprehensive_metrics(scheme_code: str):
    """Get comprehensive financial and risk metrics"""
    try:
        history_df = get_nav_history(scheme_code)
        
        if history_df.empty:
            raise HTTPException(status_code=404, detail="NAV history not found")
        
        # Convert to pandas Series with date index
        nav_series = pd.Series(
            history_df['nav'].values,
            index=pd.to_datetime(history_df['date'])
        )
        date_series = pd.Series(nav_series.index)
        
        # Calculate financial metrics
        fin_metrics = metrics_calculator.get_comprehensive_metrics(nav_series, date_series)
        
        # Calculate risk metrics
        risk_metrics = risk_calculator.get_comprehensive_risk_metrics(nav_series, date_series)
        
        # Combine metrics
        comprehensive = {
            "scheme_code": scheme_code,
            "financial_metrics": {
                "current_nav": fin_metrics['current_nav'],
                "cagr": fin_metrics.get('cagr'),
                "annualized_return": fin_metrics['annualized_return'],
                "sharpe_ratio": fin_metrics.get('sharpe_ratio'),
                "sortino_ratio": fin_metrics.get('sortino_ratio'),
                "absolute_returns": fin_metrics.get('absolute_returns', {})
            },
            "risk_metrics": {
                "volatility": risk_metrics['volatility'],
                "downside_deviation": risk_metrics['downside_deviation'],
                "max_drawdown": risk_metrics['max_drawdown'],
                "var_95": risk_metrics['var_95'],
                "cvar_95": risk_metrics['cvar_95'],
                "calmar_ratio": risk_metrics.get('calmar_ratio'),
                "ulcer_index": risk_metrics.get('ulcer_index')
            }
        }
        
        logger.info(f"Calculated comprehensive metrics for {scheme_code}")
        return comprehensive
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_comprehensive_metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analytics/compare", response_model=dict, summary="Compare schemes")
async def compare_schemes_performance(scheme_codes: List[str]):
    """Compare performance metrics for multiple schemes"""
    try:
        if len(scheme_codes) < 2:
            raise HTTPException(
                status_code=400,
                detail="Need at least 2 schemes to compare"
            )
        
        # Fetch NAV data for all schemes
        nav_data = {}
        for code in scheme_codes:
            history_df = get_nav_history(code)
            if not history_df.empty:
                nav_series = pd.Series(
                    history_df['nav'].values,
                    index=pd.to_datetime(history_df['date'])
                )
                nav_data[code] = nav_series
        
        if len(nav_data) < 2:
            raise HTTPException(
                status_code=404,
                detail="Could not load data for at least 2 schemes"
            )
        
        # Compare schemes
        comparison = comparator.compare_schemes(
            list(nav_data.keys()),
            nav_data
        )
        
        # Convert DataFrames to JSON-serializable format
        result = {
            "comparison": comparison['comparison'].to_dict('records'),
            "rankings": {k: v.tolist() for k, v in comparison.get('rankings', {}).items()},
            "best_schemes": comparison.get('best_schemes', {}),
            "correlation_matrix": comparator.get_correlation_matrix(nav_data).to_dict()
        }
        
        # Add normalized performance
        normalized_perf = {}
        for code, nav_series in nav_data.items():
            normalized = (nav_series / nav_series.iloc[0] * 100).reset_index()
            normalized.columns = ['date', 'normalized_nav']
            normalized['date'] = normalized['date'].astype(str)
            normalized_perf[code] = normalized.to_dict('records')
        
        result['normalized_performance'] = normalized_perf
        
        logger.info(f"Compared {len(nav_data)} schemes")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in compare_schemes_performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =========================================
# PORTFOLIO ENDPOINTS
# =========================================

@router.post("/portfolio/analyze", response_model=dict, summary="Analyze portfolio")
async def analyze_portfolio(portfolio: PortfolioRequest):
    """Analyze a portfolio of schemes"""
    try:
        # Prepare weights dictionary
        weights = {s.scheme_code: s.weight for s in portfolio.schemes}
        
        # Fetch NAV data for all schemes
        schemes_data = {}
        for scheme in portfolio.schemes:
            history_df = get_nav_history(scheme.scheme_code)
            if not history_df.empty:
                nav_series = pd.Series(
                    history_df['nav'].values,
                    index=pd.to_datetime(history_df['date'])
                )
                schemes_data[scheme.scheme_code] = nav_series
        
        if not schemes_data:
            raise HTTPException(
                status_code=404,
                detail="Could not load data for any schemes"
            )
        
        # Create analyzer and analyze
        analyzer = PortfolioAnalyzer()
        
        # Calculate portfolio metrics
        metrics = analyzer.calculate_portfolio_metrics(schemes_data, weights)
        
        # Calculate diversification score
        div_score = analyzer.get_diversification_score(schemes_data, weights)
        
        # Get correlation matrix
        corr_matrix = analyzer.calculate_correlation_matrix(schemes_data)
        
        result = {
            "portfolio_name": portfolio.name,
            "total_schemes": len(portfolio.schemes),
            "metrics": {
                "annualized_return": float(metrics['annualized_return']),
                "volatility": float(metrics['volatility']),
                "sharpe_ratio": float(metrics['sharpe_ratio']),
                "sortino_ratio": float(metrics['sortino_ratio']),
                "max_drawdown": float(metrics['max_drawdown']),
                "var_95": float(metrics['var_95']),
                "cvar_95": float(metrics['cvar_95'])
            },
            "diversification_score": float(div_score),
            "correlation_matrix": corr_matrix.to_dict()
        }
        
        logger.info(f"Analyzed portfolio: {portfolio.name}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze_portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/portfolio/save", response_model=PortfolioResponse, summary="Save portfolio")
async def save_portfolio(portfolio: PortfolioRequest):
    """Save a user-defined portfolio"""
    try:
        portfolio_id = str(uuid.uuid4())
        file_path = PORTFOLIO_DIR / f"{portfolio_id}.json"
        
        portfolio_data = {
            "id": portfolio_id,
            **portfolio.model_dump()
        }
        
        with open(file_path, "w") as f:
            json.dump(portfolio_data, f, indent=2)
        
        logger.info(f"Saved portfolio: {portfolio.name} (ID: {portfolio_id})")
        return PortfolioResponse(
            success=True,
            portfolio_id=portfolio_id,
            message="Portfolio saved successfully"
        )
    except Exception as e:
        logger.error(f"Error in save_portfolio: {e}")
        return PortfolioResponse(success=False, error=str(e))

@router.get("/portfolio/{portfolio_id}", response_model=dict, summary="Get portfolio")
async def get_portfolio(portfolio_id: str):
    """Get a saved portfolio by ID"""
    try:
        file_path = PORTFOLIO_DIR / f"{portfolio_id}.json"
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        with open(file_path, "r") as f:
            data = json.load(f)
        
        logger.info(f"Retrieved portfolio: {portfolio_id}")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portfolio/list", response_model=dict, summary="List all portfolios")
async def list_portfolios():
    """List all saved portfolios"""
    try:
        portfolios = []
        
        for file_path in PORTFOLIO_DIR.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    portfolios.append({
                        "id": data.get("id"),
                        "name": data.get("name"),
                        "description": data.get("description", ""),
                        "schemes_count": len(data.get("schemes", [])),
                        "created_at": data.get("created_at")
                    })
            except Exception as e:
                logger.warning(f"Could not load portfolio {file_path}: {e}")
                continue
        
        logger.info(f"Listed {len(portfolios)} portfolios")
        return {"portfolios": portfolios}
    except Exception as e:
        logger.error(f"Error in list_portfolios: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/portfolio/{portfolio_id}", response_model=PortfolioResponse, summary="Delete portfolio")
async def delete_portfolio(portfolio_id: str):
    """Delete a saved portfolio"""
    try:
        file_path = PORTFOLIO_DIR / f"{portfolio_id}.json"
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        file_path.unlink()
        
        logger.info(f"Deleted portfolio: {portfolio_id}")
        return PortfolioResponse(
            success=True,
            message="Portfolio deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_portfolio: {e}")
        return PortfolioResponse(success=False, error=str(e))

# =========================================
# PREDICTION ENDPOINTS
# =========================================

@router.post("/predict/single", response_model=dict, summary="Predict NAV")
async def predict_nav_endpoint(req: PredictionRequestModel):
    """Predict NAV for a given scheme"""
    try:
        # Get historical data
        history_df = get_nav_history(req.scheme_code)
        
        if history_df.empty:
            raise HTTPException(status_code=404, detail="NAV history not found")
        
        # Check if we have enough data
        min_required = 200  # Minimum days for reliable prediction
        if len(history_df) < min_required:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough historical data. Need at least {min_required} days, found {len(history_df)}"
            )
        
        # Convert to pandas Series
        nav_series = pd.Series(
            history_df['nav'].values,
            index=pd.to_datetime(history_df['date'])
        )
        
        # Train predictor
        predictor_instance = NAVPredictor(
            lookback_days=60,
            forecast_days=req.forecast_days
        )
        
        metrics = predictor_instance.train(nav_series, validation_split=0.2)
        
        # Make prediction
        prediction_df = predictor_instance.predict(nav_series)
        
        # Get scheme name
        nav_data_df = get_enhanced_nav_data()
        scheme_data = nav_data_df[nav_data_df['Scheme Code'].astype(str) == str(req.scheme_code)]
        scheme_name = scheme_data.iloc[0]['Scheme Name'] if not scheme_data.empty else req.scheme_code
        
        # Determine confidence based on validation metrics
        val_mape = metrics.get('val_mape', 100)
        if val_mape < 2:
            confidence = "High"
        elif val_mape < 5:
            confidence = "Medium"
        else:
            confidence = "Low"
        
        result = {
            "success": True,
            "scheme_code": req.scheme_code,
            "scheme_name": scheme_name,
            "current_nav": float(prediction_df['Current_NAV'].iloc[0]),
            "prediction": {
                "date": str(prediction_df['Date'].iloc[0]),
                "predicted_nav": float(prediction_df['Predicted_NAV'].iloc[0]),
                "change": float(prediction_df['Change'].iloc[0]),
                "change_percent": float(prediction_df['Change_Percent'].iloc[0])
            },
            "confidence": confidence,
            "model_performance": {
                "validation_mape": f"{val_mape:.2f}%",
                "directional_accuracy": f"{metrics.get('val_directional', 0):.2f}%",
                "training_samples": metrics.get('train_samples', 0),
                "validation_samples": metrics.get('val_samples', 0),
                "confidence": confidence
            },
            "data_quality": {
                "historical_days": len(history_df),
                "date_range": {
                    "start": str(history_df['date'].min()),
                    "end": str(history_df['date'].max())
                }
            }
        }
        
        logger.info(f"Generated prediction for {req.scheme_code}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in predict_nav_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predict/sequence", response_model=dict, summary="Sequential predictions")
async def predict_sequence(
    scheme_code: str,
    days: int = Query(7, ge=1, le=30, description="Number of days")
):
    """Get sequential NAV predictions"""
    try:
        # Get historical data
        history_df = get_nav_history(scheme_code)
        
        if history_df.empty:
            raise HTTPException(status_code=404, detail="NAV history not found")
        
        # Convert to pandas Series
        nav_series = pd.Series(
            history_df['nav'].values,
            index=pd.to_datetime(history_df['date'])
        )
        
        # Train predictor
        predictor_instance = NAVPredictor(lookback_days=60, forecast_days=1)
        predictor_instance.train(nav_series, validation_split=0.2)
        
        # Generate sequence
        seq_predictions = predictor_instance.predict_sequence(nav_series, n_days=days)
        
        # Get scheme name
        nav_data_df = get_enhanced_nav_data()
        scheme_data = nav_data_df[nav_data_df['Scheme Code'].astype(str) == str(scheme_code)]
        scheme_name = scheme_data.iloc[0]['Scheme Name'] if not scheme_data.empty else scheme_code
        
        result = {
            "scheme_code": scheme_code,
            "scheme_name": scheme_name,
            "current_nav": float(nav_series.iloc[-1]),
            "predictions": seq_predictions.to_dict('records')
        }
        
        logger.info(f"Generated {days}-day sequence for {scheme_code}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in predict_sequence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =========================================
# NEWS ENDPOINTS
# =========================================

@router.get("/news/market", summary="Get market news")
async def get_analyzed_market_news(
    topic: str = Query("equity mutual funds", description="News topic"),
    limit: int = Query(20, ge=5, le=50, description="Max articles")
):
    """Get market news"""
    try:
        result = news_agent.get_market_news(topic=topic, limit=limit)
        
        logger.info(f"Retrieved {result.get('total_articles', 0)} news articles")
        return result
    except Exception as e:
        logger.error(f"Error in get_analyzed_market_news: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/news/sources", summary="Get news sources")
async def get_news_sources():
    """Get list of news sources"""
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
            }
        ]
    }
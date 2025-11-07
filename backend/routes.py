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
from data.fetch_aum_data import RealAUMDataFetcher
from backend.schemas import *
from data.fetch_data import MutualFundDataFetcher
from analytics.financial_metrics import FinancialMetricsCalculator
from analytics.risk_metrics import RiskMetricsCalculator
from analytics.portfolio_analysis import PortfolioAnalyzer
from analytics.comparison import SchemeComparator
from models.predictor import NAVPredictor


# ==========================================
# PORTFOLIO MODELS (Pydantic)
# ==========================================

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

# ==========================================
# PORTFOLIO STORAGE
# ==========================================

PORTFOLIOS_DIR = Path("backend/data/portfolios")
PORTFOLIOS_DIR.mkdir(parents=True, exist_ok=True)


def load_portfolio(portfolio_id: str) -> dict:
    """Load portfolio from JSON file"""
    portfolio_file = PORTFOLIOS_DIR / f"{portfolio_id}.json"
    if not portfolio_file.exists():
        return None
    
    with open(portfolio_file, 'r') as f:
        return json.load(f)


def save_portfolio_to_file(portfolio_id: str, portfolio_data: dict):
    """Save portfolio to JSON file"""
    portfolio_file = PORTFOLIOS_DIR / f"{portfolio_id}.json"
    with open(portfolio_file, 'w') as f:
        json.dump(portfolio_data, f, indent=2)


def list_portfolios() -> list:
    """List all saved portfolios"""
    portfolios = []
    for portfolio_file in PORTFOLIOS_DIR.glob("*.json"):
        with open(portfolio_file, 'r') as f:
            portfolio = json.load(f)
            portfolios.append(portfolio)
    return portfolios


# ==========================================
# Create routers
# ==========================================

router = APIRouter()
health_router = APIRouter()


# ==========================================
# Initialize components
# ==========================================

data_fetcher = MutualFundDataFetcher()
fin_calc = FinancialMetricsCalculator()
risk_calc = RiskMetricsCalculator()
portfolio_analyzer = PortfolioAnalyzer()
scheme_comparator = SchemeComparator()


# ==========================================
# Health Check
# ==========================================

@health_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


# ==========================================
# Scheme Endpoints
# ==========================================

@router.get("/schemes/search")
async def search_schemes(
    query: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(50, ge=1, le=200, description="Max results")
):
    """Search mutual fund schemes by name, AMC, or code"""
    try:
        # Fetch latest data
        df = data_fetcher.fetch_amfi_daily_nav(save_to_cache=False)
        
        if df is None or len(df) == 0:
            raise HTTPException(status_code=503, detail="Unable to fetch data")
        
        # Add categories - WITH ERROR HANDLING
        try:
            if hasattr(data_fetcher, 'get_scheme_categories'):
                df = data_fetcher.get_scheme_categories(df)
            else:
                # If method doesn't exist, assign default category
                df['Category'] = 'Other'
        except Exception as cat_error:
            # If categorization fails, add a default category
            print(f"⚠️ Category assignment failed: {cat_error}")
            df['Category'] = 'Other'
        
        # Search
        results = data_fetcher.search_schemes(query, df)
        
        if results is None or len(results) == 0:
            return {
                "total_results": 0,
                "schemes": []
            }
        
        # Limit results
        results = results.head(limit)
        
        # Format response
        schemes = []
        for _, row in results.iterrows():
            try:
                schemes.append({
                    "scheme_code": str(row.get('Scheme_Code', '')),
                    "scheme_name": row.get('Scheme_Name', ''),
                    "amc": row.get('AMC', ''),
                    "category": row.get('Category', 'Other'),
                    "current_nav": float(row.get('NAV', 0)),
                    "nav_date": row['Date'].strftime('%Y-%m-%d') if pd.notna(row.get('Date')) else '',
                    "isin_div": row.get('ISIN_Div', ''),
                    "isin_growth": row.get('ISIN_Growth', '')
                })
            except Exception as row_error:
                # Skip malformed rows
                print(f"⚠️ Skipping row: {row_error}")
                continue
        
        return {
            "total_results": len(schemes),
            "schemes": schemes
        }
    
    except HTTPException:
        raise
    except Exception as e:
        # Log the actual error
        print(f"❌ Search error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")



@router.get("/schemes/{scheme_code}")
async def get_scheme_details(scheme_code: str):
    """Get details for a specific scheme"""
    try:
        info = data_fetcher.get_scheme_info(scheme_code)
        
        if not info:
            raise HTTPException(status_code=404, detail="Scheme not found")
        
        return {
            "scheme_code": info.get('scheme_code', scheme_code),
            "scheme_name": info.get('scheme_name', 'Unknown'),
            "amc": info.get('fund_house'),
            "category": info.get('scheme_category'),
            "current_nav": float(info.get('scheme_nav', 0)),
            "nav_date": info.get('nav_date', '')
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Metrics Endpoints
# ==========================================

@router.get("/metrics/financial/{scheme_code}")
async def get_financial_metrics(scheme_code: str):
    """Get financial metrics for a scheme"""
    try:
        df = data_fetcher.fetch_historical_nav_mfapi(scheme_code)
        
        if df is None or len(df) < 100:
            raise HTTPException(status_code=404, detail="Insufficient historical data")
        
        nav_series = df.set_index('Date')['NAV']
        date_series = df['Date']
        
        metrics = fin_calc.get_comprehensive_metrics(nav_series, date_series)
        
        return {
            "current_nav": metrics['current_nav'],
            "cagr": metrics.get('cagr'),
            "annualized_return": metrics['annualized_return'],
            "sharpe_ratio": metrics.get('sharpe_ratio'),
            "sortino_ratio": metrics.get('sortino_ratio'),
            "absolute_returns": metrics.get('absolute_returns', {})
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/risk/{scheme_code}")
async def get_risk_metrics(scheme_code: str):
    """Get risk metrics for a scheme"""
    try:
        df = data_fetcher.fetch_historical_nav_mfapi(scheme_code)
        
        if df is None or len(df) < 100:
            raise HTTPException(status_code=404, detail="Insufficient historical data")
        
        nav_series = df.set_index('Date')['NAV']
        date_series = df['Date']
        
        metrics = risk_calc.get_comprehensive_risk_metrics(nav_series, date_series)
        
        return {
            "volatility": metrics['volatility'],
            "downside_deviation": metrics['downside_deviation'],
            "max_drawdown": metrics['max_drawdown'],
            "ulcer_index": metrics['ulcer_index'],
            "var_95": metrics['var_95'],
            "cvar_95": metrics['cvar_95'],
            "calmar_ratio": metrics.get('calmar_ratio')
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/comprehensive/{scheme_code}")
async def get_comprehensive_metrics(scheme_code: str):
    """Get all metrics (financial + risk) for a scheme"""
    try:
        info = data_fetcher.get_scheme_info(scheme_code)
        scheme_name = info.get('scheme_name', 'Unknown') if info else 'Unknown'
        
        financial = await get_financial_metrics(scheme_code)
        risk = await get_risk_metrics(scheme_code)
        
        return {
            "scheme_code": scheme_code,
            "scheme_name": scheme_name,
            "financial_metrics": financial,
            "risk_metrics": risk
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Portfolio Endpoints
# ==========================================

@router.post("/portfolio/analyze")
async def analyze_portfolio(portfolio: PortfolioRequest):
    """Analyze a portfolio of schemes with given weights"""
    try:
        total_weight = sum([s.weight for s in portfolio.schemes])
        if not (0.99 <= total_weight <= 1.01):
            raise HTTPException(status_code=400, detail="Weights must sum to 1.0")
        
        schemes_data = {}
        weights = {}
        
        for scheme in portfolio.schemes:
            df = data_fetcher.fetch_historical_nav_mfapi(scheme.scheme_code)
            if df is None or len(df) < 100:
                raise HTTPException(
                    status_code=404,
                    detail=f"Insufficient data for scheme {scheme.scheme_code}"
                )
            
            nav_series = df.set_index('Date')['NAV']
            schemes_data[scheme.scheme_code] = nav_series
            weights[scheme.scheme_code] = scheme.weight
        
        metrics = portfolio_analyzer.calculate_portfolio_metrics(schemes_data, weights)
        div_score = portfolio_analyzer.get_diversification_score(schemes_data, weights)
        
        return {
            "annualized_return": metrics['annualized_return'],
            "volatility": metrics['volatility'],
            "sharpe_ratio": metrics['sharpe_ratio'],
            "sortino_ratio": metrics['sortino_ratio'],
            "max_drawdown": metrics['max_drawdown'],
            "var_95": metrics['var_95'],
            "diversification_score": div_score
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schemes/compare")
async def compare_schemes_endpoint(scheme_codes: List[str]):
    """Compare multiple schemes side by side"""
    try:
        if len(scheme_codes) < 2:
            raise HTTPException(status_code=400, detail="Need at least 2 schemes")
        
        if len(scheme_codes) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 schemes allowed")
        
        schemes_data = {}
        scheme_info = {}
        
        for code in scheme_codes:
            df = data_fetcher.fetch_historical_nav_mfapi(code)
            
            if df is not None and len(df) >= 100:
                nav_series = df.set_index('Date')['NAV']
                schemes_data[code] = nav_series
                
                info = data_fetcher.get_scheme_info(code)
                scheme_info[code] = info.get('scheme_name', code) if info else code
        
        if len(schemes_data) < 2:
            raise HTTPException(status_code=404, detail="Insufficient data for comparison")
        
        comparison_result = scheme_comparator.compare_schemes(
            list(schemes_data.keys()),
            schemes_data
        )
        
        df_comparison = comparison_result['comparison']
        
        schemes_list = []
        for idx, row in df_comparison.iterrows():
            schemes_list.append({
                'scheme_code': row['scheme_code'],
                'scheme_name': scheme_info.get(row['scheme_code'], row['scheme_code']),
                'current_nav': float(row['current_nav']),
                'cagr': float(row['cagr']) if pd.notna(row['cagr']) else None,
                'annualized_return': float(row['annualized_return']),
                'sharpe_ratio': float(row['sharpe_ratio']) if pd.notna(row['sharpe_ratio']) else None,
                'sortino_ratio': float(row['sortino_ratio']) if pd.notna(row['sortino_ratio']) else None,
                'volatility': float(row['volatility']),
                'max_drawdown': float(row['max_drawdown']),
                'downside_deviation': float(row['downside_deviation']),
                'var_95': float(row['var_95']),
                'calmar_ratio': float(row['calmar_ratio']) if pd.notna(row['calmar_ratio']) else None
            })
        
        best = comparison_result['best_schemes']
        
        return {
            'total_schemes': len(schemes_list),
            'schemes': schemes_list,
            'best_by_sharpe': scheme_info.get(best.get('best_by_sharpe', {}).get('scheme_code', ''), ''),
            'best_by_return': scheme_info.get(best.get('best_by_return', {}).get('scheme_code', ''), ''),
            'comparison_date': datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Prediction Endpoints
# ==========================================

@router.post("/predict/single")
async def predict_nav(request: PredictionRequestModel):
    """Predict future NAV for a scheme using ML model"""
    try:
        scheme_code = request.scheme_code
        forecast_days = request.forecast_days
        
        df = data_fetcher.fetch_historical_nav_mfapi(scheme_code)
        
        if df is None or len(df) < 200:
            raise HTTPException(
                status_code=404, 
                detail=f"Insufficient historical data for prediction. Found {len(df) if df is not None else 0} days, need 200+."
            )
        
        info = data_fetcher.get_scheme_info(scheme_code)
        scheme_name = info.get('scheme_name', 'Unknown') if info else 'Unknown'
        
        nav_series = df.set_index('Date')['NAV']
        
        predictor = NAVPredictor(
            lookback_days=60,
            forecast_days=forecast_days
        )
        predictor.train(nav_series, validation_split=0.2)
        
        prediction = predictor.predict(nav_series)
        
        return {
            "scheme_code": scheme_code,
            "scheme_name": scheme_name,
            "current_nav": float(prediction['Current_NAV'].iloc[0]),
            "prediction": {
                "date": prediction['Date'].iloc[0].strftime('%Y-%m-%d') if hasattr(prediction['Date'].iloc[0], 'strftime') else str(prediction['Date'].iloc[0]),
                "predicted_nav": float(prediction['Predicted_NAV'].iloc[0]),
                "current_nav": float(prediction['Current_NAV'].iloc[0]),
                "change": float(prediction['Change'].iloc[0]),
                "change_percent": float(prediction['Change_Percent'].iloc[0])
            },
            "confidence": "Medium"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predict/sequence")
async def predict_sequence(
    scheme_code: str = Query(..., description="Scheme code"),
    days: int = Query(7, ge=1, le=30, description="Number of days to predict")
):
    """Sequential NAV predictions for multiple days ahead"""
    try:
        df = data_fetcher.fetch_historical_nav_mfapi(scheme_code)
        
        if df is None or len(df) < 200:
            raise HTTPException(status_code=404, detail="Insufficient historical data")
        
        info = data_fetcher.get_scheme_info(scheme_code)
        scheme_name = info.get('scheme_name', 'Unknown') if info else 'Unknown'
        
        nav_series = df.set_index('Date')['NAV']
        
        predictor = NAVPredictor(lookback_days=60, forecast_days=1)
        predictor.train(nav_series, validation_split=0.2)
        
        predictions = predictor.predict_sequence(nav_series, n_days=days)
        
        pred_list = []
        for _, row in predictions.iterrows():
            pred_list.append({
                "day": int(row['Day']),
                "predicted_nav": float(row['Predicted_NAV']),
                "change_from_today": float(row['Change_from_today']),
                "change_percent": float(row['Change_percent'])
            })
        
        return {
            "scheme_code": scheme_code,
            "scheme_name": scheme_name,
            "current_nav": float(nav_series.iloc[-1]),
            "predictions": pred_list
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ==========================================
# Historical Data Endpoints
# ==========================================

@router.get("/historical/{scheme_code}")
async def get_historical_data(
    scheme_code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(365, ge=1, le=2000, description="Max data points")
):
    """Get historical NAV data for a scheme"""
    try:
        df = data_fetcher.fetch_historical_nav_mfapi(scheme_code)
        
        if df is None or len(df) == 0:
            raise HTTPException(status_code=404, detail="No historical data found")
        
        if start_date:
            df = df[df['Date'] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df['Date'] <= pd.to_datetime(end_date)]
        
        df = df.tail(limit)
        
        info = data_fetcher.get_scheme_info(scheme_code)
        scheme_name = info.get('scheme_name', 'Unknown') if info else 'Unknown'
        
        data_points = []
        for _, row in df.iterrows():
            data_points.append({
                "date": row['Date'].strftime('%Y-%m-%d'),
                "nav": float(row['NAV'])
            })
        
        return {
            "scheme_code": scheme_code,
            "scheme_name": scheme_name,
            "data": data_points,
            "total_records": len(data_points)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Portfolio Save/Manage Endpoints (NEW)
# ==========================================

@router.post("/portfolio/save", response_model=PortfolioResponse)
async def save_portfolio_endpoint(portfolio_req: PortfolioRequest):
    """Save a new portfolio"""
    try:
        if not portfolio_req.name or len(portfolio_req.name.strip()) == 0:
            raise HTTPException(status_code=400, detail="Portfolio name cannot be empty")
        
        if abs(portfolio_req.total_weight - 1.0) > 0.01:
            raise HTTPException(status_code=400, detail=f"Total weight must be 100%, got {portfolio_req.total_weight*100:.1f}%")
        
        if len(portfolio_req.schemes) < 2:
            raise HTTPException(status_code=400, detail="Portfolio must have at least 2 schemes")
        
        existing_portfolios = list_portfolios()
        if any(p['name'] == portfolio_req.name for p in existing_portfolios):
            raise HTTPException(status_code=409, detail=f"Portfolio '{portfolio_req.name}' already exists")
        
        portfolio_id = str(uuid.uuid4())
        
        portfolio = {
            "id": portfolio_id,
            "name": portfolio_req.name,
            "description": portfolio_req.description,
            "schemes": [
                {
                    "scheme_code": s.scheme_code,
                    "scheme_name": s.scheme_name,
                    "weight": s.weight
                }
                for s in portfolio_req.schemes
            ],
            "created_at": portfolio_req.created_at,
            "total_weight": portfolio_req.total_weight
        }
        
        save_portfolio_to_file(portfolio_id, portfolio)
        
        return PortfolioResponse(
            success=True,
            portfolio_id=portfolio_id,
            message=f"Portfolio '{portfolio_req.name}' saved successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio/list")
async def get_portfolios_list():
    """Get list of all saved portfolios"""
    try:
        portfolios = list_portfolios()
        return {
            "success": True,
            "total": len(portfolios),
            "portfolios": portfolios
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio/{portfolio_id}")
async def get_portfolio_endpoint(portfolio_id: str):
    """Get a specific portfolio"""
    try:
        portfolio = load_portfolio(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail=f"Portfolio '{portfolio_id}' not found")
        return {
            "success": True,
            "portfolio": portfolio
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/portfolio/{portfolio_id}")
async def delete_portfolio_endpoint(portfolio_id: str):
    """Delete a portfolio"""
    try:
        portfolio_file = PORTFOLIOS_DIR / f"{portfolio_id}.json"
        if not portfolio_file.exists():
            raise HTTPException(status_code=404, detail=f"Portfolio '{portfolio_id}' not found")
        portfolio_file.unlink()
        return {
            "success": True,
            "message": "Portfolio deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/portfolio/{portfolio_id}")
async def update_portfolio_endpoint(portfolio_id: str, portfolio_req: PortfolioRequest):
    """Update an existing portfolio"""
    try:
        portfolio_file = PORTFOLIOS_DIR / f"{portfolio_id}.json"
        if not portfolio_file.exists():
            raise HTTPException(status_code=404, detail=f"Portfolio '{portfolio_id}' not found")
        
        if abs(portfolio_req.total_weight - 1.0) > 0.01:
            raise HTTPException(status_code=400, detail=f"Total weight must be 100%")
        
        portfolio = load_portfolio(portfolio_id)
        
        portfolio['name'] = portfolio_req.name
        portfolio['description'] = portfolio_req.description
        portfolio['schemes'] = [
            {
                "scheme_code": s.scheme_code,
                "scheme_name": s.scheme_name,
                "weight": s.weight
            }
            for s in portfolio_req.schemes
        ]
        portfolio['total_weight'] = portfolio_req.total_weight
        portfolio['updated_at'] = datetime.now().isoformat()
        
        save_portfolio_to_file(portfolio_id, portfolio)
        
        return {
            "success": True,
            "portfolio_id": portfolio_id,
            "message": "Portfolio updated successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/aum/top_amcs")
async def get_top_amcs_by_aum(limit: int = Query(10, ge=1, le=50)):
    """Get top AMCs by actual AUM"""
    try:
        top_amcs = RealAUMDataFetcher.get_top_amc_by_aum(limit=limit)
        
        if top_amcs is None:
            raise HTTPException(status_code=503, detail="AUM data not available")
        
        # Convert to dict
        amc_data = [
            {"amc": amc, "aum": float(aum_value)}
            for amc, aum_value in top_amcs.items()
        ]
        
        return {
            "total_amcs": len(amc_data),
            "data": amc_data,
            "note": "AUM data updated weekly from external source"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/aum/total")
async def get_total_industry_aum():
    """Get total AUM across all schemes"""
    try:
        total_aum = RealAUMDataFetcher.get_total_aum()
        
        if total_aum is None:
            raise HTTPException(status_code=503, detail="AUM data not available")
        
        return {
            "total_aum": float(total_aum),
            "total_aum_crores": float(total_aum / 100),
            "total_aum_lakh_crores": float(total_aum / 100000),
            "currency": "INR",
            "note": "AUM data updated weekly"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))    

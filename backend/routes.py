"""
API routes for MF_NAVigator
All REST API endpoints for the application
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict
from datetime import datetime
import pandas as pd

from backend.schemas import *
from data.fetch_data import MutualFundDataFetcher
from analytics.financial_metrics import FinancialMetricsCalculator
from analytics.risk_metrics import RiskMetricsCalculator
from analytics.portfolio_analysis import PortfolioAnalyzer
from analytics.comparison import SchemeComparator
from models.predictor import NAVPredictor


# Create routers
router = APIRouter()
health_router = APIRouter()

# Initialize components
data_fetcher = MutualFundDataFetcher()
fin_calc = FinancialMetricsCalculator()
risk_calc = RiskMetricsCalculator()
portfolio_analyzer = PortfolioAnalyzer()
scheme_comparator = SchemeComparator()


# ==========================================
# Health Check
# ==========================================

@health_router.get("/health", response_model=HealthCheck)
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

@router.get("/schemes/search", response_model=SchemeSearchResponse)
async def search_schemes(
    query: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(50, ge=1, le=200, description="Max results")
):
    """
    Search mutual fund schemes by name, AMC, or code
    
    - **query**: Search term (minimum 2 characters)
    - **limit**: Maximum number of results to return
    """
    try:
        # Fetch latest data
        df = data_fetcher.fetch_amfi_daily_nav(save_to_cache=False)
        
        # Add categories
        df = data_fetcher.get_scheme_categories(df)
        
        # Search
        results = data_fetcher.search_schemes(query, df)
        
        # Limit results
        results = results.head(limit)
        
        # Format response
        schemes = []
        for _, row in results.iterrows():
            schemes.append({
                "scheme_code": str(row['Scheme_Code']),
                "scheme_name": row['Scheme_Name'],
                "amc": row['AMC'],
                "category": row.get('Category'),
                "current_nav": float(row['NAV']),
                "nav_date": row['Date'].strftime('%Y-%m-%d'),
                "isin_div": row.get('ISIN_Div'),
                "isin_growth": row.get('ISIN_Growth')
            })
        
        return {
            "total_results": len(schemes),
            "schemes": schemes
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schemes/{scheme_code}", response_model=SchemeDetail)
async def get_scheme_details(scheme_code: str):
    """
    Get details for a specific scheme
    
    - **scheme_code**: The scheme code
    """
    try:
        # Get scheme info from MFapi
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

@router.get("/metrics/financial/{scheme_code}", response_model=FinancialMetrics)
async def get_financial_metrics(scheme_code: str):
    """
    Get financial metrics for a scheme (CAGR, Sharpe, returns, etc.)
    
    - **scheme_code**: The scheme code
    """
    try:
        # Fetch historical data
        df = data_fetcher.fetch_historical_nav_mfapi(scheme_code)
        
        if df is None or len(df) < 100:
            raise HTTPException(status_code=404, detail="Insufficient historical data")
        
        # Calculate metrics
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


@router.get("/metrics/risk/{scheme_code}", response_model=RiskMetrics)
async def get_risk_metrics(scheme_code: str):
    """
    Get risk metrics for a scheme (volatility, drawdown, VaR, etc.)
    
    - **scheme_code**: The scheme code
    """
    try:
        # Fetch historical data
        df = data_fetcher.fetch_historical_nav_mfapi(scheme_code)
        
        if df is None or len(df) < 100:
            raise HTTPException(status_code=404, detail="Insufficient historical data")
        
        # Calculate metrics
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


@router.get("/metrics/comprehensive/{scheme_code}", response_model=ComprehensiveMetrics)
async def get_comprehensive_metrics(scheme_code: str):
    """
    Get all metrics (financial + risk) for a scheme
    
    - **scheme_code**: The scheme code
    """
    try:
        # Get scheme info
        info = data_fetcher.get_scheme_info(scheme_code)
        scheme_name = info.get('scheme_name', 'Unknown') if info else 'Unknown'
        
        # Get both metrics
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

@router.post("/portfolio/analyze", response_model=PortfolioMetrics)
async def analyze_portfolio(portfolio: PortfolioRequest):
    """
    Analyze a portfolio of schemes with given weights
    
    Weights must sum to 1.0 (100%)
    """
    try:
        # Validate weights sum to 1
        total_weight = sum([s.weight for s in portfolio.schemes])
        if not (0.99 <= total_weight <= 1.01):
            raise HTTPException(status_code=400, detail="Weights must sum to 1.0")
        
        # Fetch historical data for all schemes
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
        
        # Calculate portfolio metrics
        metrics = portfolio_analyzer.calculate_portfolio_metrics(schemes_data, weights)
        
        # Calculate diversification
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


@router.post("/portfolio/compare", response_model=Dict)
async def compare_schemes_old(scheme_codes: List[str]):
    """
    Compare multiple schemes side by side (legacy endpoint)
    Use /schemes/compare instead
    
    - **scheme_codes**: List of scheme codes to compare
    """
    try:
        if len(scheme_codes) < 2:
            raise HTTPException(status_code=400, detail="Need at least 2 schemes to compare")
        
        if len(scheme_codes) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 schemes allowed")
        
        # Fetch data for all schemes
        schemes_data = {}
        
        for code in scheme_codes:
            df = data_fetcher.fetch_historical_nav_mfapi(code)
            if df is not None and len(df) >= 100:
                nav_series = df.set_index('Date')['NAV']
                schemes_data[code] = nav_series
        
        if len(schemes_data) < 2:
            raise HTTPException(status_code=404, detail="Insufficient data for comparison")
        
        # Compare schemes
        comparison_df = portfolio_analyzer.compare_schemes(schemes_data)
        
        # Format response
        schemes = []
        for _, row in comparison_df.iterrows():
            schemes.append({
                "scheme": row['Scheme'],
                "current_nav": row['Current NAV'],
                "cagr": row['CAGR (%)'] if not pd.isna(row['CAGR (%)']) else None,
                "return_1y": row['1Y Return (%)'] if not pd.isna(row['1Y Return (%)']) else None,
                "return_3y": row['3Y Return (%)'] if not pd.isna(row['3Y Return (%)']) else None,
                "volatility": row['Volatility (%)'],
                "max_drawdown": row['Max Drawdown (%)'],
                "sharpe_ratio": row['Sharpe Ratio'] if not pd.isna(row['Sharpe Ratio']) else None
            })
        
        # Find best schemes
        best_sharpe = comparison_df.loc[comparison_df['Sharpe Ratio'].idxmax(), 'Scheme']
        best_return = comparison_df.loc[comparison_df['CAGR (%)'].idxmax(), 'Scheme']
        
        return {
            "schemes": schemes,
            "best_by_sharpe": best_sharpe,
            "best_by_return": best_return
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schemes/compare", response_model=Dict)
async def compare_schemes_endpoint(scheme_codes: List[str]):
    """
    Compare multiple schemes side by side with detailed metrics
    
    - **scheme_codes**: List of scheme codes to compare (2-10 schemes)
    """
    try:
        if len(scheme_codes) < 2:
            raise HTTPException(status_code=400, detail="Need at least 2 schemes")
        
        if len(scheme_codes) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 schemes allowed")
        
        # Fetch data for all schemes
        schemes_data = {}
        scheme_info = {}
        
        for code in scheme_codes:
            df = data_fetcher.fetch_historical_nav_mfapi(code)
            
            if df is not None and len(df) >= 100:
                nav_series = df.set_index('Date')['NAV']
                schemes_data[code] = nav_series
                
                # Get scheme info
                info = data_fetcher.get_scheme_info(code)
                scheme_info[code] = info.get('scheme_name', code) if info else code
        
        if len(schemes_data) < 2:
            raise HTTPException(status_code=404, detail="Insufficient data for comparison")
        
        # Use comparator to get detailed comparison
        comparison_result = scheme_comparator.compare_schemes(
            list(schemes_data.keys()),
            schemes_data
        )
        
        # Format response
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

@router.post("/predict/single", response_model=PredictionResponse)
async def predict_nav(request: PredictionRequest):
    """
    Predict future NAV for a scheme using ML model
    
    - **scheme_code**: Scheme code
    - **forecast_days**: Number of days to forecast (1-90 days)
    """
    try:
        # Fetch historical data
        df = data_fetcher.fetch_historical_nav_mfapi(request.scheme_code)
        
        if df is None or len(df) < 200:
            raise HTTPException(status_code=404, detail="Insufficient historical data for prediction")
        
        # Get scheme info
        info = data_fetcher.get_scheme_info(request.scheme_code)
        scheme_name = info.get('scheme_name', 'Unknown') if info else 'Unknown'
        
        # Train predictor
        nav_series = df.set_index('Date')['NAV']
        
        predictor = NAVPredictor(
            lookback_days=60,
            forecast_days=request.forecast_days
        )
        predictor.train(nav_series, validation_split=0.2)
        
        # Make prediction
        prediction = predictor.predict(nav_series)
        
        return {
            "scheme_code": request.scheme_code,
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


@router.post("/predict/sequence", response_model=SequentialPredictionResponse)
async def predict_sequence(
    scheme_code: str,
    days: int = Query(7, ge=1, le=30, description="Number of days to predict")
):
    """
    Sequential NAV predictions for multiple days ahead
    
    - **scheme_code**: Scheme code
    - **days**: Number of days to predict (1-30 days)
    """
    try:
        # Fetch historical data
        df = data_fetcher.fetch_historical_nav_mfapi(scheme_code)
        
        if df is None or len(df) < 200:
            raise HTTPException(status_code=404, detail="Insufficient historical data")
        
        # Get scheme info
        info = data_fetcher.get_scheme_info(scheme_code)
        scheme_name = info.get('scheme_name', 'Unknown') if info else 'Unknown'
        
        # Train and predict
        nav_series = df.set_index('Date')['NAV']
        
        predictor = NAVPredictor(lookback_days=60, forecast_days=1)
        predictor.train(nav_series, validation_split=0.2)
        
        predictions = predictor.predict_sequence(nav_series, n_days=days)
        
        # Format response
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

@router.get("/historical/{scheme_code}", response_model=HistoricalDataResponse)
async def get_historical_data(
    scheme_code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(365, ge=1, le=2000, description="Max data points")
):
    """
    Get historical NAV data for a scheme
    
    - **scheme_code**: Scheme code
    - **start_date**: Start date (YYYY-MM-DD) - optional
    - **end_date**: End date (YYYY-MM-DD) - optional
    - **limit**: Maximum data points to return (1-2000)
    """
    try:
        # Fetch data
        df = data_fetcher.fetch_historical_nav_mfapi(scheme_code)
        
        if df is None or len(df) == 0:
            raise HTTPException(status_code=404, detail="No historical data found")
        
        # Filter by date range
        if start_date:
            df = df[df['Date'] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df['Date'] <= pd.to_datetime(end_date)]
        
        # Limit results
        df = df.tail(limit)
        
        # Get scheme name
        info = data_fetcher.get_scheme_info(scheme_code)
        scheme_name = info.get('scheme_name', 'Unknown') if info else 'Unknown'
        
        # Format response
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

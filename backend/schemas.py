from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime



# Scheme Schemas

class SchemeBase(BaseModel):
    """Base scheme information"""
    scheme_code: str
    scheme_name: str
    amc: Optional[str] = None
    category: Optional[str] = None


class SchemeDetail(SchemeBase):
    """Detailed scheme information"""
    current_nav: float
    nav_date: str
    isin_div: Optional[str] = None
    isin_growth: Optional[str] = None


class SchemeSearch(BaseModel):
    """Scheme search request"""
    query: str = Field(..., min_length=2, description="Search query (min 2 characters)")


class SchemeSearchResponse(BaseModel):
    """Scheme search response"""
    total_results: int
    schemes: List[SchemeDetail]


# Financial Metrics Schemas

class FinancialMetrics(BaseModel):
    """Financial performance metrics"""
    current_nav: float
    cagr: Optional[float] = None
    annualized_return: float
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    absolute_returns: Dict[str, float]


class RiskMetrics(BaseModel):
    """Risk metrics"""
    volatility: float
    downside_deviation: float
    max_drawdown: float
    ulcer_index: float
    var_95: float
    cvar_95: float
    calmar_ratio: Optional[float] = None


class ComprehensiveMetrics(BaseModel):
    """Combined financial and risk metrics"""
    scheme_code: str
    scheme_name: str
    financial_metrics: FinancialMetrics
    risk_metrics: RiskMetrics

# Portfolio Schemas

class PortfolioScheme(BaseModel):
    """Scheme in portfolio"""
    scheme_code: str
    weight: float = Field(..., ge=0, le=1, description="Weight between 0 and 1")


class PortfolioRequest(BaseModel):
    """Portfolio analysis request"""
    schemes: List[PortfolioScheme]
    
    class Config:
        json_schema_extra = {
            "example": {
                "schemes": [
                    {"scheme_code": "119551", "weight": 0.4},
                    {"scheme_code": "120503", "weight": 0.3},
                    {"scheme_code": "118989", "weight": 0.3}
                ]
            }
        }


class PortfolioMetrics(BaseModel):
    """Portfolio performance metrics"""
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    var_95: float
    diversification_score: float


class SchemeComparison(BaseModel):
    """Comparison of multiple schemes"""
    scheme: str
    current_nav: float
    cagr: Optional[float] = None
    return_1y: Optional[float] = None
    return_3y: Optional[float] = None
    volatility: float
    max_drawdown: float
    sharpe_ratio: Optional[float] = None


class ComparisonResponse(BaseModel):
    """Response for scheme comparison"""
    schemes: List[SchemeComparison]
    best_by_sharpe: str
    best_by_return: str


# Prediction Schemas

class PredictionRequest(BaseModel):
    """NAV prediction request"""
    scheme_code: str
    forecast_days: int = Field(default=30, ge=1, le=90, description="Days to forecast (1-90)")


class PredictionResult(BaseModel):
    """Single prediction result"""
    date: str
    predicted_nav: float
    current_nav: float
    change: float
    change_percent: float


class SequentialPrediction(BaseModel):
    """Sequential prediction result"""
    day: int
    predicted_nav: float
    change_from_today: float
    change_percent: float


class PredictionResponse(BaseModel):
    """Prediction response"""
    scheme_code: str
    scheme_name: str
    current_nav: float
    prediction: PredictionResult
    confidence: str = "Medium"


class SequentialPredictionResponse(BaseModel):
    """Sequential predictions response"""
    scheme_code: str
    scheme_name: str
    current_nav: float
    predictions: List[SequentialPrediction]


class FeatureImportance(BaseModel):
    """Feature importance"""
    feature: str
    importance: float


class ModelMetrics(BaseModel):
    """Model performance metrics"""
    mae: float
    mape: float
    r2: float
    directional_accuracy: float


# General Response Schemas

class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: str


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    timestamp: str


class SuccessResponse(BaseModel):
    """Generic success response"""
    message: str
    data: Optional[Dict] = None


# Historical Data Schemas

class HistoricalDataRequest(BaseModel):
    """Historical NAV data request"""
    scheme_code: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class NAVDataPoint(BaseModel):
    """Single NAV data point"""
    date: str
    nav: float


class HistoricalDataResponse(BaseModel):
    """Historical NAV data response"""
    scheme_code: str
    scheme_name: str
    data: List[NAVDataPoint]
    total_records: int

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from backend.config import settings
from backend.routes import router, health_router
# Create FastAPI app
app = FastAPI(
    title="MF_NAVigator API",
    description="""
    🚀 **MF_NAVigator** - Mutual Fund Analytics & Prediction Platform
    
    ## Features
    
    * **Scheme Search** - Search 9,000+ mutual fund schemes
    * **Financial Metrics** - CAGR, Sharpe, Sortino, returns
    * **Risk Metrics** - Volatility, VaR, max drawdown
    * **Portfolio Analysis** - Compare and analyze portfolios
    * **NAV Predictions** - ML-powered NAV forecasting
    * **Historical Data** - Access complete NAV history
    
    ## Tech Stack
    
    * FastAPI for API framework
    * XGBoost for predictions
    * Pandas for data processing
    * Real-time data from AMFI & MFapi.in
    """,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, tags=["Health"])
app.include_router(router, prefix="/api/v1", tags=["API"])


@app.get("/", include_in_schema=False)
async def root():
    """Redirect to docs"""
    return RedirectResponse(url="/docs")


@app.on_event("startup")
async def startup_event():
    """Run on app startup"""
    print("="*70)
    print(f"🚀 {settings.APP_NAME} API Starting...")
    print(f"   Version: {settings.APP_VERSION}")
    print(f"   Docs: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    print("="*70)


@app.on_event("shutdown")
async def shutdown_event():
    """Run on app shutdown"""
    print("\n🛑 Shutting down MF_NAVigator API...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )

"""
MF_NAVigator - FastAPI Backend Main Application
Entry point for the API server
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.openapi.utils import get_openapi
import logging
import sys
from pathlib import Path

# ==========================================
# SETUP PATH & LOGGING
# ==========================================
# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==========================================
# IMPORTS
# ==========================================
try:
    from backend.config import settings
    logger.info("✅ Config loaded")
except Exception as e:
    logger.error(f"❌ Config import failed: {e}")
    raise

try:
    from backend.routes import router, health_router
    logger.info("✅ Routes imported")
except Exception as e:
    logger.error(f"❌ Routes import failed: {e}")
    raise

# ==========================================
# CREATE FASTAPI APP
# ==========================================
app = FastAPI(
    title="MF_NAVigator API",
    description="""
🚀 **MF_NAVigator** - Mutual Fund Analytics & Prediction Platform

## 📊 Features
- **Scheme Search** - Search 9,000+ mutual fund schemes
- **Financial Metrics** - CAGR, Sharpe Ratio, Sortino Ratio
- **Risk Metrics** - Volatility, VaR, Max Drawdown
- **Portfolio Analysis** - Compare and analyze portfolios
- **NAV Predictions** - ML-powered NAV forecasting
- **Historical Data** - Complete NAV history
- **Market News** - Latest equity & hybrid fund news
- **Analytics** - Comprehensive financial analysis

## 🔧 Tech Stack
- FastAPI for REST API framework
- XGBoost for ML predictions
- Pandas for data processing
- Real-time data from AMFI & MFapi.in
- LangChain for AI-powered news analysis

## 📚 Documentation
- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI Schema: `/openapi.json`

## 🌐 API Base URL
- `http://localhost:8000/api/v1`
""",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ==========================================
# CORS MIDDLEWARE
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# ==========================================
# INCLUDE ROUTERS
# ==========================================
logger.info("📋 Registering routers...")

# ✅ FIXED: Router already has prefix="/api/v1", so DON'T add it again
app.include_router(health_router, tags=["Health"])
app.include_router(router, tags=["API"])

logger.info("✅ Routers registered successfully")

# ==========================================
# ROOT REDIRECT
# ==========================================
@app.get("/", include_in_schema=False)
async def root():
    """Redirect to API documentation"""
    return RedirectResponse(url="/docs")

# ==========================================
# CUSTOM OPENAPI SCHEMA
# ==========================================
def custom_openapi():
    """Customize OpenAPI schema"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="MF_NAVigator API",
        version=settings.APP_VERSION,
        description=app.description,
        routes=app.routes,
    )
    
    openapi_schema["info"]["x-logo"] = {
        "url": "https://img.icons8.com/fluency/96/000000/profit-report.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# ==========================================
# STARTUP EVENT
# ==========================================
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("")
    logger.info("=" * 70)
    logger.info("🚀 MF_NAVigator Backend Starting...")
    logger.info("=" * 70)
    logger.info(f"   Application: {settings.APP_NAME}")
    logger.info(f"   Version: {settings.APP_VERSION}")
    logger.info(f"   Environment: {'DEBUG' if settings.DEBUG else 'PRODUCTION'}")
    logger.info(f"   Host: {settings.API_HOST}")
    logger.info(f"   Port: {settings.API_PORT}")
    logger.info("")
    logger.info("📚 API Documentation:")
    logger.info(f"   Swagger UI: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    logger.info(f"   ReDoc: http://{settings.API_HOST}:{settings.API_PORT}/redoc")
    logger.info(f"   OpenAPI: http://{settings.API_HOST}:{settings.API_PORT}/openapi.json")
    logger.info("")
    logger.info("🔗 API Base URL:")
    logger.info(f"   http://{settings.API_HOST}:{settings.API_PORT}/api/v1")
    logger.info("")
    logger.info("=" * 70)
    logger.info("✅ Backend ready to accept requests!")
    logger.info("=" * 70)
    logger.info("")

# ==========================================
# SHUTDOWN EVENT
# ==========================================
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("")
    logger.info("🛑 Shutting down MF_NAVigator Backend...")
    logger.info("")

# ==========================================
# LIFESPAN CONTEXT
# ==========================================
@app.get("/api/v1/status", tags=["Health"])
async def get_status():
    """Get detailed server status"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "timestamp": str(Path(__file__).stat().st_mtime)
    }

# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting Uvicorn server...")
    
    uvicorn.run(
        "backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
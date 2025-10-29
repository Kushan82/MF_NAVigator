from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""
    
    # Application Info
    APP_NAME: str = "MF_NAVigator"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Data Sources
    AMFI_NAV_URL: str = "https://www.amfiindia.com/spages/NAVAll.txt"
    MFAPI_BASE_URL: str = "https://api.mfapi.in"
    GITHUB_DATA_URL: str = "https://raw.githubusercontent.com/InertExpert2911/Mutual_Fund_Data/main/"
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data" / "cache"
    MODELS_DIR: Path = BASE_DIR / "models"
    LOGS_DIR: Path = BASE_DIR / "logs"
    
    # ML Model Settings
    MODEL_TYPE: str = "xgboost"
    PREDICTION_DAYS: int = 30
    TRAIN_TEST_SPLIT: float = 0.8
    
    # Financial Metrics
    RISK_FREE_RATE: float = 0.06  # 6% annual risk-free rate (India)
    TRADING_DAYS_PER_YEAR: int = 252
    
    # Cache Settings
    CACHE_ENABLED: bool = True
    CACHE_TTL: int = 3600  # 1 hour in seconds
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create global settings instance
settings = Settings()

# Create necessary directories
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)

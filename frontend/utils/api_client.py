"""
API Client for MF_NAVigator Frontend - COMPLETE FIXED VERSION
Centralized wrapper for all backend API calls
"""

import requests
from typing import Dict, List, Optional, Any
import streamlit as st
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIClient:
    """Centralized API client for MF_NAVigator frontend"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize API client
        
        Args:
            base_url: Base URL of the API (default: http://localhost:8000)
        """
        self.base_url = base_url
        self.api_v1 = f"{base_url}/api/v1"
        self.timeout = 30
        logger.info(f"✅ APIClient initialized with base URL: {base_url}")
    
    # ==========================================
    # CORE REQUEST METHOD
    # ==========================================
    
    def _make_request(
        self,
        method: str,
        url: str,
        show_error: bool = True,
        **kwargs
    ) -> Optional[Any]:
        """
        Make HTTP request with comprehensive error handling
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            url: Full URL to request
            show_error: Whether to show error messages in Streamlit
            **kwargs: Additional arguments to pass to requests
        
        Returns:
            Response JSON/data or None if error
        """
        try:
            response = requests.request(
                method,
                url,
                timeout=self.timeout,
                **kwargs
            )
            
            response.raise_for_status()
            
            # Return JSON if available
            try:
                return response.json()
            except:
                return response.text
        
        except requests.exceptions.Timeout:
            if show_error:
                st.error("⏱️ Request timed out. Please try again.")
            logger.error(f"Timeout: {method} {url}")
            return None
        
        except requests.exceptions.ConnectionError:
            if show_error:
                st.error("🔴 Cannot connect to API. Ensure backend is running at " + self.base_url)
            logger.error(f"Connection error: {method} {url}")
            return None
        
        except requests.exceptions.HTTPError as e:
            if show_error:
                st.error(f"❌ API Error: {e}")
            logger.error(f"HTTP error: {method} {url} - {e}")
            return None
        
        except Exception as e:
            if show_error:
                st.error(f"⚠️ Unexpected error: {e}")
            logger.error(f"Unexpected error: {method} {url} - {e}")
            return None
    
    # ==========================================
    # SCHEME SEARCH & DETAILS
    # ==========================================
    
    def search_schemes(self, query: str, limit: int = 20) -> Optional[Dict]:
        """
        Search mutual fund schemes by name, AMC, or code
        
        Args:
            query: Search query string
            limit: Maximum number of results
        
        Returns:
            Dictionary with 'total_results' and 'schemes' list
        """
        return self._make_request(
            "GET",
            f"{self.api_v1}/schemes/search",
            params={"query": query, "limit": limit}
        )
    
    def get_scheme_details(self, scheme_code: str) -> Optional[Dict]:
        """
        Get detailed information for a specific scheme
        
        Args:
            scheme_code: Unique scheme code
        
        Returns:
            Scheme details dictionary
        """
        return self._make_request(
            "GET",
            f"{self.api_v1}/schemes/{scheme_code}"
        )
    
    def get_all_schemes(self) -> Optional[List[Dict]]:
        """Get list of all available schemes"""
        return self._make_request(
            "GET",
            f"{self.api_v1}/nav",
            show_error=False
        )
    
    # ==========================================
    # HISTORICAL DATA
    # ==========================================
    
    def get_historical_data(self, scheme_code: str, days: int = 365) -> Optional[Dict]:
        """
        Get historical NAV data for a scheme
        
        Args:
            scheme_code: Scheme code
            days: Number of days of historical data
        
        Returns:
            Historical NAV data
        """
        return self._make_request(
            "GET",
            f"{self.api_v1}/schemes/{scheme_code}/history",
            params={"days": days}
        )
    
    # ==========================================
    # ANALYTICS & METRICS
    # ==========================================
    
    def get_cagr(self, scheme_code: str, years: int = 3) -> Optional[Dict]:
        """Get CAGR for a scheme"""
        return self._make_request(
            "GET",
            f"{self.api_v1}/analytics/cagr/{scheme_code}",
            params={"years": years}
        )
    
    def get_risk_metrics(self, scheme_code: str) -> Optional[Dict]:
        """Get risk metrics for a scheme"""
        return self._make_request(
            "GET",
            f"{self.api_v1}/analytics/risk/{scheme_code}"
        )
    
    def get_comprehensive_metrics(self, scheme_code: str) -> Optional[Dict]:
        """Get comprehensive financial and risk metrics"""
        return self._make_request(
            "GET",
            f"{self.api_v1}/analytics/comprehensive/{scheme_code}"
        )
    
    # ==========================================
    # COMPARISON
    # ==========================================
    
    def compare_schemes(self, scheme_codes: List[str]) -> Optional[Dict]:
        """
        Compare multiple schemes side-by-side
        
        Args:
            scheme_codes: List of scheme codes to compare
        
        Returns:
            Comparison data with metrics for all schemes
        """
        # Try POST with JSON body first
        result = self._make_request(
            "POST",
            f"{self.api_v1}/analytics/compare",
            json=scheme_codes,
            show_error=False
        )
        
        # Fallback to GET with query params
        if result is None:
            result = self._make_request(
                "GET",
                f"{self.api_v1}/analytics/compare",
                params={"scheme_codes": scheme_codes}
            )
        
        return result
    
    # ==========================================
    # PORTFOLIO MANAGEMENT
    # ==========================================
    
    def analyze_portfolio(self, portfolio_data: Dict) -> Optional[Dict]:
        """
        Analyze a portfolio of schemes
        
        Args:
            portfolio_data: Dictionary with portfolio details
        
        Returns:
            Portfolio analysis metrics
        """
        return self._make_request(
            "POST",
            f"{self.api_v1}/portfolio/analyze",
            json=portfolio_data
        )
    
    def save_portfolio(self, portfolio_data: Dict) -> Dict:
        """
        Save portfolio to backend
        
        Args:
            portfolio_data: Portfolio data to save
        
        Returns:
            Response with portfolio_id if successful
        """
        result = self._make_request(
            "POST",
            f"{self.api_v1}/portfolio/save",
            json=portfolio_data
        )
        
        if result is None:
            return {"success": False, "error": "Request failed"}
        
        return result
    
    def get_saved_portfolios(self) -> List[Dict]:
        """
        Get list of all saved portfolios
        
        Returns:
            List of portfolio summaries
        """
        result = self._make_request(
            "GET",
            f"{self.api_v1}/portfolio",
            show_error=False
        )
        
        # Handle both response formats
        if isinstance(result, list):
            return result
        elif isinstance(result, dict) and 'portfolios' in result:
            return result['portfolios']
        else:
            return []
    
    def get_portfolio(self, portfolio_id: str) -> Dict:
        """
        Get specific portfolio details
        
        Args:
            portfolio_id: Portfolio UUID
        
        Returns:
            Portfolio details
        """
        result = self._make_request(
            "GET",
            f"{self.api_v1}/portfolio/{portfolio_id}"
        )
        
        return result if result else {}
    
    def delete_portfolio(self, portfolio_id: str) -> Dict:
        """
        Delete a portfolio
        
        Args:
            portfolio_id: Portfolio UUID
        
        Returns:
            Deletion status
        """
        result = self._make_request(
            "DELETE",
            f"{self.api_v1}/portfolio/{portfolio_id}"
        )
        
        return result if result else {"success": False, "error": "Request failed"}
    
    # ==========================================
    # NAV PREDICTIONS
    # ==========================================
    
    def predict_nav(self, scheme_code: str, forecast_days: int = 30) -> Optional[Dict]:
        """
        Predict future NAV for a scheme
        
        Args:
            scheme_code: Scheme code
            forecast_days: Number of days to forecast
        
        Returns:
            Prediction data
        """
        return self._make_request(
            "POST",
            f"{self.api_v1}/predict/single",
            json={
                "scheme_code": scheme_code,
                "forecast_days": forecast_days
            }
        )
    
    def predict_sequence(self, scheme_code: str, days: int = 7) -> Optional[Dict]:
        """
        Get sequential NAV predictions for multiple days
        
        Args:
            scheme_code: Scheme code
            days: Number of days to predict (1-30)
        
        Returns:
            Sequential predictions
        """
        return self._make_request(
            "GET",
            f"{self.api_v1}/predict/sequence/{scheme_code}",
            params={"days": days}
        )
    
    # ==========================================
    # NEWS & MARKET DATA
    # ==========================================
    
    def get_market_news(self, topic: str = "equity mutual funds", limit: int = 20) -> Optional[Dict]:
        """
        Get latest market news
        
        Args:
            topic: News topic
            limit: Number of articles
        
        Returns:
            News articles
        """
        return self._make_request(
            "GET",
            f"{self.api_v1}/news/market",
            params={"topic": topic, "limit": limit}
        )
    
    def analyze_market_news(self, query: str) -> Optional[Dict]:
        """Get AI-analyzed market news"""
        return self._make_request(
            "POST",
            f"{self.api_v1}/news/analyze",
            params={"query": query}
        )
    
    def get_news_sources(self) -> Optional[Dict]:
        """Get list of configured news sources"""
        return self._make_request(
            "GET",
            f"{self.api_v1}/news/sources"
        )
    
    # ==========================================
    # AUM DATA
    # ==========================================
    
    def get_aum_data(self, scheme_code: Optional[str] = None) -> Optional[Dict]:
        """
        Get AUM (Assets Under Management) data
        
        Args:
            scheme_code: Optional specific scheme code
        
        Returns:
            AUM data
        """
        params = {}
        if scheme_code:
            params['scheme_code'] = scheme_code
        
        return self._make_request(
            "GET",
            f"{self.api_v1}/aum",
            params=params
        )
    
    # ==========================================
    # HEALTH CHECK
    # ==========================================
    
    def check_api_health(self) -> bool:
        """
        Check if backend API is running and healthy
        
        Returns:
            True if API is healthy, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def get_api_status(self) -> Optional[Dict]:
        """Get detailed API status"""
        return self._make_request(
            "GET",
            f"{self.api_v1}/status",
            show_error=False
        )
    
    # ==========================================
    # BATCH OPERATIONS
    # ==========================================
    
    def batch_get_metrics(self, scheme_codes: List[str]) -> Dict[str, Dict]:
        """
        Get comprehensive metrics for multiple schemes
        
        Args:
            scheme_codes: List of scheme codes
        
        Returns:
            Dictionary mapping scheme codes to their metrics
        """
        results = {}
        
        for code in scheme_codes:
            metrics = self.get_comprehensive_metrics(code)
            if metrics:
                results[code] = metrics
        
        return results
    
    def batch_get_predictions(
        self,
        scheme_codes: List[str],
        forecast_days: int = 30
    ) -> Dict[str, Dict]:
        """
        Get predictions for multiple schemes
        
        Args:
            scheme_codes: List of scheme codes
            forecast_days: Number of days to forecast
        
        Returns:
            Dictionary mapping scheme codes to predictions
        """
        results = {}
        
        for code in scheme_codes:
            prediction = self.predict_nav(code, forecast_days)
            if prediction:
                results[code] = prediction
        
        return results
    
    # ==========================================
    # UTILITY METHODS
    # ==========================================
    
    def test_connection(self) -> bool:
        """
        Test connection to backend
        
        Returns:
            True if connection successful
        """
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_base_url(self) -> str:
        """Get configured base URL"""
        return self.base_url
    
    def set_timeout(self, timeout: int):
        """Set request timeout in seconds"""
        self.timeout = timeout
        logger.info(f"Timeout set to {timeout}s")


# ==========================================
# SINGLETON INSTANCE
# ==========================================

# Create default instance
_default_client = None

def get_api_client(base_url: str = "http://localhost:8000") -> APIClient:
    """
    Get or create API client instance
    
    Args:
        base_url: Base URL for API
    
    Returns:
        APIClient instance
    """
    global _default_client
    
    if _default_client is None:
        _default_client = APIClient(base_url)
    
    return _default_client

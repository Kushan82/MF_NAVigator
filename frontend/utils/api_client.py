"""
API client wrapper for all backend calls
Centralized API communication for the frontend
"""

import requests
from typing import Dict, List, Optional
import streamlit as st


class APIClient:
    """Centralized API client for MF_NAVigator"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize API client
        
        Args:
            base_url: Base URL of the API (default: localhost:8000)
        """
        self.base_url = base_url
        self.api_v1 = f"{base_url}/api/v1"
        self.timeout = 30
    
    def _make_request(
        self,
        method: str,
        url: str,
        show_error: bool = True,
        **kwargs
    ) -> Optional[Dict]:
        """
        Make HTTP request with error handling
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL to request
            show_error: Whether to show error messages in Streamlit
            **kwargs: Additional arguments to pass to requests
        
        Returns:
            Response JSON or None if error
        """
        try:
            response = requests.request(
                method,
                url,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.Timeout:
            if show_error:
                st.error("⏱️ Request timed out. Please try again.")
            return None
        
        except requests.exceptions.ConnectionError:
            if show_error:
                st.error("🔴 Cannot connect to API. Ensure the backend is running.")
            return None
        
        except requests.exceptions.HTTPError as e:
            if show_error:
                st.error(f"❌ API Error: {e}")
            return None
        
        except Exception as e:
            if show_error:
                st.error(f"⚠️ Unexpected error: {e}")
            return None
    
    # ==========================================
    # Scheme Endpoints
    # ==========================================
    
    def search_schemes(
        self,
        query: str,
        limit: int = 10
    ) -> Optional[Dict]:
        """
        Search mutual fund schemes
        
        Args:
            query: Search query (scheme name, AMC, code)
            limit: Maximum results to return
        
        Returns:
            Dictionary with search results or None
        """
        return self._make_request(
            "GET",
            f"{self.api_v1}/schemes/search",
            params={"query": query, "limit": limit}
        )
    
    def get_scheme_details(self, scheme_code: str) -> Optional[Dict]:
        """
        Get details for a specific scheme
        
        Args:
            scheme_code: Scheme code
        
        Returns:
            Scheme details dictionary or None
        """
        return self._make_request(
            "GET",
            f"{self.api_v1}/schemes/{scheme_code}"
        )
    
    # ==========================================
    # Metrics Endpoints
    # ==========================================
    
    def get_financial_metrics(self, scheme_code: str) -> Optional[Dict]:
        """
        Get financial metrics for a scheme
        
        Args:
            scheme_code: Scheme code
        
        Returns:
            Financial metrics dictionary
        """
        return self._make_request(
            "GET",
            f"{self.api_v1}/metrics/financial/{scheme_code}"
        )
    
    def get_risk_metrics(self, scheme_code: str) -> Optional[Dict]:
        """
        Get risk metrics for a scheme
        
        Args:
            scheme_code: Scheme code
        
        Returns:
            Risk metrics dictionary
        """
        return self._make_request(
            "GET",
            f"{self.api_v1}/metrics/risk/{scheme_code}"
        )
    
    def get_comprehensive_metrics(self, scheme_code: str) -> Optional[Dict]:
        """
        Get comprehensive metrics (financial + risk) for a scheme
        
        Args:
            scheme_code: Scheme code
        
        Returns:
            Comprehensive metrics dictionary
        """
        return self._make_request(
            "GET",
            f"{self.api_v1}/metrics/comprehensive/{scheme_code}"
        )
    
    # ==========================================
    # Portfolio Endpoints
    # ==========================================
    
    def analyze_portfolio(self, schemes: List[Dict]) -> Optional[Dict]:
        """
        Analyze a portfolio of schemes
        
        Args:
            schemes: List of dicts with 'scheme_code' and 'weight'
            Example: [
                {"scheme_code": "119551", "weight": 0.4},
                {"scheme_code": "120503", "weight": 0.6}
            ]
        
        Returns:
            Portfolio metrics dictionary
        """
        return self._make_request(
            "POST",
            f"{self.api_v1}/portfolio/analyze",
            json={"schemes": schemes}
        )
    
    def compare_schemes(self, scheme_codes: List[str]) -> Optional[Dict]:
        """
        Compare multiple schemes side by side
        
        Args:
            scheme_codes: List of scheme codes to compare
            Example: ["119551", "120503", "118989"]
        
        Returns:
            Comparison results dictionary
        """
        return self._make_request(
            "POST",
            f"{self.api_v1}/schemes/compare",
            json=scheme_codes
        )
    
    # ==========================================
    # Prediction Endpoints
    # ==========================================
    
    def predict_nav(
        self,
        scheme_code: str,
        forecast_days: int = 30
    ) -> Optional[Dict]:
        """
        Predict future NAV for a scheme
        
        Args:
            scheme_code: Scheme code
            forecast_days: Number of days to forecast (1-90)
        
        Returns:
            Prediction result dictionary
        """
        return self._make_request(
            "POST",
            f"{self.api_v1}/predict/single",
            json={
                "scheme_code": scheme_code,
                "forecast_days": min(max(forecast_days, 1), 90)
            }
        )
    
    def predict_sequence(
        self,
        scheme_code: str,
        days: int = 7
    ) -> Optional[Dict]:
        """
        Get sequential NAV predictions
        
        Args:
            scheme_code: Scheme code
            days: Number of days to predict (1-30)
        
        Returns:
            Sequential predictions dictionary
        """
        return self._make_request(
            "POST",
            f"{self.api_v1}/predict/sequence",
            params={
                "scheme_code": scheme_code,
                "days": min(max(days, 1), 30)
            }
        )
    
    # ==========================================
    # Historical Data Endpoints
    # ==========================================
    
    def get_historical_data(
        self,
        scheme_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 365
    ) -> Optional[Dict]:
        """
        Get historical NAV data for a scheme
        
        Args:
            scheme_code: Scheme code
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Maximum data points (1-2000)
        
        Returns:
            Historical data dictionary
        """
        params = {"limit": min(max(limit, 1), 2000)}
        
        if start_date:
            params["start_date"] = start_date
        
        if end_date:
            params["end_date"] = end_date
        
        return self._make_request(
            "GET",
            f"{self.api_v1}/historical/{scheme_code}",
            params=params
        )
    
    # ==========================================
    # Health Check
    # ==========================================
    
    def check_api_health(self) -> bool:
        """
        Check if API is running and healthy
        
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
    
    # ==========================================
    # Batch Operations
    # ==========================================
    
    def batch_get_metrics(
        self,
        scheme_codes: List[str]
    ) -> Dict[str, Dict]:
        """
        Get metrics for multiple schemes
        
        Args:
            scheme_codes: List of scheme codes
        
        Returns:
            Dictionary with {scheme_code: metrics}
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
            Dictionary with {scheme_code: prediction}
        """
        results = {}
        
        for code in scheme_codes:
            prediction = self.predict_nav(code, forecast_days)
            if prediction:
                results[code] = prediction
        
        return results
    def save_portfolio(self, portfolio_data: dict) -> dict:
        """Save portfolio to backend"""
        try:
            response = requests.post(
                f"{self.base_url}/portfolio/save",
                json=portfolio_data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_saved_portfolios(self) -> list:
        """Get list of saved portfolios"""
        try:
            response = requests.get(
                f"{self.base_url}/portfolio/list",
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get('portfolios', [])
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return []
    
    def get_portfolio(self, portfolio_id: str) -> dict:
        """Get portfolio details"""
        try:
            response = requests.get(
                f"{self.base_url}/portfolio/{portfolio_id}",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return {}
    
    def delete_portfolio(self, portfolio_id: str) -> dict:
        """Delete portfolio"""
        try:
            response = requests.delete(
                f"{self.base_url}/portfolio/{portfolio_id}",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return {"success": False, "error": str(e)}
"""
Test script for MF_NAVigator API
Tests all REST API endpoints
"""

import requests
import json
from typing import Dict

# API base URL
BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"


def print_response(title: str, response):
    """Pretty print API response"""
    print(f"\n{'='*70}")
    print(f"📋 {title}")
    print(f"{'='*70}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
        print("✅ SUCCESS")
    else:
        print(f"❌ FAILED: {response.text}")


def main():
    print("\n" + "="*70)
    print("🚀 MF_NAVigator API Test Suite")
    print("="*70)
    print("\n⚠️  Make sure the API server is running:")
    print("   $ python backend/main.py")
    print("\n")
    
    # Test 1: Health Check
    print("\n📌 Test 1: Health Check")
    response = requests.get(f"{BASE_URL}/health")
    print_response("Health Check", response)
    
    # Test 2: Search Schemes
    print("\n📌 Test 2: Search Schemes")
    response = requests.get(f"{API_V1}/schemes/search?query=HDFC&limit=5")
    print_response("Search HDFC Schemes", response)
    
    # Get a scheme code for further tests
    scheme_code = "119551"  # HDFC Top 100
    
    # Test 3: Get Scheme Details
    print(f"\n📌 Test 3: Get Scheme Details (Code: {scheme_code})")
    response = requests.get(f"{API_V1}/schemes/{scheme_code}")
    print_response("Scheme Details", response)
    
    # Test 4: Financial Metrics
    print(f"\n📌 Test 4: Financial Metrics")
    response = requests.get(f"{API_V1}/metrics/financial/{scheme_code}")
    print_response("Financial Metrics", response)
    
    # Test 5: Risk Metrics
    print(f"\n📌 Test 5: Risk Metrics")
    response = requests.get(f"{API_V1}/metrics/risk/{scheme_code}")
    print_response("Risk Metrics", response)
    
    # Test 6: Comprehensive Metrics
    print(f"\n📌 Test 6: Comprehensive Metrics")
    response = requests.get(f"{API_V1}/metrics/comprehensive/{scheme_code}")
    print_response("Comprehensive Metrics", response)
    
    # Test 7: Portfolio Analysis
    print(f"\n📌 Test 7: Portfolio Analysis")
    portfolio_data = {
        "schemes": [
            {"scheme_code": "119551", "weight": 0.4},
            {"scheme_code": "120503", "weight": 0.3},
            {"scheme_code": "118989", "weight": 0.3}
        ]
    }
    response = requests.post(f"{API_V1}/portfolio/analyze", json=portfolio_data)
    print_response("Portfolio Analysis", response)
    
    # Test 8: Compare Schemes
    print(f"\n📌 Test 8: Compare Schemes")
    schemes_to_compare = ["119551", "120503", "118989"]
    response = requests.post(f"{API_V1}/portfolio/compare", json=schemes_to_compare)
    print_response("Scheme Comparison", response)
    
    # Test 9: NAV Prediction
    print(f"\n📌 Test 9: NAV Prediction")
    prediction_data = {
        "scheme_code": scheme_code,
        "forecast_days": 30
    }
    response = requests.post(f"{API_V1}/predict/single", json=prediction_data)
    print_response("NAV Prediction", response)
    
    # Test 10: Sequential Predictions
    print(f"\n📌 Test 10: Sequential Predictions")
    response = requests.post(f"{API_V1}/predict/sequence?scheme_code={scheme_code}&days=7")
    print_response("Sequential Predictions", response)
    
    # Test 11: Historical Data
    print(f"\n📌 Test 11: Historical Data")
    response = requests.get(f"{API_V1}/historical/{scheme_code}?limit=10")
    print_response("Historical Data", response)
    
    # Summary
    print("\n" + "="*70)
    print("✅ All API Tests Complete!")
    print("="*70)
    print("\n🎯 API Endpoints Tested:")
    print("   ✓ Health check")
    print("   ✓ Scheme search")
    print("   ✓ Scheme details")
    print("   ✓ Financial metrics")
    print("   ✓ Risk metrics")
    print("   ✓ Comprehensive metrics")
    print("   ✓ Portfolio analysis")
    print("   ✓ Scheme comparison")
    print("   ✓ NAV prediction")
    print("   ✓ Sequential predictions")
    print("   ✓ Historical data")
    print("\n📚 API Documentation: http://localhost:8000/docs")
    print("\n")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API server")
        print("   Please start the server first:")
        print("   $ python backend/main.py")
        print("\n")

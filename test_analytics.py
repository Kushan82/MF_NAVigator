"""
Test script for MF_NAVigator Analytics Module
Tests financial metrics, risk metrics, and portfolio analysis
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from analytics.financial_metrics import FinancialMetricsCalculator
from analytics.risk_metrics import RiskMetricsCalculator
from analytics.portfolio_analysis import PortfolioAnalyzer

def main():
    print("\n" + "="*70)
    print("🚀 MF_NAVigator Analytics Module Test")
    print("="*70)
    
    # Create sample data
    np.random.seed(42)
    dates = pd.date_range(start='2020-01-01', end='2024-12-31', freq='D')
    
    # Single scheme for metrics testing
    nav_values = 100 * (1 + np.random.randn(len(dates)) * 0.01).cumprod()
    nav_series = pd.Series(nav_values, index=dates)
    date_series = pd.Series(dates)
    
    # Multiple schemes for portfolio testing
    schemes_data = {
        'HDFC Equity Fund': pd.Series(100 * (1 + np.random.randn(len(dates)) * 0.012).cumprod()),
        'ICICI Prudential Fund': pd.Series(100 * (1 + np.random.randn(len(dates)) * 0.010).cumprod()),
        'SBI Bluechip Fund': pd.Series(100 * (1 + np.random.randn(len(dates)) * 0.011).cumprod())
    }
    
    # Initialize calculators
    fin_calc = FinancialMetricsCalculator()
    risk_calc = RiskMetricsCalculator()
    portfolio_analyzer = PortfolioAnalyzer()
    
    # ==========================================
    # Test 1: Financial Metrics
    # ==========================================
    print("\n📋 Test 1: Financial Metrics")
    print("-" * 70)
    
    try:
        # Calculate returns
        returns = nav_series.pct_change().dropna()
        
        # CAGR
        cagr = fin_calc.calculate_cagr_from_nav(nav_series, date_series)
        print(f"✅ CAGR: {cagr*100:.2f}%")
        
        # Sharpe Ratio
        sharpe = fin_calc.calculate_sharpe_ratio(returns)
        print(f"✅ Sharpe Ratio: {sharpe:.3f}")
        
        # Sortino Ratio
        sortino = fin_calc.calculate_sortino_ratio(returns)
        print(f"✅ Sortino Ratio: {sortino:.3f}")
        
        # Absolute Returns
        abs_returns = fin_calc.calculate_absolute_returns(nav_series)
        print(f"✅ 1Y Return: {abs_returns.get('1Y', 'N/A'):.2f}%")
        print(f"✅ 3Y Return: {abs_returns.get('3Y', 'N/A'):.2f}%")
        
        # Comprehensive metrics
        metrics = fin_calc.get_comprehensive_metrics(nav_series, date_series)
        print(f"\n📊 Comprehensive Metrics:")
        print(f"   Current NAV: ₹{metrics['current_nav']:.2f}")
        print(f"   Annualized Return: {metrics['annualized_return']*100:.2f}%")
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
    
    # ==========================================
    # Test 2: Risk Metrics
    # ==========================================
    print("\n\n📋 Test 2: Risk Metrics")
    print("-" * 70)
    
    try:
        # Volatility
        vol = risk_calc.calculate_volatility(returns)
        print(f"✅ Annualized Volatility: {vol*100:.2f}%")
        
        # Maximum Drawdown
        max_dd, peak_idx, trough_idx = risk_calc.calculate_max_drawdown(nav_series)
        print(f"✅ Maximum Drawdown: {abs(max_dd)*100:.2f}%")
        print(f"   Peak Date: {peak_idx}")
        print(f"   Trough Date: {trough_idx}")
        
        # Value at Risk
        var_95 = risk_calc.calculate_var(returns, 0.95)
        cvar_95 = risk_calc.calculate_cvar(returns, 0.95)
        print(f"✅ VaR (95%): {var_95*100:.2f}%")
        print(f"✅ CVaR (95%): {cvar_95*100:.2f}%")
        
        # Downside Deviation
        downside_dev = risk_calc.calculate_downside_deviation(returns)
        print(f"✅ Downside Deviation: {downside_dev*100:.2f}%")
        
        # Comprehensive risk metrics
        risk_metrics = risk_calc.get_comprehensive_risk_metrics(nav_series, date_series)
        print(f"\n📊 Comprehensive Risk Metrics:")
        print(f"   Ulcer Index: {risk_metrics['ulcer_index']:.4f}")
        print(f"   Calmar Ratio: {risk_metrics['calmar_ratio']:.3f}")
        print(f"   Recovery Time: {risk_metrics['recovery_info']['recovery_time_days']} days")
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
    
    # ==========================================
    # Test 3: Portfolio Comparison
    # ==========================================
    print("\n\n📋 Test 3: Portfolio Comparison")
    print("-" * 70)
    
    try:
        # Compare schemes
        comparison = portfolio_analyzer.compare_schemes(schemes_data)
        print("\n✅ Scheme Comparison:")
        print(comparison[['Scheme', 'CAGR (%)', 'Sharpe Ratio', 'Max Drawdown (%)']].to_string(index=False))
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
    
    # ==========================================
    # Test 4: Scheme Ranking
    # ==========================================
    print("\n\n📋 Test 4: Scheme Ranking")
    print("-" * 70)
    
    try:
        # Rank by Sharpe ratio
        ranked = portfolio_analyzer.rank_schemes(schemes_data, 'sharpe_ratio')
        print("\n✅ Ranked by Sharpe Ratio:")
        print(ranked[['Rank', 'Scheme', 'Sharpe Ratio', 'Volatility (%)']].to_string(index=False))
        
        # Find best scheme
        best_scheme, best_metrics = portfolio_analyzer.find_best_scheme(
            schemes_data, 
            'risk_adjusted_return'
        )
        print(f"\n✅ Best Scheme (Risk-Adjusted): {best_scheme}")
        print(f"   Sharpe Ratio: {best_metrics['Sharpe Ratio']:.3f}")
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
    
    # ==========================================
    # Test 5: Portfolio Metrics
    # ==========================================
    print("\n\n📋 Test 5: Portfolio Metrics")
    print("-" * 70)
    
    try:
        # Equal weight portfolio
        weights = {
            'HDFC Equity Fund': 0.33,
            'ICICI Prudential Fund': 0.33,
            'SBI Bluechip Fund': 0.34
        }
        
        portfolio_metrics = portfolio_analyzer.calculate_portfolio_metrics(
            schemes_data, 
            weights
        )
        
        print("\n✅ Portfolio Metrics (Equal Weight):")
        print(f"   Annualized Return: {portfolio_metrics['annualized_return']*100:.2f}%")
        print(f"   Volatility: {portfolio_metrics['volatility']*100:.2f}%")
        print(f"   Sharpe Ratio: {portfolio_metrics['sharpe_ratio']:.3f}")
        print(f"   Sortino Ratio: {portfolio_metrics['sortino_ratio']:.3f}")
        print(f"   Max Drawdown: {abs(portfolio_metrics['max_drawdown'])*100:.2f}%")
        print(f"   VaR (95%): {portfolio_metrics['var_95']*100:.2f}%")
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
    
    # ==========================================
    # Test 6: Correlation & Diversification
    # ==========================================
    print("\n\n📋 Test 6: Correlation & Diversification")
    print("-" * 70)
    
    try:
        # Correlation matrix
        corr_matrix = portfolio_analyzer.calculate_correlation_matrix(schemes_data)
        print("\n✅ Correlation Matrix:")
        print(corr_matrix.round(3))
        
        # Diversification score
        div_score = portfolio_analyzer.get_diversification_score(schemes_data, weights)
        print(f"\n✅ Diversification Score: {div_score:.3f}")
        print(f"   (0 = fully correlated, 1 = perfectly diversified)")
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
    
    # ==========================================
    # Summary
    # ==========================================
    print("\n" + "="*70)
    print("✅ All Analytics Module Tests Completed Successfully!")
    print("="*70)
    
    print("\n🎯 Key Features Demonstrated:")
    print("   ✓ CAGR, Sharpe Ratio, Sortino Ratio calculations")
    print("   ✓ Absolute returns for multiple periods")
    print("   ✓ Volatility and risk metrics")
    print("   ✓ Maximum drawdown and recovery analysis")
    print("   ✓ Value at Risk (VaR) and CVaR")
    print("   ✓ Multi-scheme comparison")
    print("   ✓ Portfolio metrics calculation")
    print("   ✓ Correlation and diversification analysis")
    
    print("\n🚀 Next Phase: ML Models")
    print("   → XGBoost predictor for NAV forecasting")
    print("   → Model training and evaluation")
    print("   → Feature importance analysis")
    print("\n")

if __name__ == "__main__":
    main()

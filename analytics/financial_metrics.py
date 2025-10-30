import pandas as pd
import numpy as np
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from backend.config import settings


class FinancialMetricsCalculator:
    
    def __init__(self, risk_free_rate: float = None):
        self.risk_free_rate = risk_free_rate or settings.RISK_FREE_RATE
        self.trading_days = settings.TRADING_DAYS_PER_YEAR
    
    def calculate_returns(
        self, 
        nav_series: pd.Series,
        period: str = 'daily'
    ) -> pd.Series:
        if period == 'daily':
            return nav_series.pct_change()
        elif period == 'weekly':
            return nav_series.pct_change(periods=5)
        elif period == 'monthly':
            return nav_series.pct_change(periods=21)
        elif period == 'yearly':
            return nav_series.pct_change(periods=252)
        else:
            raise ValueError(f"Invalid period: {period}")
    
    def calculate_cagr(
        self, 
        start_value: float, 
        end_value: float, 
        num_years: float
    ) -> float:
        if start_value <= 0 or num_years <= 0:
            return np.nan
        
        cagr = (end_value / start_value) ** (1 / num_years) - 1
        return cagr
    
    def calculate_cagr_from_nav(
        self, 
        nav_series: pd.Series,
        date_series: pd.Series = None
    ) -> float:
        if len(nav_series) < 2:
            return np.nan
        
        start_value = nav_series.iloc[0]
        end_value = nav_series.iloc[-1]
        
        # Calculate number of years
        if date_series is not None and len(date_series) == len(nav_series):
            num_days = (date_series.iloc[-1] - date_series.iloc[0]).days
            num_years = num_days / 365.25
        else:
            # Assume daily data
            num_years = len(nav_series) / self.trading_days
        
        return self.calculate_cagr(start_value, end_value, num_years)
    
    def calculate_absolute_returns(
        self,
        nav_series: pd.Series,
        periods: Dict[str, int] = None
    ) -> Dict[str, float]:
        if periods is None:
            periods = {
                '1D': 1,
                '1W': 7,
                '1M': 30,
                '3M': 90,
                '6M': 180,
                '1Y': 252,
                '3Y': 756,
                '5Y': 1260
            }
        
        returns = {}
        current_nav = nav_series.iloc[-1]
        
        for name, days in periods.items():
            if len(nav_series) > days:
                past_nav = nav_series.iloc[-days-1]
                ret = ((current_nav - past_nav) / past_nav) * 100
                returns[name] = round(ret, 2)
            else:
                returns[name] = np.nan
        
        return returns
    
    def calculate_sharpe_ratio(
        self,
        returns: pd.Series,
        risk_free_rate: float = None,
        periods_per_year: int = None
    ) -> float:
        
        if len(returns) < 2:
            return np.nan
        
        rf_rate = risk_free_rate or self.risk_free_rate
        periods = periods_per_year or self.trading_days
        
        # Annualize returns and volatility
        mean_return = returns.mean() * periods
        std_return = returns.std() * np.sqrt(periods)
        
        if std_return == 0:
            return np.nan
        
        sharpe = (mean_return - rf_rate) / std_return
        return sharpe
    
    def calculate_sortino_ratio(
        self,
        returns: pd.Series,
        risk_free_rate: float = None,
        periods_per_year: int = None
    ) -> float:
       
        if len(returns) < 2:
            return np.nan
        
        rf_rate = risk_free_rate or self.risk_free_rate
        periods = periods_per_year or self.trading_days
        
        # Calculate downside deviation (only negative returns)
        downside_returns = returns[returns < 0]
        
        if len(downside_returns) == 0:
            return np.nan
        
        mean_return = returns.mean() * periods
        downside_std = downside_returns.std() * np.sqrt(periods)
        
        if downside_std == 0:
            return np.nan
        
        sortino = (mean_return - rf_rate) / downside_std
        return sortino
    
    def calculate_information_ratio(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> float:
       
        if len(returns) != len(benchmark_returns) or len(returns) < 2:
            return np.nan
        
        excess_returns = returns - benchmark_returns
        mean_excess = excess_returns.mean() * self.trading_days
        tracking_error = excess_returns.std() * np.sqrt(self.trading_days)
        
        if tracking_error == 0:
            return np.nan
        
        return mean_excess / tracking_error
    
    def calculate_alpha_beta(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> Tuple[float, float]:
       
        if len(returns) != len(benchmark_returns) or len(returns) < 2:
            return np.nan, np.nan
        
        # Calculate beta
        covariance = np.cov(returns, benchmark_returns)[0][1]
        benchmark_variance = np.var(benchmark_returns)
        
        if benchmark_variance == 0:
            return np.nan, np.nan
        
        beta = covariance / benchmark_variance
        
        # Calculate alpha (annualized)
        alpha = (returns.mean() - beta * benchmark_returns.mean()) * self.trading_days
        
        return alpha, beta
    
    def calculate_treynor_ratio(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series,
        risk_free_rate: float = None
    ) -> float:
        
        rf_rate = risk_free_rate or self.risk_free_rate
        
        alpha, beta = self.calculate_alpha_beta(returns, benchmark_returns)
        
        if np.isnan(beta) or beta == 0:
            return np.nan
        
        mean_return = returns.mean() * self.trading_days
        treynor = (mean_return - rf_rate) / beta
        
        return treynor
    
    def calculate_calmar_ratio(
        self,
        returns: pd.Series,
        max_drawdown: float
    ) -> float:
       
        if max_drawdown == 0 or np.isnan(max_drawdown):
            return np.nan
        
        annualized_return = returns.mean() * self.trading_days
        calmar = annualized_return / abs(max_drawdown)
        
        return calmar
    
    def get_comprehensive_metrics(
        self,
        nav_series: pd.Series,
        date_series: pd.Series = None,
        benchmark_returns: pd.Series = None
    ) -> Dict:
        
        # Calculate returns
        returns = self.calculate_returns(nav_series, 'daily')
        
        # Basic metrics
        metrics = {
            'current_nav': float(nav_series.iloc[-1]),
            'cagr': self.calculate_cagr_from_nav(nav_series, date_series),
            'annualized_return': float(returns.mean() * self.trading_days),
            'sharpe_ratio': self.calculate_sharpe_ratio(returns),
            'sortino_ratio': self.calculate_sortino_ratio(returns),
        }
        
        # Absolute returns
        abs_returns = self.calculate_absolute_returns(nav_series)
        metrics['absolute_returns'] = abs_returns
        
        # Alpha/Beta if benchmark provided
        if benchmark_returns is not None and len(benchmark_returns) == len(returns):
            alpha, beta = self.calculate_alpha_beta(returns.dropna(), benchmark_returns.dropna())
            metrics['alpha'] = alpha
            metrics['beta'] = beta
            metrics['treynor_ratio'] = self.calculate_treynor_ratio(
                returns.dropna(), 
                benchmark_returns.dropna()
            )
            metrics['information_ratio'] = self.calculate_information_ratio(
                returns.dropna(), 
                benchmark_returns.dropna()
            )
        
        return metrics

def calculate_scheme_metrics(nav_series: pd.Series, date_series: pd.Series = None) -> Dict:
    calculator = FinancialMetricsCalculator()
    return calculator.get_comprehensive_metrics(nav_series, date_series)


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧪 Testing Financial Metrics Calculator")
    print("="*70 + "\n")
    
    np.random.seed(42)
    dates = pd.date_range(start='2020-01-01', end='2024-12-31', freq='D')
    nav_values = 100 * (1 + np.random.randn(len(dates)).cumsum() * 0.001)
    nav_series = pd.Series(nav_values, index=dates)
    date_series = pd.Series(dates)
    
    calculator = FinancialMetricsCalculator()
    
    # Test 1: CAGR
    print("📌 Test 1: CAGR Calculation")
    cagr = calculator.calculate_cagr_from_nav(nav_series, date_series)
    print(f"CAGR: {cagr*100:.2f}%")
    
    # Test 2: Sharpe Ratio
    print("\n📌 Test 2: Sharpe Ratio")
    returns = calculator.calculate_returns(nav_series)
    sharpe = calculator.calculate_sharpe_ratio(returns)
    print(f"Sharpe Ratio: {sharpe:.3f}")
    
    # Test 3: Absolute Returns
    print("\n📌 Test 3: Absolute Returns")
    abs_returns = calculator.calculate_absolute_returns(nav_series)
    for period, ret in abs_returns.items():
        if not np.isnan(ret):
            print(f"{period}: {ret:.2f}%")
    
    
    print("\n📌 Test 4: Comprehensive Metrics")
    metrics = calculator.get_comprehensive_metrics(nav_series, date_series)
    print(f"\nCurrent NAV: ₹{metrics['current_nav']:.2f}")
    print(f"CAGR: {metrics['cagr']*100:.2f}%")
    print(f"Annualized Return: {metrics['annualized_return']*100:.2f}%")
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
    print(f"Sortino Ratio: {metrics['sortino_ratio']:.3f}")
    
    print("\n" + "="*70)
    print("✅ Financial metrics calculator working successfully!")
    print("="*70)

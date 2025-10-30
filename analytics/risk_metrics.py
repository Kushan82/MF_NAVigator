import pandas as pd
import numpy as np
from typing import Dict, Tuple
from scipy import stats

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from backend.config import settings


class RiskMetricsCalculator:
    
    def __init__(self):
        self.trading_days = settings.TRADING_DAYS_PER_YEAR
    
    def calculate_volatility(
        self,
        returns: pd.Series,
        periods_per_year: int = None,
        annualize: bool = True
    ) -> float:
        
        if len(returns) < 2:
            return np.nan
        
        vol = returns.std()
        
        if annualize:
            periods = periods_per_year or self.trading_days
            vol = vol * np.sqrt(periods)
        
        return vol
    
    def calculate_downside_deviation(
        self,
        returns: pd.Series,
        target_return: float = 0.0,
        annualize: bool = True
    ) -> float:
        
        downside_returns = returns[returns < target_return]
        
        if len(downside_returns) == 0:
            return 0.0
        
        downside_dev = downside_returns.std()
        
        if annualize:
            downside_dev = downside_dev * np.sqrt(self.trading_days)
        
        return downside_dev
    
    def calculate_max_drawdown(
        self,
        nav_series: pd.Series
    ) -> Tuple[float, int, int]:
        
        if len(nav_series) < 2:
            return np.nan, None, None
        
        # Calculate cumulative returns
        cumulative = nav_series / nav_series.iloc[0]
        
        # Calculate running maximum
        running_max = cumulative.expanding().max()
        
        # Calculate drawdown
        drawdown = (cumulative - running_max) / running_max
        
        # Find maximum drawdown
        max_dd = drawdown.min()
        
        # Find peak and trough indices
        trough_idx = drawdown.idxmin()
        peak_idx = cumulative[:trough_idx].idxmax()
        
        return max_dd, peak_idx, trough_idx
    
    def calculate_drawdown_series(
        self,
        nav_series: pd.Series
    ) -> pd.Series:
        
        cumulative = nav_series / nav_series.iloc[0]
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        
        return drawdown
    
    def calculate_calmar_ratio(
        self,
        nav_series: pd.Series,
        date_series: pd.Series = None
    ) -> float:
        
        # Calculate CAGR
        if date_series is not None:
            num_days = (date_series.iloc[-1] - date_series.iloc[0]).days
            num_years = num_days / 365.25
        else:
            num_years = len(nav_series) / self.trading_days
        
        if num_years <= 0:
            return np.nan
        
        start_val = nav_series.iloc[0]
        end_val = nav_series.iloc[-1]
        cagr = (end_val / start_val) ** (1 / num_years) - 1
        
        # Calculate max drawdown
        max_dd, _, _ = self.calculate_max_drawdown(nav_series)
        
        if max_dd == 0 or np.isnan(max_dd):
            return np.nan
        
        return cagr / abs(max_dd)
    
    def calculate_var(
        self,
        returns: pd.Series,
        confidence_level: float = 0.95,
        method: str = 'historical'
    ) -> float:
        
        if len(returns) < 2:
            return np.nan
        
        if method == 'historical':
            # Historical VaR
            var = np.percentile(returns, (1 - confidence_level) * 100)
        elif method == 'parametric':
            # Parametric VaR (assumes normal distribution)
            mean = returns.mean()
            std = returns.std()
            var = mean - stats.norm.ppf(confidence_level) * std
        else:
            raise ValueError(f"Invalid method: {method}")
        
        return var
    
    def calculate_cvar(
        self,
        returns: pd.Series,
        confidence_level: float = 0.95
    ) -> float:
        
        if len(returns) < 2:
            return np.nan
        
        var = self.calculate_var(returns, confidence_level, 'historical')
        
        # Calculate mean of returns worse than VaR
        cvar = returns[returns <= var].mean()
        
        return cvar
    
    def calculate_ulcer_index(
        self,
        nav_series: pd.Series
    ) -> float:
        
        drawdowns = self.calculate_drawdown_series(nav_series)
        
        # Square the drawdowns and take mean
        squared_dd = drawdowns ** 2
        ulcer = np.sqrt(squared_dd.mean())
        
        return ulcer
    
    def calculate_recovery_time(
        self,
        nav_series: pd.Series
    ) -> Dict:
        
        max_dd, peak_idx, trough_idx = self.calculate_max_drawdown(nav_series)
        
        if peak_idx is None or trough_idx is None:
            return {
                'max_drawdown': max_dd,
                'recovery_time_days': np.nan,
                'recovered': False
            }
        
        # Check if recovered
        peak_value = nav_series.loc[peak_idx]
        post_trough = nav_series.loc[trough_idx:]
        
        recovered_indices = post_trough[post_trough >= peak_value].index
        
        if len(recovered_indices) > 0:
            recovery_idx = recovered_indices[0]
            recovery_time = (recovery_idx - trough_idx).days if hasattr(recovery_idx - trough_idx, 'days') else len(nav_series.loc[trough_idx:recovery_idx])
            recovered = True
        else:
            recovery_time = np.nan
            recovered = False
        
        return {
            'max_drawdown': max_dd,
            'peak_date': peak_idx,
            'trough_date': trough_idx,
            'recovery_time_days': recovery_time,
            'recovered': recovered
        }
    
    def calculate_tracking_error(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series,
        annualize: bool = True
    ) -> float:
        
        if len(returns) != len(benchmark_returns) or len(returns) < 2:
            return np.nan
        
        excess_returns = returns - benchmark_returns
        te = excess_returns.std()
        
        if annualize:
            te = te * np.sqrt(self.trading_days)
        
        return te
    
    def get_comprehensive_risk_metrics(
        self,
        nav_series: pd.Series,
        date_series: pd.Series = None,
        benchmark_returns: pd.Series = None
    ) -> Dict:
        
        # Calculate returns
        returns = nav_series.pct_change().dropna()
        
        # Basic risk metrics
        metrics = {
            'volatility': self.calculate_volatility(returns),
            'downside_deviation': self.calculate_downside_deviation(returns),
            'max_drawdown': self.calculate_max_drawdown(nav_series)[0],
            'ulcer_index': self.calculate_ulcer_index(nav_series),
            'var_95': self.calculate_var(returns, 0.95),
            'cvar_95': self.calculate_cvar(returns, 0.95),
            'var_99': self.calculate_var(returns, 0.99),
            'cvar_99': self.calculate_cvar(returns, 0.99),
            'calmar_ratio': self.calculate_calmar_ratio(nav_series, date_series)
        }
        
        # Recovery information
        recovery_info = self.calculate_recovery_time(nav_series)
        metrics['recovery_info'] = recovery_info
        
        # Tracking error if benchmark provided
        if benchmark_returns is not None and len(benchmark_returns) == len(returns):
            metrics['tracking_error'] = self.calculate_tracking_error(
                returns, 
                benchmark_returns
            )
        
        return metrics


# Convenience function
def calculate_risk_metrics(nav_series: pd.Series, date_series: pd.Series = None) -> Dict:
    calculator = RiskMetricsCalculator()
    return calculator.get_comprehensive_risk_metrics(nav_series, date_series)


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧪 Testing Risk Metrics Calculator")
    print("="*70 + "\n")
    
    # Creating sample data with drawdown
    np.random.seed(42)
    dates = pd.date_range(start='2020-01-01', end='2024-12-31', freq='D')
    returns = np.random.randn(len(dates)) * 0.01
    returns[500:700] = -0.02  # Create a drawdown period
    nav_values = 100 * (1 + pd.Series(returns)).cumprod()
    nav_series = pd.Series(nav_values.values, index=dates)
    date_series = pd.Series(dates)
    
    calculator = RiskMetricsCalculator()
    
    # Test 1: Volatility
    print("📌 Test 1: Volatility")
    returns = nav_series.pct_change().dropna()
    vol = calculator.calculate_volatility(returns)
    print(f"Annualized Volatility: {vol*100:.2f}%")
    
    # Test 2: Maximum Drawdown
    print("\n📌 Test 2: Maximum Drawdown")
    max_dd, peak_idx, trough_idx = calculator.calculate_max_drawdown(nav_series)
    print(f"Max Drawdown: {max_dd*100:.2f}%")
    print(f"Peak Date: {peak_idx}")
    print(f"Trough Date: {trough_idx}")
    
    # Test 3: VaR and CVaR
    print("\n📌 Test 3: Value at Risk")
    var_95 = calculator.calculate_var(returns, 0.95)
    cvar_95 = calculator.calculate_cvar(returns, 0.95)
    print(f"VaR (95%): {var_95*100:.2f}%")
    print(f"CVaR (95%): {cvar_95*100:.2f}%")
    
    # Test 4: Comprehensive Metrics
    print("\n📌 Test 4: Comprehensive Risk Metrics")
    metrics = calculator.get_comprehensive_risk_metrics(nav_series, date_series)
    print(f"\nVolatility: {metrics['volatility']*100:.2f}%")
    print(f"Downside Deviation: {metrics['downside_deviation']*100:.2f}%")
    print(f"Max Drawdown: {metrics['max_drawdown']*100:.2f}%")
    print(f"Ulcer Index: {metrics['ulcer_index']:.4f}")
    print(f"Calmar Ratio: {metrics['calmar_ratio']:.3f}")
    print(f"Recovery Time: {metrics['recovery_info']['recovery_time_days']} days")
    
    print("\n" + "="*70)
    print("✅ Risk metrics calculator working successfully!")
    print("="*70)

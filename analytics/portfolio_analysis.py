import pandas as pd
import numpy as np
from typing import List, Dict, Tuple

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from backend.config import settings
from analytics.financial_metrics import FinancialMetricsCalculator
from analytics.risk_metrics import RiskMetricsCalculator


class PortfolioAnalyzer:
    
    def __init__(self):
        self.fin_calc = FinancialMetricsCalculator()
        self.risk_calc = RiskMetricsCalculator()
        self.trading_days = settings.TRADING_DAYS_PER_YEAR
    
    def compare_schemes(
        self,
        schemes_data: Dict[str, pd.Series],
        date_series: pd.Series = None
    ) -> pd.DataFrame:
        
        comparison = []
        
        for scheme_name, nav_series in schemes_data.items():
            returns = nav_series.pct_change().dropna()
            
            # Calculate metrics
            cagr = self.fin_calc.calculate_cagr_from_nav(nav_series, date_series)
            sharpe = self.fin_calc.calculate_sharpe_ratio(returns)
            sortino = self.fin_calc.calculate_sortino_ratio(returns)
            volatility = self.risk_calc.calculate_volatility(returns)
            max_dd, _, _ = self.risk_calc.calculate_max_drawdown(nav_series)
            
            # Absolute returns
            abs_returns = self.fin_calc.calculate_absolute_returns(nav_series)
            
            comparison.append({
                'Scheme': scheme_name,
                'Current NAV': nav_series.iloc[-1],
                'CAGR (%)': cagr * 100 if not np.isnan(cagr) else np.nan,
                '1Y Return (%)': abs_returns.get('1Y', np.nan),
                '3Y Return (%)': abs_returns.get('3Y', np.nan),
                '5Y Return (%)': abs_returns.get('5Y', np.nan),
                'Volatility (%)': volatility * 100 if not np.isnan(volatility) else np.nan,
                'Max Drawdown (%)': abs(max_dd) * 100 if not np.isnan(max_dd) else np.nan,
                'Sharpe Ratio': sharpe if not np.isnan(sharpe) else np.nan,
                'Sortino Ratio': sortino if not np.isnan(sortino) else np.nan,
            })
        
        df = pd.DataFrame(comparison)
        return df
    
    def calculate_correlation_matrix(
        self,
        schemes_data: Dict[str, pd.Series]
    ) -> pd.DataFrame:
        
        # Calculate returns for all schemes
        returns_dict = {}
        for scheme_name, nav_series in schemes_data.items():
            returns_dict[scheme_name] = nav_series.pct_change().dropna()
        
        # Create DataFrame and calculate correlation
        returns_df = pd.DataFrame(returns_dict)
        corr_matrix = returns_df.corr()
        
        return corr_matrix
    
    def rank_schemes(
        self,
        schemes_data: Dict[str, pd.Series],
        metric: str = 'sharpe_ratio',
        ascending: bool = False
    ) -> pd.DataFrame:
        
        comparison = self.compare_schemes(schemes_data)
        
        metric_map = {
            'sharpe_ratio': 'Sharpe Ratio',
            'cagr': 'CAGR (%)',
            'volatility': 'Volatility (%)',
            'max_drawdown': 'Max Drawdown (%)',
            'sortino_ratio': 'Sortino Ratio'
        }
        
        col_name = metric_map.get(metric, metric)
        
        if col_name in comparison.columns:
            ranked = comparison.sort_values(col_name, ascending=ascending)
            ranked['Rank'] = range(1, len(ranked) + 1)
            return ranked
        else:
            return comparison
    
    def calculate_portfolio_returns(
        self,
        schemes_data: Dict[str, pd.Series],
        weights: Dict[str, float]
    ) -> pd.Series:
        
        # Validate weights
        total_weight = sum(weights.values())
        if not np.isclose(total_weight, 1.0):
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
        
        # Calculate weighted returns
        portfolio_returns = None
        
        for scheme_name, nav_series in schemes_data.items():
            weight = weights.get(scheme_name, 0)
            if weight > 0:
                returns = nav_series.pct_change().dropna()
                
                if portfolio_returns is None:
                    portfolio_returns = returns * weight
                else:
                    # Align indices
                    aligned_returns = returns.reindex(portfolio_returns.index, fill_value=0)
                    portfolio_returns = portfolio_returns + (aligned_returns * weight)
        
        return portfolio_returns
    
    def calculate_portfolio_metrics(
        self,
        schemes_data: Dict[str, pd.Series],
        weights: Dict[str, float],
        benchmark_returns: pd.Series = None
    ) -> Dict:
       
        # Calculate portfolio returns
        portfolio_returns = self.calculate_portfolio_returns(schemes_data, weights)
        
        # Calculate portfolio NAV (assuming starting value of 100)
        portfolio_nav = 100 * (1 + portfolio_returns).cumprod()
        
        # Calculate metrics
        metrics = {
            'annualized_return': portfolio_returns.mean() * self.trading_days,
            'volatility': self.risk_calc.calculate_volatility(portfolio_returns),
            'sharpe_ratio': self.fin_calc.calculate_sharpe_ratio(portfolio_returns),
            'sortino_ratio': self.fin_calc.calculate_sortino_ratio(portfolio_returns),
            'max_drawdown': self.risk_calc.calculate_max_drawdown(portfolio_nav)[0],
            'var_95': self.risk_calc.calculate_var(portfolio_returns, 0.95),
            'cvar_95': self.risk_calc.calculate_cvar(portfolio_returns, 0.95)
        }
        
        # Benchmark comparison if provided
        if benchmark_returns is not None:
            alpha, beta = self.fin_calc.calculate_alpha_beta(
                portfolio_returns, 
                benchmark_returns
            )
            metrics['alpha'] = alpha
            metrics['beta'] = beta
            metrics['tracking_error'] = self.risk_calc.calculate_tracking_error(
                portfolio_returns, 
                benchmark_returns
            )
        
        return metrics
    
    def find_best_scheme(
        self,
        schemes_data: Dict[str, pd.Series],
        criteria: str = 'risk_adjusted_return'
    ) -> Tuple[str, Dict]:
        
        comparison = self.compare_schemes(schemes_data)
        
        if criteria == 'risk_adjusted_return':
            best_idx = comparison['Sharpe Ratio'].idxmax()
        elif criteria == 'return':
            best_idx = comparison['CAGR (%)'].idxmax()
        elif criteria == 'low_risk':
            best_idx = comparison['Volatility (%)'].idxmin()
        elif criteria == 'min_drawdown':
            best_idx = comparison['Max Drawdown (%)'].idxmin()
        else:
            raise ValueError(f"Unknown criteria: {criteria}")
        
        best_scheme = comparison.loc[best_idx, 'Scheme']
        best_metrics = comparison.loc[best_idx].to_dict()
        
        return best_scheme, best_metrics
    
    def efficient_frontier_simple(
        self,
        schemes_data: Dict[str, pd.Series],
        num_portfolios: int = 100
    ) -> pd.DataFrame:
        
        scheme_names = list(schemes_data.keys())
        num_schemes = len(scheme_names)
        
        results = []
        
        for _ in range(num_portfolios):
            # Generate random weights
            weights_arr = np.random.random(num_schemes)
            weights_arr = weights_arr / weights_arr.sum()
            
            weights = dict(zip(scheme_names, weights_arr))
            
            # Calculate portfolio metrics
            try:
                metrics = self.calculate_portfolio_metrics(schemes_data, weights)
                
                results.append({
                    'Return': metrics['annualized_return'],
                    'Volatility': metrics['volatility'],
                    'Sharpe': metrics['sharpe_ratio'],
                    **{f'Weight_{name}': weights[name] for name in scheme_names}
                })
            except:
                continue
        
        return pd.DataFrame(results)
    
    def get_diversification_score(
        self,
        schemes_data: Dict[str, pd.Series],
        weights: Dict[str, float]
    ) -> float:
        
        # Calculate correlation matrix
        corr_matrix = self.calculate_correlation_matrix(schemes_data)
        
        # Calculate average correlation weighted by portfolio weights
        scheme_names = list(weights.keys())
        total_weighted_corr = 0
        total_weight_pairs = 0
        
        for i, scheme1 in enumerate(scheme_names):
            for j, scheme2 in enumerate(scheme_names):
                if i != j:
                    weight1 = weights[scheme1]
                    weight2 = weights[scheme2]
                    corr = corr_matrix.loc[scheme1, scheme2]
                    
                    total_weighted_corr += weight1 * weight2 * corr
                    total_weight_pairs += weight1 * weight2
        
        avg_corr = total_weighted_corr / total_weight_pairs if total_weight_pairs > 0 else 0
        
        # Diversification score (lower correlation = higher score)
        div_score = 1 - avg_corr
        
        return max(0, min(1, div_score))


# Convenience functions
def compare_mutual_funds(schemes_data: Dict[str, pd.Series]) -> pd.DataFrame:
    analyzer = PortfolioAnalyzer()
    return analyzer.compare_schemes(schemes_data)


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧪 Testing Portfolio Analyzer")
    print("="*70 + "\n")
    
    # Create sample data for 3 schemes
    np.random.seed(42)
    dates = pd.date_range(start='2020-01-01', end='2024-12-31', freq='D')
    
    schemes_data = {
        'Scheme A': pd.Series(100 * (1 + np.random.randn(len(dates)) * 0.008).cumprod()),
        'Scheme B': pd.Series(100 * (1 + np.random.randn(len(dates)) * 0.012).cumprod()),
        'Scheme C': pd.Series(100 * (1 + np.random.randn(len(dates)) * 0.010).cumprod())
    }
    
    analyzer = PortfolioAnalyzer()
    
    # Test 1: Compare schemes
    print("📌 Test 1: Comparing Schemes")
    comparison = analyzer.compare_schemes(schemes_data)
    print(comparison.to_string(index=False))
    
    # Test 2: Rank by Sharpe ratio
    print("\n📌 Test 2: Ranking by Sharpe Ratio")
    ranked = analyzer.rank_schemes(schemes_data, 'sharpe_ratio')
    print(ranked[['Rank', 'Scheme', 'Sharpe Ratio', 'CAGR (%)']].to_string(index=False))
    
    # Test 3: Portfolio metrics
    print("\n📌 Test 3: Portfolio Metrics (Equal Weight)")
    weights = {'Scheme A': 0.33, 'Scheme B': 0.33, 'Scheme C': 0.34}
    portfolio_metrics = analyzer.calculate_portfolio_metrics(schemes_data, weights)
    print(f"Annualized Return: {portfolio_metrics['annualized_return']*100:.2f}%")
    print(f"Volatility: {portfolio_metrics['volatility']*100:.2f}%")
    print(f"Sharpe Ratio: {portfolio_metrics['sharpe_ratio']:.3f}")
    print(f"Max Drawdown: {abs(portfolio_metrics['max_drawdown'])*100:.2f}%")
    
    # Test 4: Find best scheme
    print("\n📌 Test 4: Finding Best Scheme")
    best_scheme, metrics = analyzer.find_best_scheme(schemes_data, 'risk_adjusted_return')
    print(f"Best Scheme (Sharpe): {best_scheme}")
    print(f"Sharpe Ratio: {metrics['Sharpe Ratio']:.3f}")
    
    # Test 5: Diversification score
    print("\n📌 Test 5: Diversification Score")
    div_score = analyzer.get_diversification_score(schemes_data, weights)
    print(f"Diversification Score: {div_score:.3f}")
    
    print("\n" + "="*70)
    print("✅ Portfolio analyzer working successfully!")
    print("="*70)

"""
Scheme Comparison Module
Handles comparison of multiple mutual fund schemes
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from analytics.financial_metrics import FinancialMetricsCalculator
from analytics.risk_metrics import RiskMetricsCalculator


class SchemeComparator:
    """Compare multiple mutual fund schemes"""
    
    def __init__(self):
        self.fin_calc = FinancialMetricsCalculator()
        self.risk_calc = RiskMetricsCalculator()
    
    def compare_schemes(
        self,
        scheme_codes: List[str],
        nav_data: Dict[str, pd.Series],
        date_series: Optional[pd.Series] = None
    ) -> Dict:
        """
        Compare multiple schemes and return comprehensive comparison
        
        Args:
            scheme_codes: List of scheme codes to compare
            nav_data: Dict of {scheme_code: nav_series}
            date_series: Optional date series
        
        Returns:
            Dictionary with comparison results
        """
        
        if len(scheme_codes) < 2:
            raise ValueError("Need at least 2 schemes to compare")
        
        comparison_data = []
        
        for scheme_code in scheme_codes:
            if scheme_code not in nav_data:
                continue
            
            nav_series = nav_data[scheme_code]
            
            # Calculate metrics
            returns = nav_series.pct_change().dropna()
            
            fin_metrics = self.fin_calc.get_comprehensive_metrics(nav_series, date_series)
            risk_metrics = self.risk_calc.get_comprehensive_risk_metrics(nav_series, date_series)
            
            comparison_data.append({
                'scheme_code': scheme_code,
                'current_nav': fin_metrics['current_nav'],
                'cagr': fin_metrics.get('cagr'),
                'annualized_return': fin_metrics['annualized_return'],
                'sharpe_ratio': fin_metrics.get('sharpe_ratio'),
                'sortino_ratio': fin_metrics.get('sortino_ratio'),
                'volatility': risk_metrics['volatility'],
                'max_drawdown': risk_metrics['max_drawdown'],
                'downside_deviation': risk_metrics['downside_deviation'],
                'var_95': risk_metrics['var_95'],
                'calmar_ratio': risk_metrics.get('calmar_ratio')
            })
        
        # Convert to DataFrame
        df_comparison = pd.DataFrame(comparison_data)
        
        # Rank schemes
        rankings = self._calculate_rankings(df_comparison)
        
        # Best performers
        best_schemes = self._find_best_schemes(df_comparison)
        
        return {
            'comparison': df_comparison,
            'rankings': rankings,
            'best_schemes': best_schemes
        }
    
    def _calculate_rankings(self, df: pd.DataFrame) -> Dict:
        """Calculate rankings for each metric"""
        
        rankings = {}
        
        metrics_to_rank = [
            'sharpe_ratio', 'sortino_ratio', 'cagr', 
            'volatility', 'max_drawdown', 'calmar_ratio'
        ]
        
        for metric in metrics_to_rank:
            if metric in df.columns and df[metric].notna().any():
                # Higher is better for return metrics
                if metric in ['sharpe_ratio', 'sortino_ratio', 'cagr', 'calmar_ratio']:
                    rankings[f'{metric}_rank'] = df[metric].rank(ascending=False)
                # Lower is better for risk metrics
                else:
                    rankings[f'{metric}_rank'] = df[metric].rank(ascending=True)
        
        return rankings
    
    def _find_best_schemes(self, df: pd.DataFrame) -> Dict:
        """Find best schemes by different criteria"""
        
        best = {}
        
        # Best by Sharpe Ratio
        if 'sharpe_ratio' in df.columns:
            best_sharpe_idx = df['sharpe_ratio'].idxmax()
            best['best_by_sharpe'] = {
                'scheme_code': df.loc[best_sharpe_idx, 'scheme_code'],
                'sharpe_ratio': df.loc[best_sharpe_idx, 'sharpe_ratio']
            }
        
        # Best by CAGR
        if 'cagr' in df.columns:
            best_cagr_idx = df['cagr'].idxmax()
            best['best_by_return'] = {
                'scheme_code': df.loc[best_cagr_idx, 'scheme_code'],
                'cagr': df.loc[best_cagr_idx, 'cagr']
            }
        
        # Lowest Volatility
        if 'volatility' in df.columns:
            best_vol_idx = df['volatility'].idxmin()
            best['lowest_volatility'] = {
                'scheme_code': df.loc[best_vol_idx, 'scheme_code'],
                'volatility': df.loc[best_vol_idx, 'volatility']
            }
        
        # Lowest Max Drawdown
        if 'max_drawdown' in df.columns:
            best_dd_idx = df['max_drawdown'].idxmin()
            best['lowest_drawdown'] = {
                'scheme_code': df.loc[best_dd_idx, 'scheme_code'],
                'max_drawdown': df.loc[best_dd_idx, 'max_drawdown']
            }
        
        return best
    
    def get_correlation_matrix(self, nav_data: Dict[str, pd.Series]) -> pd.DataFrame:
        """Get correlation matrix between schemes"""
        
        returns_dict = {}
        for scheme_code, nav_series in nav_data.items():
            returns_dict[scheme_code] = nav_series.pct_change().dropna()
        
        returns_df = pd.DataFrame(returns_dict)
        return returns_df.corr()
    
    def get_comparison_summary(
        self,
        scheme_codes: List[str],
        nav_data: Dict[str, pd.Series]
    ) -> Dict:
        """Get summary statistics for comparison"""
        
        summary = {}
        
        for scheme_code in scheme_codes:
            if scheme_code not in nav_data:
                continue
            
            nav_series = nav_data[scheme_code]
            returns = nav_series.pct_change().dropna()
            
            summary[scheme_code] = {
                'mean_daily_return': returns.mean(),
                'std_daily_return': returns.std(),
                'min_return': returns.min(),
                'max_return': returns.max(),
                'skewness': returns.skew(),
                'kurtosis': returns.kurtosis()
            }
        
        return summary

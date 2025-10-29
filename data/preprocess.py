"""
Data preprocessing module for MF_NAVigator
Cleans and prepares data for analysis and modeling
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple


class DataPreprocessor:
    """Preprocess mutual fund data for analysis"""
    
    def __init__(self):
        pass
    
    def clean_nav_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean NAV data: remove duplicates, handle missing values
        """
        print("🧹 Cleaning NAV data...")
        
        initial_count = len(df)
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['Scheme_Code', 'Date'], keep='last')
        
        # Remove rows with missing NAV
        df = df.dropna(subset=['NAV'])
        
        # Remove zero or negative NAV values
        df = df[df['NAV'] > 0]
        
        # Sort by date
        df = df.sort_values(['Scheme_Code', 'Date']).reset_index(drop=True)
        
        removed = initial_count - len(df)
        print(f"✅ Removed {removed:,} invalid records")
        print(f"✅ Clean data: {len(df):,} records")
        
        return df
    
    def calculate_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate daily, weekly, monthly returns
        """
        print("📈 Calculating returns...")
        
        # Sort by scheme and date
        df = df.sort_values(['Scheme_Code', 'Date'])
        
        # Daily returns
        df['Daily_Return'] = df.groupby('Scheme_Code')['NAV'].pct_change()
        
        # 7-day return
        df['Return_7D'] = df.groupby('Scheme_Code')['NAV'].pct_change(periods=7)
        
        # 30-day return
        df['Return_30D'] = df.groupby('Scheme_Code')['NAV'].pct_change(periods=30)
        
        # 90-day return
        df['Return_90D'] = df.groupby('Scheme_Code')['NAV'].pct_change(periods=90)
        
        # 1-year return (252 trading days)
        df['Return_1Y'] = df.groupby('Scheme_Code')['NAV'].pct_change(periods=252)
        
        print("✅ Returns calculated")
        
        return df
    
    def prepare_for_ml(
        self, 
        df: pd.DataFrame,
        scheme_code: str,
        lookback_days: int = 60
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare data for machine learning
        Creates features and target variable
        """
        print(f"🤖 Preparing data for ML (lookback: {lookback_days} days)...")
        
        # Filter for specific scheme
        df_scheme = df[df['Scheme_Code'] == scheme_code].copy()
        df_scheme = df_scheme.sort_values('Date').reset_index(drop=True)
        
        # Create lag features
        for i in range(1, min(lookback_days + 1, 31)):  # Limit to 30 lags
            df_scheme[f'NAV_lag_{i}'] = df_scheme['NAV'].shift(i)
        
        # Create rolling statistics
        for window in [7, 14, 30]:
            df_scheme[f'NAV_rolling_mean_{window}'] = df_scheme['NAV'].rolling(window=window).mean()
            df_scheme[f'NAV_rolling_std_{window}'] = df_scheme['NAV'].rolling(window=window).std()
        
        # Create return features
        df_scheme['return_1d'] = df_scheme['NAV'].pct_change(1)
        df_scheme['return_7d'] = df_scheme['NAV'].pct_change(7)
        df_scheme['return_30d'] = df_scheme['NAV'].pct_change(30)
        
        # Create momentum features
        df_scheme['momentum_7d'] = df_scheme['NAV'] - df_scheme['NAV'].shift(7)
        df_scheme['momentum_30d'] = df_scheme['NAV'] - df_scheme['NAV'].shift(30)
        
        # Drop rows with NaN (due to shifting)
        df_scheme = df_scheme.dropna()
        
        # Separate features and target
        feature_cols = [col for col in df_scheme.columns 
                       if col.startswith(('NAV_lag', 'NAV_rolling', 'return', 'momentum'))]
        
        X = df_scheme[feature_cols]
        y = df_scheme['NAV']
        
        print(f"✅ Prepared {len(X):,} samples with {len(feature_cols)} features")
        
        return X, y
    
    def get_data_summary(self, df: pd.DataFrame) -> dict:
        """
        Get summary statistics of the data
        """
        summary = {
            'total_records': len(df),
            'total_schemes': df['Scheme_Code'].nunique(),
            'date_range': {
                'start': df['Date'].min().strftime('%Y-%m-%d'),
                'end': df['Date'].max().strftime('%Y-%m-%d')
            },
            'nav_stats': {
                'min': float(df['NAV'].min()),
                'max': float(df['NAV'].max()),
                'mean': float(df['NAV'].mean()),
                'median': float(df['NAV'].median())
            }
        }
        
        if 'Category' in df.columns:
            summary['category_counts'] = df['Category'].value_counts().to_dict()
        
        if 'AMC' in df.columns:
            summary['top_amcs'] = df['AMC'].value_counts().head(10).to_dict()
        
        return summary


# Convenience functions
def clean_and_prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """Quick function to clean and prepare data"""
    preprocessor = DataPreprocessor()
    df = preprocessor.clean_nav_data(df)
    df = preprocessor.calculate_returns(df)
    return df


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧪 Testing Data Preprocessor")
    print("="*70 + "\n")
    
    # Create sample data
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    sample_data = pd.DataFrame({
        'Scheme_Code': ['100001'] * len(dates),
        'Scheme_Name': ['Test Fund'] * len(dates),
        'NAV': np.random.randn(len(dates)).cumsum() + 100,
        'Date': dates,
        'AMC': ['Test AMC'] * len(dates)
    })
    
    preprocessor = DataPreprocessor()
    
    # Test cleaning
    print("📌 Test: Cleaning data...")
    cleaned_data = preprocessor.clean_nav_data(sample_data)
    
    # Test returns
    print("\n📌 Test: Calculating returns...")
    data_with_returns = preprocessor.calculate_returns(cleaned_data)
    print(data_with_returns[['Date', 'NAV', 'Daily_Return', 'Return_30D']].tail())
    
    print("\n" + "="*70)
    print("✅ Preprocessor working successfully!")
    print("="*70)

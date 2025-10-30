import pandas as pd
import numpy as np
from typing import Tuple, Dict, Optional
import joblib
from pathlib import Path
from datetime import datetime, timedelta

from xgboost import XGBRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit

import sys
sys.path.append(str(Path(__file__).parent.parent))
from backend.config import settings


class NAVPredictor:
    
    def __init__(
        self,
        lookback_days: int = 60,
        forecast_days: int = 30,
        model_params: Dict = None
    ):
        
        self.lookback_days = lookback_days
        self.forecast_days = forecast_days
        
        # Default XGBoost parameters
        self.model_params = model_params or {
            'n_estimators': 100,
            'learning_rate': 0.1,
            'max_depth': 5,
            'min_child_weight': 1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'gamma': 0,
            'reg_alpha': 0.1,
            'reg_lambda': 1,
            'random_state': 42,
            'n_jobs': -1
        }
        
        self.model = None
        self.scaler = StandardScaler()
        self.feature_importance = None
        self.is_trained = False
    
    def create_features(
        self,
        nav_series: pd.Series,
        return_target: bool = True
    ) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
        
        df = pd.DataFrame({'NAV': nav_series})
        
        # Lag features (past NAV values)
        for i in range(1, min(self.lookback_days + 1, 31)):
            df[f'lag_{i}'] = df['NAV'].shift(i)
        
        # Rolling statistics
        for window in [7, 14, 21, 30]:
            df[f'rolling_mean_{window}'] = df['NAV'].rolling(window=window).mean()
            df[f'rolling_std_{window}'] = df['NAV'].rolling(window=window).std()
            df[f'rolling_min_{window}'] = df['NAV'].rolling(window=window).min()
            df[f'rolling_max_{window}'] = df['NAV'].rolling(window=window).max()
        
        # Returns features
        df['return_1d'] = df['NAV'].pct_change(1)
        df['return_7d'] = df['NAV'].pct_change(7)
        df['return_14d'] = df['NAV'].pct_change(14)
        df['return_30d'] = df['NAV'].pct_change(30)
        
        # Momentum features
        df['momentum_7d'] = df['NAV'] - df['NAV'].shift(7)
        df['momentum_14d'] = df['NAV'] - df['NAV'].shift(14)
        df['momentum_30d'] = df['NAV'] - df['NAV'].shift(30)
        
        # Volatility features
        df['volatility_7d'] = df['return_1d'].rolling(window=7).std()
        df['volatility_14d'] = df['return_1d'].rolling(window=14).std()
        df['volatility_30d'] = df['return_1d'].rolling(window=30).std()
        
        # Trend features
        df['nav_diff_7d'] = df['NAV'] - df['rolling_mean_7']
        df['nav_diff_30d'] = df['NAV'] - df['rolling_mean_30']
        
        # Time-based features
        if isinstance(nav_series.index, pd.DatetimeIndex):
            df['day_of_week'] = nav_series.index.dayofweek
            df['day_of_month'] = nav_series.index.day
            df['month'] = nav_series.index.month
            df['quarter'] = nav_series.index.quarter
        
        # Drop rows with NaN
        df_clean = df.dropna()
        
        if return_target:
            # Target: NAV value after forecast_days
            target = df_clean['NAV'].shift(-self.forecast_days)
            
            # Remove rows where target is NaN
            valid_idx = target.notna()
            features = df_clean[valid_idx].drop('NAV', axis=1)
            target = target[valid_idx]
            
            return features, target
        else:
            features = df_clean.drop('NAV', axis=1)
            return features, None
    
    def train(
        self,
        nav_series: pd.Series,
        validation_split: float = 0.2
    ) -> Dict:
        
        print(f"🤖 Training NAV Predictor...")
        print(f"   Lookback: {self.lookback_days} days")
        print(f"   Forecast: {self.forecast_days} days ahead")
        
        # Create features
        X, y = self.create_features(nav_series)
        
        print(f"   Features: {X.shape[1]}")
        print(f"   Samples: {len(X)}")
        
        # Split data (time series split)
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        
        # Train model
        print("\n   Training XGBoost model...")
        self.model = XGBRegressor(**self.model_params)
        self.model.fit(
            X_train_scaled, 
            y_train,
            eval_set=[(X_val_scaled, y_val)],
            verbose=False
        )
        
        # Calculate metrics
        train_pred = self.model.predict(X_train_scaled)
        val_pred = self.model.predict(X_val_scaled)
        
        train_mse = np.mean((train_pred - y_train) ** 2)
        val_mse = np.mean((val_pred - y_val) ** 2)
        
        train_mae = np.mean(np.abs(train_pred - y_train))
        val_mae = np.mean(np.abs(val_pred - y_val))
        
        train_mape = np.mean(np.abs((train_pred - y_train) / y_train)) * 100
        val_mape = np.mean(np.abs((val_pred - y_val) / y_val)) * 100
        
        # Feature importance
        self.feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        self.is_trained = True
        
        metrics = {
            'train_mse': train_mse,
            'val_mse': val_mse,
            'train_mae': train_mae,
            'val_mae': val_mae,
            'train_mape': train_mape,
            'val_mape': val_mape,
            'train_samples': len(X_train),
            'val_samples': len(X_val)
        }
        
        print(f"\n✅ Training Complete!")
        print(f"   Train MAE: ₹{train_mae:.4f}")
        print(f"   Val MAE: ₹{val_mae:.4f}")
        print(f"   Train MAPE: {train_mape:.2f}%")
        print(f"   Val MAPE: {val_mape:.2f}%")
        
        return metrics
    
    def predict(
        self,
        nav_series: pd.Series,
        n_days: int = None
    ) -> pd.DataFrame:
        
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        n_days = n_days or self.forecast_days
        
        # Create features for latest data point
        X, _ = self.create_features(nav_series, return_target=False)
        
        # Use the last available features
        X_latest = X.iloc[-1:].copy()
        X_scaled = self.scaler.transform(X_latest)
        
        # Predict
        prediction = self.model.predict(X_scaled)[0]
        
        # Generate future dates
        if isinstance(nav_series.index, pd.DatetimeIndex):
            last_date = nav_series.index[-1]
            pred_date = last_date + pd.Timedelta(days=self.forecast_days)
        else:
            pred_date = len(nav_series) + self.forecast_days
        
        result = pd.DataFrame({
            'Date': [pred_date],
            'Predicted_NAV': [prediction],
            'Current_NAV': [nav_series.iloc[-1]],
            'Change': [prediction - nav_series.iloc[-1]],
            'Change_Percent': [(prediction - nav_series.iloc[-1]) / nav_series.iloc[-1] * 100]
        })
        
        return result
    
    def predict_sequence(
        self,
        nav_series: pd.Series,
        n_days: int = 30
    ) -> pd.DataFrame:
        
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        predictions = []
        current_series = nav_series.copy()
        
        for i in range(n_days):
            # Predict next value
            pred_df = self.predict(current_series)
            pred_value = pred_df['Predicted_NAV'].iloc[0]
            
            predictions.append({
                'Day': i + 1,
                'Predicted_NAV': pred_value,
                'Change_from_today': pred_value - nav_series.iloc[-1],
                'Change_percent': (pred_value - nav_series.iloc[-1]) / nav_series.iloc[-1] * 100
            })
            
            # Append prediction to series for next iteration
            if isinstance(current_series.index, pd.DatetimeIndex):
                next_date = current_series.index[-1] + pd.Timedelta(days=1)
                current_series = pd.concat([
                    current_series,
                    pd.Series([pred_value], index=[next_date])
                ])
            else:
                current_series = pd.concat([
                    current_series,
                    pd.Series([pred_value], index=[len(current_series)])
                ])
        
        return pd.DataFrame(predictions)
    
    def get_feature_importance(self, top_n: int = 10) -> pd.DataFrame:
        
        if self.feature_importance is None:
            raise ValueError("Model not trained yet.")
        
        return self.feature_importance.head(top_n)
    
    def save_model(self, filepath: str = None):
        
        if not self.is_trained:
            raise ValueError("Model not trained yet.")
        
        if filepath is None:
            filepath = settings.MODELS_DIR / "nav_predictor.pkl"
        else:
            filepath = Path(filepath)
        
        # Save model and scaler
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_importance': self.feature_importance,
            'lookback_days': self.lookback_days,
            'forecast_days': self.forecast_days,
            'model_params': self.model_params
        }
        
        joblib.dump(model_data, filepath)
        print(f"💾 Model saved to: {filepath}")
    
    def load_model(self, filepath: str = None):
        """
        Load trained model
        
        Args:
            filepath: Path to load model from
        """
        if filepath is None:
            filepath = settings.MODELS_DIR / "nav_predictor.pkl"
        else:
            filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Model file not found: {filepath}")
        
        model_data = joblib.load(filepath)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_importance = model_data['feature_importance']
        self.lookback_days = model_data['lookback_days']
        self.forecast_days = model_data['forecast_days']
        self.model_params = model_data['model_params']
        self.is_trained = True
        
        print(f"📂 Model loaded from: {filepath}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧪 Testing NAV Predictor")
    print("="*70 + "\n")
    
    # Create sample data
    np.random.seed(42)
    dates = pd.date_range(start='2020-01-01', end='2024-12-31', freq='D')
    nav_values = 100 * (1 + np.random.randn(len(dates)) * 0.01).cumprod()
    nav_series = pd.Series(nav_values, index=dates)
    
    # Initialize predictor
    predictor = NAVPredictor(lookback_days=60, forecast_days=30)
    
    # Test 1: Training
    print("📌 Test 1: Training Model")
    metrics = predictor.train(nav_series)
    
    # Test 2: Single prediction
    print("\n📌 Test 2: Single Prediction (30 days ahead)")
    prediction = predictor.predict(nav_series)
    print(prediction)
    
    # Test 3: Feature importance
    print("\n📌 Test 3: Top 10 Features")
    importance = predictor.get_feature_importance(top_n=10)
    print(importance)
    
    # Test 4: Sequential predictions
    print("\n📌 Test 4: Sequential Predictions (7 days)")
    seq_pred = predictor.predict_sequence(nav_series, n_days=7)
    print(seq_pred)
    
    print("\n" + "="*70)
    print("✅ NAV Predictor working successfully!")
    print("="*70)

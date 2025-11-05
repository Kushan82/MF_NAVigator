import pandas as pd
import numpy as np
from typing import Tuple, Dict, Optional
import joblib
from pathlib import Path
from datetime import datetime, timedelta

from xgboost import XGBRegressor
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import TimeSeriesSplit

import sys
sys.path.append(str(Path(__file__).parent.parent))
from backend.config import settings


class ImprovedNAVPredictor:
    """
    Improved NAV Predictor with realistic predictions
    Key improvements:
    - Better feature engineering
    - Robust scaling
    - Constrained predictions
    - Better hyperparameters
    """
    
    def __init__(
        self,
        lookback_days: int = 90,  # Increased from 60
        forecast_days: int = 30,
        model_params: Dict = None
    ):
        self.lookback_days = lookback_days
        self.forecast_days = forecast_days
        
        # Improved XGBoost parameters for stability
        self.model_params = model_params or {
            'n_estimators': 200,  # More trees for stability
            'learning_rate': 0.05,  # Lower learning rate
            'max_depth': 4,  # Shallower trees to prevent overfitting
            'min_child_weight': 3,  # Higher to prevent overfitting
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'gamma': 0.1,  # Minimum loss reduction
            'reg_alpha': 0.5,  # L1 regularization
            'reg_lambda': 2,  # L2 regularization (increased)
            'random_state': 42,
            'n_jobs': -1,
            'objective': 'reg:squarederror'
        }
        
        self.model = None
        # Use RobustScaler instead of StandardScaler - better for outliers
        self.scaler = RobustScaler()
        self.feature_importance = None
        self.is_trained = False
        
        # Store training statistics for validation
        self.train_mean = None
        self.train_std = None
        self.max_change_pct = 0.05  # Max 5% change allowed per prediction
    
    def create_features(
        self,
        nav_series: pd.Series,
        return_target: bool = True
    ) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
        """
        Enhanced feature engineering with focus on realistic patterns
        """
        df = pd.DataFrame({'NAV': nav_series})
        
        # Core lag features (fewer, more relevant)
        for i in [1, 2, 3, 5, 7, 14, 21, 30]:
            if i <= len(df):
                df[f'lag_{i}'] = df['NAV'].shift(i)
        
        # Percentage change features (more stable than absolute values)
        df['pct_change_1d'] = df['NAV'].pct_change(1)
        df['pct_change_7d'] = df['NAV'].pct_change(7)
        df['pct_change_14d'] = df['NAV'].pct_change(14)
        df['pct_change_30d'] = df['NAV'].pct_change(30)
        
        # Rolling statistics
        for window in [7, 14, 30, 60]:
            if window <= len(df):
                df[f'rolling_mean_{window}'] = df['NAV'].rolling(window=window).mean()
                df[f'rolling_std_{window}'] = df['NAV'].rolling(window=window).std()
                
                # Ratio features (more stable)
                df[f'nav_to_ma_{window}'] = df['NAV'] / df[f'rolling_mean_{window}']
        
        # Volatility features (important for mutual funds)
        df['volatility_7d'] = df['pct_change_1d'].rolling(window=7).std()
        df['volatility_30d'] = df['pct_change_1d'].rolling(window=30).std()
        
        # Trend features
        df['trend_7d'] = (df['NAV'] - df['NAV'].shift(7)) / df['NAV'].shift(7)
        df['trend_30d'] = (df['NAV'] - df['NAV'].shift(30)) / df['NAV'].shift(30)
        
        # Moving average crossovers
        if 'rolling_mean_7' in df.columns and 'rolling_mean_30' in df.columns:
            df['ma_cross'] = df['rolling_mean_7'] - df['rolling_mean_30']
        
        # Momentum indicators
        df['momentum_7d'] = df['pct_change_7d'] - df['pct_change_7d'].shift(7)
        
        # Time-based features (if datetime index)
        if isinstance(nav_series.index, pd.DatetimeIndex):
            df['day_of_week'] = nav_series.index.dayofweek
            df['month'] = nav_series.index.month
            df['quarter'] = nav_series.index.quarter
            
            # Is it month-end? (important for mutual funds)
            df['is_month_end'] = (nav_series.index.day > 25).astype(int)
        
        # Remove infinite values and NaN
        df = df.replace([np.inf, -np.inf], np.nan)
        df_clean = df.dropna()
        
        if return_target:
            # Target: PERCENTAGE CHANGE instead of absolute NAV
            # This is more stable for prediction
            future_nav = df_clean['NAV'].shift(-self.forecast_days)
            target = (future_nav - df_clean['NAV']) / df_clean['NAV']  # Percentage change
            
            # Remove rows where target is NaN
            valid_idx = target.notna()
            features = df_clean[valid_idx].drop('NAV', axis=1)
            target = target[valid_idx]
            
            # Store current NAV for reconstruction
            features['current_nav'] = df_clean.loc[valid_idx, 'NAV']
            
            return features, target
        else:
            features = df_clean.drop('NAV', axis=1)
            features['current_nav'] = df_clean['NAV']
            return features, None
    
    def train(
        self,
        nav_series: pd.Series,
        validation_split: float = 0.2
    ) -> Dict:
        """
        Train model with enhanced validation
        """
        print(f"🤖 Training Improved NAV Predictor...")
        print(f"   Lookback: {self.lookback_days} days")
        print(f"   Forecast: {self.forecast_days} days ahead")
        
        # Store training statistics
        self.train_mean = nav_series.mean()
        self.train_std = nav_series.std()
        
        # Create features (target is now percentage change)
        X, y = self.create_features(nav_series)
        
        print(f"   Features: {X.shape[1] - 1}")  # -1 for current_nav column
        print(f"   Samples: {len(X)}")
        
        # Extract current_nav and remove from features
        current_navs = X['current_nav'].values
        X_features = X.drop('current_nav', axis=1)
        
        # Split data (time series split)
        split_idx = int(len(X_features) * (1 - validation_split))
        X_train, X_val = X_features.iloc[:split_idx], X_features.iloc[split_idx:]
        y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]
        train_navs, val_navs = current_navs[:split_idx], current_navs[split_idx:]
        
        # Scale features (using RobustScaler)
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
        
        # Calculate metrics (convert back to NAV values)
        train_pct_pred = self.model.predict(X_train_scaled)
        val_pct_pred = self.model.predict(X_val_scaled)
        
        # Convert percentage predictions back to NAV
        train_pred = train_navs * (1 + train_pct_pred)
        val_pred = val_navs * (1 + val_pct_pred)
        train_actual = train_navs * (1 + y_train)
        val_actual = val_navs * (1 + y_val)
        
        # Calculate metrics
        train_mae = np.mean(np.abs(train_pred - train_actual))
        val_mae = np.mean(np.abs(val_pred - val_actual))
        
        train_mape = np.mean(np.abs((train_pred - train_actual) / train_actual)) * 100
        val_mape = np.mean(np.abs((val_pred - val_actual) / val_actual)) * 100
        
        # Directional accuracy
        train_dir = np.mean(np.sign(train_pct_pred) == np.sign(y_train)) * 100
        val_dir = np.mean(np.sign(val_pct_pred) == np.sign(y_val)) * 100
        
        # Feature importance
        self.feature_importance = pd.DataFrame({
            'feature': X_features.columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        self.is_trained = True
        
        metrics = {
            'train_mae': train_mae,
            'val_mae': val_mae,
            'train_mape': train_mape,
            'val_mape': val_mape,
            'train_directional': train_dir,
            'val_directional': val_dir,
            'train_samples': len(X_train),
            'val_samples': len(X_val)
        }
        
        print(f"\n✅ Training Complete!")
        print(f"   Train MAE: ₹{train_mae:.4f} ({train_mape:.2f}%)")
        print(f"   Val MAE: ₹{val_mae:.4f} ({val_mape:.2f}%)")
        print(f"   Val Directional Accuracy: {val_dir:.2f}%")
        
        # Warning if validation metrics are poor
        if val_mape > 5:
            print(f"\n⚠️  Warning: Validation MAPE is high ({val_mape:.2f}%)")
            print(f"   Predictions may be unreliable for this scheme")
        
        return metrics
    
    def predict(
        self,
        nav_series: pd.Series,
        apply_constraints: bool = True
    ) -> pd.DataFrame:
        """
        Predict with realistic constraints
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        # Create features
        X, _ = self.create_features(nav_series, return_target=False)
        
        # Extract current NAV
        current_nav = X.iloc[-1]['current_nav']
        X_features = X.iloc[-1:].drop('current_nav', axis=1)
        
        # Scale and predict PERCENTAGE CHANGE
        X_scaled = self.scaler.transform(X_features)
        pct_change_pred = self.model.predict(X_scaled)[0]
        
        # Apply constraints to prevent unrealistic predictions
        if apply_constraints:
            # Constrain to ±5% maximum change
            max_change = self.max_change_pct * (self.forecast_days / 30)  # Scale by days
            pct_change_pred = np.clip(pct_change_pred, -max_change, max_change)
            
            # Additional constraint: use historical volatility
            recent_returns = nav_series.pct_change().dropna().tail(90)
            if len(recent_returns) > 0:
                hist_vol = recent_returns.std() * np.sqrt(252)  # Annualized vol
                max_move = hist_vol * np.sqrt(self.forecast_days / 252) * 2  # 2 std devs
                pct_change_pred = np.clip(pct_change_pred, -max_move, max_move)
        
        # Convert percentage change to NAV
        predicted_nav = current_nav * (1 + pct_change_pred)
        
        # Generate future date
        if isinstance(nav_series.index, pd.DatetimeIndex):
            last_date = nav_series.index[-1]
            pred_date = last_date + pd.Timedelta(days=self.forecast_days)
        else:
            pred_date = len(nav_series) + self.forecast_days
        
        result = pd.DataFrame({
            'Date': [pred_date],
            'Predicted_NAV': [predicted_nav],
            'Current_NAV': [current_nav],
            'Change': [predicted_nav - current_nav],
            'Change_Percent': [pct_change_pred * 100]
        })
        
        return result
    
    def predict_sequence(
        self,
        nav_series: pd.Series,
        n_days: int = 30
    ) -> pd.DataFrame:
        """
        Sequential predictions with drift correction
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        predictions = []
        current_series = nav_series.copy()
        
        # Calculate average daily return for drift correction
        avg_daily_return = nav_series.pct_change().mean()
        
        for i in range(n_days):
            # Predict next value
            pred_df = self.predict(current_series, apply_constraints=True)
            pred_value = pred_df['Predicted_NAV'].iloc[0]
            
            # Apply additional smoothing for multi-step
            if i > 0:
                # Use exponential smoothing
                alpha = 0.3
                prev_value = float(current_series.iloc[-1])
                pred_value = alpha * pred_value + (1 - alpha) * (prev_value * (1 + avg_daily_return))
            
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
            filepath = settings.MODELS_DIR / "improved_nav_predictor.pkl"
        else:
            filepath = Path(filepath)
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_importance': self.feature_importance,
            'lookback_days': self.lookback_days,
            'forecast_days': self.forecast_days,
            'model_params': self.model_params,
            'train_mean': self.train_mean,
            'train_std': self.train_std,
            'max_change_pct': self.max_change_pct
        }
        
        joblib.dump(model_data, filepath)
        print(f"💾 Model saved to: {filepath}")
    
    def load_model(self, filepath: str = None):
        if filepath is None:
            filepath = settings.MODELS_DIR / "improved_nav_predictor.pkl"
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
        self.train_mean = model_data.get('train_mean')
        self.train_std = model_data.get('train_std')
        self.max_change_pct = model_data.get('max_change_pct', 0.05)
        self.is_trained = True
        
        print(f"📂 Model loaded from: {filepath}")


# Alias for backwards compatibility
NAVPredictor = ImprovedNAVPredictor
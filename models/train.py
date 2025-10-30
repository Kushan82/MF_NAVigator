import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from pathlib import Path

from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

import sys
sys.path.append(str(Path(__file__).parent.parent))
from backend.config import settings
from models.predictor import NAVPredictor


class ModelTrainer:
    """Training pipeline for NAV prediction models"""
    
    def __init__(self):
        self.best_model = None
        self.best_params = None
        self.cv_results = None
    
    def cross_validate(
        self,
        nav_series: pd.Series,
        n_splits: int = 5,
        lookback_days: int = 60,
        forecast_days: int = 30
    ) -> Dict:
        
        print(f"🔄 Performing {n_splits}-fold Cross-Validation...")
        
        predictor = NAVPredictor(
            lookback_days=lookback_days,
            forecast_days=forecast_days
        )
        
        # Create features
        X, y = predictor.create_features(nav_series)
        
        # Time series split
        tscv = TimeSeriesSplit(n_splits=n_splits)
        
        fold_results = []
        
        for fold, (train_idx, val_idx) in enumerate(tscv.split(X), 1):
            print(f"\n   Fold {fold}/{n_splits}...")
            
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            # Scale features
            X_train_scaled = predictor.scaler.fit_transform(X_train)
            X_val_scaled = predictor.scaler.transform(X_val)
            
            # Train model
            predictor.model = predictor.model.__class__(**predictor.model_params)
            predictor.model.fit(X_train_scaled, y_train, verbose=False)
            
            # Predict
            y_pred = predictor.model.predict(X_val_scaled)
            
            # Calculate metrics
            mse = mean_squared_error(y_val, y_pred)
            mae = mean_absolute_error(y_val, y_pred)
            rmse = np.sqrt(mse)
            mape = np.mean(np.abs((y_val - y_pred) / y_val)) * 100
            r2 = r2_score(y_val, y_pred)
            
            fold_results.append({
                'fold': fold,
                'mse': mse,
                'mae': mae,
                'rmse': rmse,
                'mape': mape,
                'r2': r2
            })
            
            print(f"      MAE: ₹{mae:.4f} | MAPE: {mape:.2f}% | R²: {r2:.4f}")
        
        # Aggregate results
        cv_results = pd.DataFrame(fold_results)
        
        summary = {
            'mean_mae': cv_results['mae'].mean(),
            'std_mae': cv_results['mae'].std(),
            'mean_mape': cv_results['mape'].mean(),
            'std_mape': cv_results['mape'].std(),
            'mean_r2': cv_results['r2'].mean(),
            'std_r2': cv_results['r2'].std(),
            'fold_results': cv_results
        }
        
        self.cv_results = cv_results
        
        print(f"\n✅ Cross-Validation Complete!")
        print(f"   Mean MAE: ₹{summary['mean_mae']:.4f} (±{summary['std_mae']:.4f})")
        print(f"   Mean MAPE: {summary['mean_mape']:.2f}% (±{summary['std_mape']:.2f}%)")
        print(f"   Mean R²: {summary['mean_r2']:.4f} (±{summary['std_r2']:.4f})")
        
        return summary
    
    def hyperparameter_search(
        self,
        nav_series: pd.Series,
        param_grid: Dict[str, List] = None
    ) -> Dict:
        
        if param_grid is None:
            param_grid = {
                'n_estimators': [50, 100, 150],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [3, 5, 7]
            }
        
        print(f"🔍 Hyperparameter Search...")
        print(f"   Testing {np.prod([len(v) for v in param_grid.values()])} combinations\n")
        
        best_score = float('inf')
        best_params = None
        results = []
        
        # Generate all combinations
        from itertools import product
        param_combinations = [
            dict(zip(param_grid.keys(), v))
            for v in product(*param_grid.values())
        ]
        
        for i, params in enumerate(param_combinations, 1):
            print(f"   [{i}/{len(param_combinations)}] Testing: {params}")
            
            # Create predictor with these params
            predictor = NAVPredictor(
                lookback_days=60,
                forecast_days=30,
                model_params={**NAVPredictor().model_params, **params}
            )
            
            # Train and evaluate
            metrics = predictor.train(nav_series, validation_split=0.2)
            
            results.append({
                **params,
                'val_mae': metrics['val_mae'],
                'val_mape': metrics['val_mape']
            })
            
            # Track best
            if metrics['val_mae'] < best_score:
                best_score = metrics['val_mae']
                best_params = params
                self.best_model = predictor
        
        self.best_params = best_params
        
        print(f"\n✅ Search Complete!")
        print(f"   Best Params: {best_params}")
        print(f"   Best MAE: ₹{best_score:.4f}")
        
        return {
            'best_params': best_params,
            'best_mae': best_score,
            'all_results': pd.DataFrame(results)
        }
    
    def train_final_model(
        self,
        nav_series: pd.Series,
        use_best_params: bool = True,
        save_model: bool = True
    ) -> NAVPredictor:
       
        print("🎯 Training Final Model...")
        
        # Use best params if available
        model_params = None
        if use_best_params and self.best_params:
            model_params = {**NAVPredictor().model_params, **self.best_params}
            print(f"   Using best params: {self.best_params}")
        
        # Create and train predictor
        predictor = NAVPredictor(
            lookback_days=60,
            forecast_days=30,
            model_params=model_params
        )
        
        metrics = predictor.train(nav_series, validation_split=0.1)
        
        # Save model
        if save_model:
            predictor.save_model()
        
        self.best_model = predictor
        
        return predictor
    
    def evaluate_on_test_set(
        self,
        nav_series: pd.Series,
        test_start_date: str = None
    ) -> Dict:
       
        if self.best_model is None:
            raise ValueError("No model trained. Train a model first.")
        
        print("📊 Evaluating on Test Set...")
        
        # Split data
        if test_start_date:
            test_start = pd.to_datetime(test_start_date)
            train_data = nav_series[nav_series.index < test_start]
            test_data = nav_series[nav_series.index >= test_start]
        else:
            split_idx = int(len(nav_series) * 0.8)
            train_data = nav_series.iloc[:split_idx]
            test_data = nav_series.iloc[split_idx:]
        
        print(f"   Train: {len(train_data)} days")
        print(f"   Test: {len(test_data)} days")
        
        # Create features for test set
        X_test, y_test = self.best_model.create_features(nav_series)
        
        # Get test indices
        test_idx = y_test.index >= test_data.index[0]
        X_test = X_test[test_idx]
        y_test = y_test[test_idx]
        
        # Scale and predict
        X_test_scaled = self.best_model.scaler.transform(X_test)
        y_pred = self.best_model.model.predict(X_test_scaled)
        
        # Calculate metrics
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
        r2 = r2_score(y_test, y_pred)
        
        metrics = {
            'test_mse': mse,
            'test_mae': mae,
            'test_rmse': rmse,
            'test_mape': mape,
            'test_r2': r2,
            'test_samples': len(y_test)
        }
        
        print(f"\n✅ Test Evaluation Complete!")
        print(f"   MAE: ₹{mae:.4f}")
        print(f"   RMSE: ₹{rmse:.4f}")
        print(f"   MAPE: {mape:.2f}%")
        print(f"   R²: {r2:.4f}")
        
        return metrics


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧪 Testing Model Trainer")
    print("="*70 + "\n")
    
    # Create sample data
    np.random.seed(42)
    dates = pd.date_range(start='2020-01-01', end='2024-12-31', freq='D')
    nav_values = 100 * (1 + np.random.randn(len(dates)) * 0.01).cumprod()
    nav_series = pd.Series(nav_values, index=dates)
    
    trainer = ModelTrainer()
    
    # Test 1: Cross-validation
    print("📌 Test 1: Cross-Validation")
    cv_results = trainer.cross_validate(nav_series, n_splits=3)
    
    # Test 2: Train final model
    print("\n📌 Test 2: Training Final Model")
    final_model = trainer.train_final_model(nav_series, use_best_params=False, save_model=False)
    
    # Test 3: Test set evaluation
    print("\n📌 Test 3: Test Set Evaluation")
    test_metrics = trainer.evaluate_on_test_set(nav_series)
    
    print("\n" + "="*70)
    print("✅ Model trainer working successfully!")
    print("="*70)

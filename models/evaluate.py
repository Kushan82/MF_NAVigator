import pandas as pd
import numpy as np
from typing import Dict, Tuple
from pathlib import Path

from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_error,
    r2_score,
    mean_absolute_percentage_error
)

import sys
sys.path.append(str(Path(__file__).parent.parent))
from models.predictor import NAVPredictor


class ModelEvaluator:
    
    def __init__(self, predictor: NAVPredictor):
        
        self.predictor = predictor
    
    def calculate_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> Dict:
        
        # Basic metrics
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        
        # Percentage errors
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        
        # Directional accuracy (did we predict direction correctly?)
        y_true_diff = np.diff(y_true)
        y_pred_diff = np.diff(y_pred)
        direction_correct = np.sum(np.sign(y_true_diff) == np.sign(y_pred_diff))
        directional_accuracy = direction_correct / len(y_true_diff) * 100
        
        # Max error
        max_error = np.max(np.abs(y_true - y_pred))
        
        # Mean error (bias)
        mean_error = np.mean(y_pred - y_true)
        
        metrics = {
            'mse': mse,
            'rmse': rmse,
            'mae': mae,
            'mape': mape,
            'r2': r2,
            'max_error': max_error,
            'mean_error': mean_error,
            'directional_accuracy': directional_accuracy
        }
        
        return metrics
    
    def evaluate_model(
        self,
        nav_series: pd.Series,
        test_size: float = 0.2
    ) -> Dict:
        
        print("📊 Evaluating Model Performance...")
        
        # Create features
        X, y = self.predictor.create_features(nav_series)
        
        # Train-test split
        split_idx = int(len(X) * (1 - test_size))
        X_test = X.iloc[split_idx:]
        y_test = y.iloc[split_idx:]
        
        # Scale and predict
        X_test_scaled = self.predictor.scaler.transform(X_test)
        y_pred = self.predictor.model.predict(X_test_scaled)
        
        # Calculate metrics
        metrics = self.calculate_metrics(y_test.values, y_pred)
        
        print(f"\n✅ Evaluation Complete!")
        print(f"   MAE: ₹{metrics['mae']:.4f}")
        print(f"   RMSE: ₹{metrics['rmse']:.4f}")
        print(f"   MAPE: {metrics['mape']:.2f}%")
        print(f"   R²: {metrics['r2']:.4f}")
        print(f"   Directional Accuracy: {metrics['directional_accuracy']:.2f}%")
        
        # Add predictions for analysis
        results = {
            'metrics': metrics,
            'predictions': pd.DataFrame({
                'Date': X_test.index,
                'Actual': y_test.values,
                'Predicted': y_pred,
                'Error': y_pred - y_test.values,
                'Abs_Error': np.abs(y_pred - y_test.values),
                'Pct_Error': (y_pred - y_test.values) / y_test.values * 100
            })
        }
        
        return results
    
    def error_analysis(
        self,
        predictions_df: pd.DataFrame
    ) -> Dict:
        
        print("\n🔍 Error Analysis...")
        
        errors = predictions_df['Error'].values
        abs_errors = predictions_df['Abs_Error'].values
        pct_errors = predictions_df['Pct_Error'].values
        
        analysis = {
            'mean_error': np.mean(errors),
            'std_error': np.std(errors),
            'mean_abs_error': np.mean(abs_errors),
            'median_abs_error': np.median(abs_errors),
            'max_abs_error': np.max(abs_errors),
            'mean_pct_error': np.mean(pct_errors),
            'median_pct_error': np.median(pct_errors),
            'error_range': (np.min(errors), np.max(errors))
        }
        
        # Identify largest errors
        largest_errors = predictions_df.nlargest(5, 'Abs_Error')[
            ['Date', 'Actual', 'Predicted', 'Abs_Error', 'Pct_Error']
        ]
        
        analysis['largest_errors'] = largest_errors
        
        print(f"   Mean Error (Bias): ₹{analysis['mean_error']:.4f}")
        print(f"   Std Error: ₹{analysis['std_error']:.4f}")
        print(f"   Median Abs Error: ₹{analysis['median_abs_error']:.4f}")
        print(f"   Max Abs Error: ₹{analysis['max_abs_error']:.4f}")
        
        return analysis
    
    def forecast_accuracy_by_horizon(
        self,
        nav_series: pd.Series,
        horizons: list = None
    ) -> pd.DataFrame:
       
        if horizons is None:
            horizons = [7, 14, 21, 30, 60, 90]
        
        print(f"\n📈 Testing Forecast Horizons: {horizons}")
        
        results = []
        
        for horizon in horizons:
            # Create predictor for this horizon
            temp_predictor = NAVPredictor(
                lookback_days=self.predictor.lookback_days,
                forecast_days=horizon,
                model_params=self.predictor.model_params
            )
            
            # Train
            temp_predictor.train(nav_series, validation_split=0.2)
            
            # Evaluate
            eval_results = self.evaluate_model.__wrapped__(self, nav_series, temp_predictor)
            
            results.append({
                'Horizon_Days': horizon,
                'MAE': eval_results['metrics']['mae'],
                'RMSE': eval_results['metrics']['rmse'],
                'MAPE': eval_results['metrics']['mape'],
                'R2': eval_results['metrics']['r2']
            })
        
        df_results = pd.DataFrame(results)
        
        print(f"\n✅ Horizon Analysis Complete!")
        print(df_results.to_string(index=False))
        
        return df_results
    
    def residual_analysis(
        self,
        predictions_df: pd.DataFrame
    ) -> Dict:
       
        print("\n🔬 Residual Analysis...")
        
        residuals = predictions_df['Error'].values
        
        # Normality test (simplified)
        from scipy import stats
        _, p_value = stats.normaltest(residuals)
        
        # Autocorrelation (lag-1)
        autocorr = np.corrcoef(residuals[:-1], residuals[1:])[0, 1]
        
        analysis = {
            'mean_residual': np.mean(residuals),
            'std_residual': np.std(residuals),
            'skewness': stats.skew(residuals),
            'kurtosis': stats.kurtosis(residuals),
            'normality_p_value': p_value,
            'is_normal': p_value > 0.05,
            'autocorrelation_lag1': autocorr,
            'residuals': residuals
        }
        
        print(f"   Mean Residual: ₹{analysis['mean_residual']:.4f}")
        print(f"   Std Residual: ₹{analysis['std_residual']:.4f}")
        print(f"   Skewness: {analysis['skewness']:.4f}")
        print(f"   Normality Test p-value: {analysis['normality_p_value']:.4f}")
        print(f"   Autocorrelation (lag-1): {analysis['autocorrelation_lag1']:.4f}")
        
        return analysis
    
    def generate_report(
        self,
        nav_series: pd.Series
    ) -> Dict:
        
        print("\n" + "="*70)
        print("📋 GENERATING COMPREHENSIVE EVALUATION REPORT")
        print("="*70)
        
        # Main evaluation
        eval_results = self.evaluate_model(nav_series)
        
        # Error analysis
        error_analysis = self.error_analysis(eval_results['predictions'])
        
        # Residual analysis
        residual_analysis = self.residual_analysis(eval_results['predictions'])
        
        # Feature importance
        feature_importance = self.predictor.get_feature_importance(top_n=10)
        
        report = {
            'metrics': eval_results['metrics'],
            'predictions': eval_results['predictions'],
            'error_analysis': error_analysis,
            'residual_analysis': residual_analysis,
            'feature_importance': feature_importance
        }
        
        print("\n" + "="*70)
        print("✅ REPORT GENERATION COMPLETE")
        print("="*70)
        
        return report


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧪 Testing Model Evaluator")
    print("="*70 + "\n")
    
    # Create sample data
    np.random.seed(42)
    dates = pd.date_range(start='2020-01-01', end='2024-12-31', freq='D')
    nav_values = 100 * (1 + np.random.randn(len(dates)) * 0.01).cumprod()
    nav_series = pd.Series(nav_values, index=dates)
    
    # Train a model
    predictor = NAVPredictor(lookback_days=60, forecast_days=30)
    predictor.train(nav_series)
    
    # Initialize evaluator
    evaluator = ModelEvaluator(predictor)
    
    # Test 1: Full evaluation
    print("📌 Test 1: Model Evaluation")
    eval_results = evaluator.evaluate_model(nav_series)
    
    # Test 2: Error analysis
    print("\n📌 Test 2: Error Analysis")
    error_analysis = evaluator.error_analysis(eval_results['predictions'])
    
    # Test 3: Residual analysis
    print("\n📌 Test 3: Residual Analysis")
    residual_analysis = evaluator.residual_analysis(eval_results['predictions'])
    
    # Test 4: Generate report
    print("\n📌 Test 4: Generate Comprehensive Report")
    report = evaluator.generate_report(nav_series)
    
    print("\n" + "="*70)
    print("✅ Model evaluator working successfully!")
    print("="*70)

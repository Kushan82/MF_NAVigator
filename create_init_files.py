"""
Create __init__.py files for all modules in MF_NAVigator
Run this from project root: python create_init_files.py
"""

from pathlib import Path

# Define all init files with their content
init_files = {
    'data/__init__.py': '''"""
Data module for MF_NAVigator
Data fetching and preprocessing
"""

from data.fetch_data import MutualFundDataFetcher
from data.preprocess import DataPreprocessor

__all__ = ['MutualFundDataFetcher', 'DataPreprocessor']
''',
    
    'analytics/__init__.py': '''"""
Analytics module for MF_NAVigator
Financial and risk metrics calculators
"""

from analytics.financial_metrics import FinancialMetricsCalculator
from analytics.risk_metrics import RiskMetricsCalculator
from analytics.portfolio_analysis import PortfolioAnalyzer

__all__ = [
    'FinancialMetricsCalculator',
    'RiskMetricsCalculator',
    'PortfolioAnalyzer'
]
''',
    
    'models/__init__.py': '''"""
Models module for MF_NAVigator
ML models for NAV prediction
"""

from models.predictor import NAVPredictor
from models.train import ModelTrainer
from models.evaluate import ModelEvaluator

__all__ = ['NAVPredictor', 'ModelTrainer', 'ModelEvaluator']
''',
    
    'frontend/__init__.py': '''"""
Frontend module for MF_NAVigator
Streamlit dashboard application
"""

__version__ = "1.0.0"
''',
    
    'data/cache/__init__.py': '''"""
Cache directory for storing fetched data
"""
''',
    
    'logs/__init__.py': '''"""
Logs directory for application logs
"""
''',
}

def create_init_files():
    """Create all __init__.py files"""
    
    print("\n" + "="*70)
    print("📁 Creating __init__.py files for MF_NAVigator")
    print("="*70 + "\n")
    
    created = 0
    existed = 0
    errors = 0
    
    for file_path, content in init_files.items():
        try:
            path = Path(file_path)
            
            # Create parent directory if it doesn't exist
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file exists
            if path.exists():
                print(f"✓ {file_path} (already exists)")
                existed += 1
            else:
                # Write content
                path.write_text(content, encoding='utf-8')
                print(f"✅ {file_path} (created)")
                created += 1
                
        except Exception as e:
            print(f"❌ {file_path} (error: {e})")
            errors += 1
    
    print("\n" + "="*70)
    print(f"✅ Summary:")
    print(f"   Created: {created} files")
    print(f"   Already existed: {existed} files")
    print(f"   Errors: {errors} files")
    print(f"   Total: {created + existed} files")
    print("="*70 + "\n")
    
    # Verify project structure
    print("📂 Project Structure:")
    print("MF_NAVigator/")
    for file_path in sorted(init_files.keys()):
        parts = file_path.split('/')
        indent = "  " * (len(parts) - 1)
        print(f"{indent}├── {parts[-1]}")
    
    print("\n✅ All __init__.py files are ready!")
    print("🚀 Your project is now properly structured for deployment.\n")

if __name__ == "__main__":
    create_init_files()

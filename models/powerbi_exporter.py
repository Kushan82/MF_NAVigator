import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from data.fetch_data import MutualFundDataFetcher
from backend.config import settings


class PowerBIDataExporter:
    """Export mutual fund data for Power BI visualization"""
    
    def __init__(self):
        self.fetcher = MutualFundDataFetcher()
        self.export_dir = Path("powerbi_data")
        self.export_dir.mkdir(exist_ok=True)
    
    def fetch_and_prepare_data(self):
        """Fetch latest data from AMFI"""
        print("📥 Fetching latest AMFI data...")
        df = self.fetcher.fetch_amfi_daily_nav(save_to_cache=False)
        df = self.fetcher.get_scheme_categories(df)
        print(f"✅ Fetched {len(df):,} schemes")
        return df
    
    def calculate_aum_by_amc(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate estimated AUM by AMC"""
        print("\n📊 Calculating AUM by AMC...")
        
        amc_stats = df.groupby('AMC').agg({
            'Scheme_Code': 'count',
            'NAV': ['mean', 'sum', 'std'],
            'Category': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'Mixed'
        }).reset_index()
        
        amc_stats.columns = ['AMC', 'Total_Schemes', 'Avg_NAV', 'Total_NAV', 'NAV_Std', 'Primary_Category']
        
        # Estimated AUM (NAV sum * multiplier for visualization)
        amc_stats['Estimated_AUM_Cr'] = amc_stats['Total_NAV'] * 10
        
        # Market share
        total_aum = amc_stats['Estimated_AUM_Cr'].sum()
        amc_stats['Market_Share_Pct'] = (amc_stats['Estimated_AUM_Cr'] / total_aum * 100).round(2)
        
        amc_stats = amc_stats.sort_values('Estimated_AUM_Cr', ascending=False)
        
        print(f"✅ Analyzed {len(amc_stats)} AMCs")
        return amc_stats
    
    def calculate_category_distribution(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate distribution across categories"""
        print("\n📊 Calculating Category Distribution...")
        
        category_stats = df.groupby('Category').agg({
            'Scheme_Code': 'count',
            'NAV': ['mean', 'sum', 'std'],
            'AMC': 'nunique'
        }).reset_index()
        
        category_stats.columns = ['Category', 'Total_Schemes', 'Avg_NAV', 'Total_NAV', 'NAV_Std', 'Num_AMCs']
        category_stats['Estimated_AUM_Cr'] = category_stats['Total_NAV'] * 10
        
        total_schemes = category_stats['Total_Schemes'].sum()
        category_stats['Percentage'] = (category_stats['Total_Schemes'] / total_schemes * 100).round(2)
        
        category_stats = category_stats.sort_values('Total_Schemes', ascending=False)
        
        print(f"✅ Analyzed {len(category_stats)} categories")
        return category_stats
    
    def calculate_amc_category_matrix(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create AMC-Category matrix for sector allocation"""
        print("\n📊 Creating AMC-Category Matrix...")
        
        matrix = df.groupby(['AMC', 'Category']).size().reset_index(name='Scheme_Count')
        nav_stats = df.groupby(['AMC', 'Category'])['NAV'].agg(['mean', 'sum']).reset_index()
        matrix = matrix.merge(nav_stats, on=['AMC', 'Category'])
        matrix.columns = ['AMC', 'Category', 'Scheme_Count', 'Avg_NAV', 'Total_NAV']
        
        print(f"✅ Created matrix with {len(matrix)} combinations")
        return matrix
    
    def calculate_nav_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate market-wide NAV statistics"""
        print("\n📊 Calculating NAV Statistics...")
        
        stats = pd.DataFrame({
            'Metric': [
                'Total Schemes',
                'Average NAV',
                'Median NAV',
                'Min NAV',
                'Max NAV',
                'Std Dev NAV',
                'Total AMCs',
                'Total Categories'
            ],
            'Value': [
                len(df),
                df['NAV'].mean(),
                df['NAV'].median(),
                df['NAV'].min(),
                df['NAV'].max(),
                df['NAV'].std(),
                df['AMC'].nunique(),
                df['Category'].nunique()
            ],
            'Date': datetime.now().strftime('%Y-%m-%d')
        })
        
        print(f"✅ Calculated market statistics")
        return stats
    
    def calculate_top_performers(self, df: pd.DataFrame, top_n: int = 50) -> pd.DataFrame:
        """Identify top schemes by NAV"""
        print(f"\n📊 Finding Top {top_n} Performers...")
        
        top_schemes = df.nlargest(top_n, 'NAV')[
            ['Scheme_Code', 'Scheme_Name', 'AMC', 'Category', 'NAV', 'Date']
        ].copy()
        
        top_schemes['Rank'] = range(1, len(top_schemes) + 1)
        
        print(f"✅ Identified top {len(top_schemes)} schemes")
        return top_schemes
    
    def export_all_datasets(self):
        """Export all datasets for Power BI"""
        print("\n" + "="*70)
        print("📦 EXPORTING ALL DATASETS FOR POWER BI")
        print("="*70)
        
        # Fetch main data
        df = self.fetch_and_prepare_data()
        
        # 1. AMC Market Share
        amc_data = self.calculate_aum_by_amc(df)
        amc_path = self.export_dir / "amc_market_share.csv"
        amc_data.to_csv(amc_path, index=False)
        print(f"\n✅ Exported: {amc_path}")
        
        # 2. Category Distribution
        category_data = self.calculate_category_distribution(df)
        category_path = self.export_dir / "category_distribution.csv"
        category_data.to_csv(category_path, index=False)
        print(f"✅ Exported: {category_path}")
        
        # 3. AMC-Category Matrix
        matrix_data = self.calculate_amc_category_matrix(df)
        matrix_path = self.export_dir / "amc_category_matrix.csv"
        matrix_data.to_csv(matrix_path, index=False)
        print(f"✅ Exported: {matrix_path}")
        
        # 4. Market Statistics
        stats_data = self.calculate_nav_statistics(df)
        stats_path = self.export_dir / "market_statistics.csv"
        stats_data.to_csv(stats_path, index=False)
        print(f"✅ Exported: {stats_path}")
        
        # 5. Top Performers
        top_data = self.calculate_top_performers(df)
        top_path = self.export_dir / "top_performers.csv"
        top_data.to_csv(top_path, index=False)
        print(f"✅ Exported: {top_path}")
        
        # 6. All Schemes Master
        master_path = self.export_dir / "all_schemes_master.csv"
        df.to_csv(master_path, index=False)
        print(f"✅ Exported: {master_path}")
        
        print("\n" + "="*70)
        print("✅ ALL DATASETS EXPORTED SUCCESSFULLY")
        print("="*70)
        print(f"\n📂 Data Location: {self.export_dir.absolute()}")
        
        return {
            'amc_market_share': amc_path,
            'category_distribution': category_path,
            'amc_category_matrix': matrix_path,
            'market_statistics': stats_path,
            'top_performers': top_path,
            'all_schemes': master_path
        }


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 POWER BI DATA EXPORTER FOR MF_NAVIGATOR")
    print("="*70)
    
    exporter = PowerBIDataExporter()
    exported_files = exporter.export_all_datasets()
    
    print("\n📋 Next Steps:")
    print("="*70)
    print("1. Open Power BI Desktop")
    print("2. Get Data → Text/CSV")
    print("3. Import files from powerbi_data folder")
    print("4. Create visualizations:")
    print("   - Total AUM card")
    print("   - Top AMCs bar chart")
    print("   - Category distribution donut chart")
    print("   - Sector allocation heatmap")
    print("5. Publish to Power BI Service (optional)")
    print("6. Embed in Streamlit dashboard")
    print("="*70)
    print("\n✅ Process Complete!")
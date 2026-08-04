import pandas as pd
import os
from sqlalchemy import create_engine
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / '.env')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_business_alerts():
    logging.info("--- Starting Alert Engine ---")

    db_password = os.getenv('DB_PASSWORD')
    if not db_password:
        logging.error("DB_PASSWORD not found in environment variables.")
        return

    db_url = f'postgresql://postgres:{db_password}@localhost:5432/andina_foods_db'
    engine = create_engine(db_url)

    alerts_list = []

    try:
        logging.info("Fetching data from analytical views...")
        df_sales = pd.read_sql("SELECT * FROM vw_monthly_sales_ranking", engine)
        df_production = pd.read_sql("SELECT * FROM vw_plant_performance", engine)

        # Merge on month and product_id
        df_merged = pd.merge(
            df_production,
            df_sales,
            left_on=['production_month', 'product_id'],
            right_on=['sales_month', 'product_id'],
            how='inner',
            suffixes=('_prod', '_sales')
        )

        logging.info("Evaluating business rules...")
        for index, row in df_merged.iterrows():
            defect_rate = row['defect_rate_percentage']
            revenue = row['total_revenue']
            plant = row['plant_location']
            product_name = row['product_name_prod']
            month_str = row['production_month'].strftime('%Y-%m')

            if defect_rate > 5.0:
                alerts_list.append({
                    'alert_date': datetime.now().strftime("%Y-%m-%d"),
                    'alert_type': 'HIGH_DEFECT_RATE',
                    'description': f"High defect rate in {plant} for {product_name} ({defect_rate}%) in {month_str}.",
                    'priority': 'HIGH'
                })
            elif defect_rate > 3.0 and revenue > 5000:
                alerts_list.append({
                    'alert_date': datetime.now().strftime("%Y-%m-%d"),
                    'alert_type': 'REVENUE_AT_RISK',
                    'description': f"Elevated defect rate ({defect_rate}%) in {plant} for high-revenue product {product_name} in {month_str}.",
                    'priority': 'CRITICAL'
                })

        columns = ['alert_date', 'alert_type', 'description', 'priority']
        alerts_df = pd.DataFrame(alerts_list, columns=columns)

        alerts_path = PROJECT_ROOT / 'data' / 'processed' / 'business_alerts.csv'
        alerts_df.to_csv(alerts_path, index=False)

        if not alerts_df.empty:
            logging.info(f"Generated {len(alerts_df)} alerts and saved to {alerts_path}")
        else:
            logging.info("No anomalies detected. Empty alerts file generated for Power BI.")

    except Exception as e:
        logging.error(f"Failed to generate alerts. Error: {e}")

if __name__ == "__main__":
    generate_business_alerts()
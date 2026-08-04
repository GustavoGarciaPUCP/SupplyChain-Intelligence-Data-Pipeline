import pandas as pd
import os
from sqlalchemy import create_engine
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Load environment variables
load_dotenv(PROJECT_ROOT / '.env')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def generate_business_alerts():
    logging.info("--- Starting Alert Engine ---")

    db_password = os.getenv('DB_PASSWORD')
    if not db_password:
        logging.error("DB_PASSWORD not found in environment variables.")
        return

    #Connect to Database
    db_url = f'postgresql://postgres:{db_password}@localhost:5432/andina_foods_db'
    engine = create_engine(db_url)

    alerts_list = []

    try:
        # Evaluate Quality Control rules (Defect rate > 5%)
        logging.info("Evaluating Quality Control rules...")
        query_defects = "SELECT * FROM vw_plant_performance"
        df_plants = pd.read_sql(query_defects, engine)

        high_defects = df_plants[df_plants['defect_rate_percentage'] > 5.0]

        for index, row in high_defects.iterrows():
            alerts_list.append({
                'alert_date': datetime.now().strftime("%Y-%m-%d"),
                'alert_type': 'ALERTA_CALIDAD',
                'description': f"High defect rate in {row['plant_location']} ({row['defect_rate_percentage']}%).",
                'priority': 'HIGH'
            })

        # Define expected columns for Power BI schema stability
        columns = ['alert_date', 'alert_type', 'description', 'priority']
        alerts_df = pd.DataFrame(alerts_list, columns=columns)

        alerts_path = PROJECT_ROOT / 'data' / 'processed' / 'business_alerts.csv'

        # Always save to CSV, even if empty, to prevent Power BI refresh errors
        alerts_df.to_csv(alerts_path, index=False)

        if not alerts_df.empty:
            logging.info(f"Generated {len(alerts_df)} alerts and saved to {alerts_path}")
        else:
            logging.info("No anomalies detected. Empty alerts file generated for Power BI.")

    except Exception as e:
        logging.error(f"Failed to generate alerts. Error: {e}")


if __name__ == "__main__":
    generate_business_alerts()
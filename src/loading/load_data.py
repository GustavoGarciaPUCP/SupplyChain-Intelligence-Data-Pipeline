import pandas as pd
from sqlalchemy import create_engine
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def load_to_postgresql():
    logging.info("--- Starting Database Loading Process ---")

    # 1. Define connection to PostgreSQL
    # Format: postgresql://username:password@host:port/database_name
    # TODO: Change 'TU_CONTRASEÑA_AQUI' to your real pgAdmin password
    db_url = 'postgresql://postgres:123rtyu7io@localhost:5432/andina_foods_db'
    engine = create_engine(db_url)

    # 2. Define file paths
    clean_sales_path = PROJECT_ROOT / 'data' / 'processed' / 'clean_sales.csv'
    clean_production_path = PROJECT_ROOT / 'data' / 'processed' / 'clean_production.csv'

    # 3. Load processed CSVs into DataFrames
    try:
        df_sales = pd.read_csv(clean_sales_path)
        df_production = pd.read_csv(clean_production_path)
        logging.info("Successfully loaded clean data from disk.")
    except FileNotFoundError as e:
        logging.error(f"Could not find processed files. Did you run clean_data.py? Error: {e}")
        return

    # 4. Upload to PostgreSQL
    # if_exists='append' ensures we add to the existing tables without overwriting the schema
    # index=False prevents Pandas from uploading the row numbers as a column
    try:
        df_sales.to_sql(name='sales', con=engine, if_exists='append', index=False)
        logging.info(f"Loaded {len(df_sales)} rows into 'sales' table.")

        df_production.to_sql(name='production', con=engine, if_exists='append', index=False)
        logging.info(f"Loaded {len(df_production)} rows into 'production' table.")

        logging.info("Database loading completed successfully.")
    except Exception as e:
        logging.error(f"Failed to load data to database. Error: {e}")


if __name__ == "__main__":
    load_to_postgresql()
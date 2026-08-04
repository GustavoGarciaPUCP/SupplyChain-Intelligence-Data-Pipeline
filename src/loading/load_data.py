import pandas as pd
from sqlalchemy import create_engine, text
import logging
from pathlib import Path
from dotenv import load_dotenv
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / '.env')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def execute_sql_file(engine, file_path):
    with engine.begin() as conn:
        with open(file_path, 'r') as file:
            sql_script = file.read()
            statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
            for stmt in statements:
                conn.execute(text(stmt))

def load_to_postgresql():
    logging.info("--- Starting Database Loading Process ---")

    db_password = os.getenv('DB_PASSWORD')
    if not db_password:
        logging.error("DB_PASSWORD not found in environment variables.")
        return

    db_url = f'postgresql://postgres:{db_password}@localhost:5432/andina_foods_db'
    engine = create_engine(db_url)

    # 1. Setup schema
    logging.info("Executing schema.sql...")
    execute_sql_file(engine, PROJECT_ROOT / 'database' / 'schema.sql')
    logging.info("Schema updated.")

    # 2. Load Data
    clean_products_path = PROJECT_ROOT / 'data' / 'processed' / 'clean_products.csv'
    clean_sales_path = PROJECT_ROOT / 'data' / 'processed' / 'clean_sales.csv'
    clean_production_path = PROJECT_ROOT / 'data' / 'processed' / 'clean_production.csv'

    try:
        df_products = pd.read_csv(clean_products_path)
        df_sales = pd.read_csv(clean_sales_path)
        df_production = pd.read_csv(clean_production_path)
        logging.info("Successfully loaded clean data from disk.")
    except FileNotFoundError as e:
        logging.error(f"Could not find processed files. Did you run clean_data.py? Error: {e}")
        return

    try:
        df_products.to_sql(name='products', con=engine, if_exists='append', index=False)
        logging.info(f"Loaded {len(df_products)} rows into 'products' table.")

        df_sales.to_sql(name='sales', con=engine, if_exists='append', index=False)
        logging.info(f"Loaded {len(df_sales)} rows into 'sales' table.")

        df_production.to_sql(name='production', con=engine, if_exists='append', index=False)
        logging.info(f"Loaded {len(df_production)} rows into 'production' table.")

        # 3. Setup views
        logging.info("Executing analytical_views.sql...")
        execute_sql_file(engine, PROJECT_ROOT / 'database' / 'analytical_views.sql')
        logging.info("Views updated.")

        logging.info("Database loading completed successfully.")
    except Exception as e:
        logging.error(f"Failed to load data to database. Error: {e}")

if __name__ == "__main__":
    load_to_postgresql()
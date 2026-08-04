import pandas as pd
import numpy as np
import os
import logging
from pathlib import Path
import shutil

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PROJECT_ROOT / "data_quality.log"),
        logging.StreamHandler()
    ]
)

def clean_products_data(input_path, output_path):
    logging.info("--- Starting Products Data Cleaning ---")
    shutil.copy2(input_path, output_path)
    logging.info(f"Products data copied to {output_path}")

def clean_sales_data(input_path, output_path):
    logging.info("--- Starting Sales Data Cleaning ---")
    df = pd.read_csv(input_path)

    initial_rows = len(df)
    df.drop_duplicates(inplace=True)
    logging.info(f"Removed {initial_rows - len(df)} duplicate rows.")

    df['order_date'] = pd.to_datetime(df['order_date'], format='mixed', errors='coerce')

    missing_qty = df['quantity'].isna().sum()
    df.dropna(subset=['quantity'], inplace=True)
    logging.info(f"Dropped {missing_qty} rows with missing quantity.")

    neg_prices = (df['unit_price'] < 0).sum()
    df['unit_price'] = df['unit_price'].abs()
    logging.info(f"Fixed {neg_prices} negative unit prices.")

    df.to_csv(output_path, index=False)
    logging.info(f"Cleaned sales data saved to {output_path}")

def clean_production_data(input_path, output_path):
    logging.info("--- Starting Production Data Cleaning ---")
    df = pd.read_excel(input_path)

    df['plant_location'] = df['plant_location'].str.strip().str.title()

    df['manufactured_qty'] = pd.to_numeric(df['manufactured_qty'], errors='coerce')
    missing_qty = df['manufactured_qty'].isna().sum()

    df['manufactured_qty'] = df['manufactured_qty'].fillna(
        df.groupby('plant_location')['manufactured_qty'].transform('median')
    )
    logging.info(f"Imputed {missing_qty} 'ERROR' or missing values using plant median.")

    # Fix logic where defects > manufactured
    df.loc[df['defect_qty'] > df['manufactured_qty'], 'defect_qty'] = df['manufactured_qty']

    df.to_csv(output_path, index=False)
    logging.info(f"Cleaned production data saved to {output_path}")

if __name__ == "__main__":
    processed_dir = PROJECT_ROOT / 'data' / 'processed'
    os.makedirs(processed_dir, exist_ok=True)

    raw_products = PROJECT_ROOT / 'data' / 'raw' / 'products.csv'
    clean_products = processed_dir / 'clean_products.csv'

    raw_sales = PROJECT_ROOT / 'data' / 'raw' / 'sales_data.csv'
    clean_sales = processed_dir / 'clean_sales.csv'

    raw_prod = PROJECT_ROOT / 'data' / 'raw' / 'production_data.xlsx'
    clean_prod = processed_dir / 'clean_production.csv'

    clean_products_data(raw_products, clean_products)
    clean_sales_data(raw_sales, clean_sales)
    clean_production_data(raw_prod, clean_prod)

    logging.info("Day 2 Pipeline completed successfully.")
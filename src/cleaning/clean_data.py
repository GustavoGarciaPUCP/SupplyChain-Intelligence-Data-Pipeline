import pandas as pd
import numpy as np
import os
import logging
from pathlib import Path

# ROOT
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# 1. Setup Professional Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PROJECT_ROOT / "data_quality.log"),
        logging.StreamHandler()
    ]
)


def clean_sales_data(input_path, output_path):
    logging.info("--- Starting Sales Data Cleaning ---")
    df = pd.read_csv(input_path)

    # Rule A: Remove exact duplicates
    initial_rows = len(df)
    df.drop_duplicates(inplace=True)
    logging.info(f"Removed {initial_rows - len(df)} duplicate rows.")

    # Rule B: Standardize date formats
    df['order_date'] = pd.to_datetime(df['order_date'], format='mixed', errors='coerce')

    # Rule C: Handle missing quantities
    missing_qty = df['quantity'].isna().sum()
    df.dropna(subset=['quantity'], inplace=True)
    logging.info(f"Dropped {missing_qty} rows with missing quantity.")

    # Rule D: Fix negative prices
    neg_prices = (df['unit_price'] < 0).sum()
    df['unit_price'] = df['unit_price'].abs()
    logging.info(f"Fixed {neg_prices} negative unit prices.")

    df.to_csv(output_path, index=False)
    logging.info(f"Cleaned sales data saved to {output_path}")


def clean_production_data(input_path, output_path):
    logging.info("--- Starting Production Data Cleaning ---")
    df = pd.read_excel(input_path)

    # Rule A: Clean inconsistent text
    df['plant_location'] = df['plant_location'].str.strip().str.title()

    # Rule B & C: Fix text in numeric columns and impute
    df['manufactured_qty'] = pd.to_numeric(df['manufactured_qty'], errors='coerce')
    missing_qty = df['manufactured_qty'].isna().sum()

    df['manufactured_qty'] = df['manufactured_qty'].fillna(
        df.groupby('plant_location')['manufactured_qty'].transform('median')
    )
    logging.info(f"Imputed {missing_qty} 'ERROR' or missing values using plant median.")

    df.to_csv(output_path, index=False)
    logging.info(f"Cleaned production data saved to {output_path}")


if __name__ == "__main__":
    # Ensure processed folder exists
    processed_dir = PROJECT_ROOT / 'data' / 'processed'
    os.makedirs(processed_dir, exist_ok=True)

    # Execute pipelines with absolute paths
    raw_sales = PROJECT_ROOT / 'data' / 'raw' / 'sales_data.csv'
    clean_sales = processed_dir / 'clean_sales.csv'

    raw_prod = PROJECT_ROOT / 'data' / 'raw' / 'production_data.xlsx'
    clean_prod = processed_dir / 'clean_production.csv'

    clean_sales_data(raw_sales, clean_sales)
    clean_production_data(raw_prod, clean_prod)

    logging.info("Day 2 Pipeline completed successfully.")
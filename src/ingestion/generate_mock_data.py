import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def create_raw_data_folders():
    """Ensure the raw data directory exists."""
    os.makedirs(PROJECT_ROOT / 'data' / 'raw', exist_ok=True)
    print("Folder 'data/raw' is ready.")

def generate_dimensions():
    """Generates products, plants, and clients dimensions."""
    # Products
    products = [
        {'product_id': 'PRD-001', 'product_name': 'Aceite Premium', 'category': 'Edible Oils'},
        {'product_id': 'PRD-002', 'product_name': 'Fideos Largos', 'category': 'Pasta'},
        {'product_id': 'PRD-003', 'product_name': 'Detergente Industrial', 'category': 'Cleaning Supplies'},
        {'product_id': 'PRD-004', 'product_name': 'Salsa de Tomate', 'category': 'Sauces'}
    ]
    df_products = pd.DataFrame(products)
    df_products.to_csv(PROJECT_ROOT / 'data' / 'raw' / 'products.csv', index=False)

    # Plants
    plants = [
        {'plant_id': 'PL-LIM', 'plant_location': 'Lima', 'region': 'Centro'},
        {'plant_id': 'PL-AQP', 'plant_location': 'Arequipa', 'region': 'Sur'},
        {'plant_id': 'PL-TRU', 'plant_location': 'Trujillo', 'region': 'Norte'}
    ]
    df_plants = pd.DataFrame(plants)
    df_plants.to_csv(PROJECT_ROOT / 'data' / 'raw' / 'plants.csv', index=False)

    # Clients
    clients = [
        {'client_id': 'CL-001', 'client_name': 'Supermercados Peruanos', 'client_type': 'Retail'},
        {'client_id': 'CL-002', 'client_name': 'Cencosud', 'client_type': 'Retail'},
        {'client_id': 'CL-003', 'client_name': 'Bodegas Unidas', 'client_type': 'Wholesale'},
        {'client_id': 'CL-004', 'client_name': 'Makro', 'client_type': 'Wholesale'}
    ]
    df_clients = pd.DataFrame(clients)
    df_clients.to_csv(PROJECT_ROOT / 'data' / 'raw' / 'clients.csv', index=False)

    print("Generated dimension tables (products, plants, clients).")
    return [p['product_id'] for p in products], [p['plant_id'] for p in plants], [c['client_id'] for c in clients]

def generate_sales_data(start_date, end_date, product_ids, plant_ids, client_ids):
    """Generates dirty sales data and saves as CSV."""
    data = []
    current_date = start_date
    while current_date <= end_date:
        for _ in range(random.randint(5, 15)):
            if random.random() > 0.8:
                date_str = current_date.strftime("%m/%d/%Y")
            else:
                date_str = current_date.strftime("%d-%m-%Y")

            data.append({
                'order_id': f"ORD-{random.randint(1000, 9999)}",
                'order_date': date_str,
                'product_id': random.choice(product_ids),
                'plant_id': random.choice(plant_ids),
                'client_id': random.choice(client_ids),
                'quantity': random.randint(10, 500),
                'unit_price': round(random.uniform(5.0, 50.0), 2)
            })
        current_date += timedelta(days=1)

    df = pd.DataFrame(data)

    # Inject anomalies
    df.loc[df.sample(frac=0.05).index, 'quantity'] = np.nan
    df.loc[df.sample(frac=0.03).index, 'unit_price'] = -15.50

    # Duplicate rows
    df = pd.concat([df, df.sample(frac=0.02)])

    df.to_csv(PROJECT_ROOT / 'data' / 'raw' / 'sales_data.csv', index=False)
    print("Generated sales_data.csv with anomalies.")

def generate_production_data(start_date, end_date, product_ids, plant_ids):
    """Generates dirty production data and saves as Excel."""
    data = []
    current_date = start_date
    while current_date <= end_date:
        for _ in range(random.randint(3, 8)):
            # Pick a valid plant_id, but sometimes inject bad plant_id to test cleaning if we wanted to
            # But let's keep it simple for the star schema fix
            plant_id = random.choice(plant_ids)
            
            data.append({
                'production_date': current_date.strftime("%Y-%m-%d"),
                'plant_id': plant_id,
                'product_id': random.choice(product_ids),
                'manufactured_qty': random.randint(1000, 5000),
                'defect_qty': random.randint(10, 200)
            })
        current_date += timedelta(days=1)

    df = pd.DataFrame(data)

    # Inject anomalies
    df['manufactured_qty'] = df['manufactured_qty'].astype(object)
    df.loc[df.sample(frac=0.02).index, 'manufactured_qty'] = "ERROR"

    df.to_excel(PROJECT_ROOT / 'data' / 'raw' / 'production_data.xlsx', index=False)
    print("Generated production_data.xlsx with anomalies.")

if __name__ == "__main__":
    print("Starting data generation for AndinaFoods...")
    start = datetime(2023, 1, 1)
    end = datetime(2023, 6, 30)

    create_raw_data_folders()
    p_ids, pl_ids, c_ids = generate_dimensions()
    generate_sales_data(start, end, p_ids, pl_ids, c_ids)
    generate_production_data(start, end, p_ids, pl_ids)
    print("Data generation complete. Ready for engineering.")
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os


def create_raw_data_folders():
    """Ensure the raw data directory exists."""
    #Current working directory
    os.makedirs('data/raw', exist_ok=True)
    print("Folder 'data/raw' is ready.")


def generate_sales_data(start_date, end_date):
    """Generates dirty sales data and saves as CSV."""
    products = ['Aceite Premium', 'Fideos Largos', 'Detergente Industrial', 'Salsa de Tomate']
    clients = ['Supermercados Peruanos', 'Cencosud', 'Bodegas Unidas', 'Makro']

    data = []
    current_date = start_date
    while current_date <= end_date:
        for _ in range(random.randint(5, 15)):
            # Dirty dates: sometimes MM/DD/YYYY, sometimes DD-MM-YYYY
            if random.random() > 0.8:
                date_str = current_date.strftime("%m/%d/%Y")
            else:
                date_str = current_date.strftime("%d-%m-%Y")

            data.append({
                'order_id': f"ORD-{random.randint(1000, 9999)}",
                'order_date': date_str,
                'product_name': random.choice(products),
                'quantity': random.randint(10, 500),
                'unit_price': round(random.uniform(5.0, 50.0), 2),
                'client': random.choice(clients)
            })
        current_date += timedelta(days=1)

    df = pd.DataFrame(data)

    # Inject dirtiness
    df.loc[df.sample(frac=0.05).index, 'quantity'] = np.nan  # Missing quantities
    df.loc[df.sample(frac=0.03).index, 'unit_price'] = -15.50  # Negative prices

    # Duplicate some rows
    df = pd.concat([df, df.sample(frac=0.02)])

    df.to_csv('data/raw/sales_data.csv', index=False)
    print("Generated sales_data.csv with anomalies.")


def generate_production_data(start_date, end_date):
    """Generates dirty production data and saves as Excel."""
    products = ['Aceite Premium', 'Fideos Largos', 'Detergente Industrial', 'Salsa de Tomate']
    plants = ['Lima', 'Arequipa', 'Trujillo']

    data = []
    current_date = start_date
    while current_date <= end_date:
        for _ in range(random.randint(3, 8)):
            # Dirty plant names (extra spaces, lowercase)
            plant = random.choice(plants)
            if random.random() > 0.7:
                plant = f" {plant.upper()} "
            elif random.random() > 0.8:
                plant = plant.lower()

            data.append({
                'production_date': current_date.strftime("%Y-%m-%d"),
                'plant_location': plant,
                'product': random.choice(products),
                'manufactured_qty': random.randint(1000, 5000),
                'defect_qty': random.randint(10, 200)
            })
        current_date += timedelta(days=1)

    df = pd.DataFrame(data)

    # Inject dirtiness: Strings in numeric columns
    df['manufactured_qty'] = df['manufactured_qty'].astype(object)  # Forzamos a que acepte texto
    df.loc[df.sample(frac=0.02).index, 'manufactured_qty'] = "ERROR"

    df.to_excel('data/raw/production_data.xlsx', index=False)
    print("Generated production_data.xlsx with anomalies.")


if __name__ == "__main__":
    print("Starting data generation for AndinaFoods...")
    start = datetime(2023, 1, 1)
    end = datetime(2023, 6, 30)

    create_raw_data_folders()
    generate_sales_data(start, end)
    generate_production_data(start, end)
    print("Data generation complete. Ready for engineering.")
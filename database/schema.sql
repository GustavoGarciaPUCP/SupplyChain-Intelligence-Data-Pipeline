-- database/schema.sql

DROP VIEW IF EXISTS vw_monthly_sales_ranking;
DROP VIEW IF EXISTS vw_plant_performance;

DROP TABLE IF EXISTS sales CASCADE;
DROP TABLE IF EXISTS production CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS plants CASCADE;
DROP TABLE IF EXISTS clients CASCADE;

-- Dimension Table: Plants
CREATE TABLE plants (
    plant_id VARCHAR(20) PRIMARY KEY,
    plant_location VARCHAR(50) NOT NULL,
    region VARCHAR(50) NOT NULL
);

-- Dimension Table: Clients
CREATE TABLE clients (
    client_id VARCHAR(20) PRIMARY KEY,
    client_name VARCHAR(100) NOT NULL,
    client_type VARCHAR(50) NOT NULL
);

-- Dimension Table: Products
CREATE TABLE products (
    product_id VARCHAR(20) PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL
);

-- Fact Table: Sales
CREATE TABLE sales (
    sale_id SERIAL PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    order_date DATE NOT NULL,
    product_id VARCHAR(20) NOT NULL REFERENCES products(product_id),
    plant_id VARCHAR(20) NOT NULL REFERENCES plants(plant_id),
    client_id VARCHAR(20) NOT NULL REFERENCES clients(client_id),
    quantity INTEGER NOT NULL CHECK (quantity >= 0),
    unit_price DECIMAL(10, 2) NOT NULL CHECK (unit_price >= 0)
);

-- Fact Table: Production
CREATE TABLE production (
    production_id SERIAL PRIMARY KEY,
    production_date DATE NOT NULL,
    plant_id VARCHAR(20) NOT NULL REFERENCES plants(plant_id),
    product_id VARCHAR(20) NOT NULL REFERENCES products(product_id),
    manufactured_qty INTEGER NOT NULL CHECK (manufactured_qty >= 0),
    defect_qty INTEGER NOT NULL CHECK (defect_qty >= 0 AND defect_qty <= manufactured_qty)
);

-- Indexes for optimal join and filtering performance
CREATE INDEX idx_sales_date ON sales(order_date);
CREATE INDEX idx_sales_product ON sales(product_id);
CREATE INDEX idx_sales_plant ON sales(plant_id);
CREATE INDEX idx_sales_client ON sales(client_id);
CREATE INDEX idx_production_date ON production(production_date);
CREATE INDEX idx_production_product ON production(product_id);
CREATE INDEX idx_production_plant ON production(plant_id);
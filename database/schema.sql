-- database/schema.sql

DROP VIEW IF EXISTS vw_monthly_sales_ranking;
DROP VIEW IF EXISTS vw_plant_performance;

DROP TABLE IF EXISTS sales CASCADE;
DROP TABLE IF EXISTS production CASCADE;
DROP TABLE IF EXISTS products CASCADE;

-- Dimension Table
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
    quantity INTEGER NOT NULL CHECK (quantity >= 0),
    unit_price DECIMAL(10, 2) NOT NULL CHECK (unit_price >= 0),
    client VARCHAR(100) NOT NULL
);

-- Fact Table: Production
CREATE TABLE production (
    production_id SERIAL PRIMARY KEY,
    production_date DATE NOT NULL,
    plant_location VARCHAR(50) NOT NULL,
    product_id VARCHAR(20) NOT NULL REFERENCES products(product_id),
    manufactured_qty INTEGER NOT NULL CHECK (manufactured_qty >= 0),
    defect_qty INTEGER NOT NULL CHECK (defect_qty >= 0 AND defect_qty <= manufactured_qty)
);

-- Indexes for optimal join and filtering performance
CREATE INDEX idx_sales_date ON sales(order_date);
CREATE INDEX idx_sales_product ON sales(product_id);
CREATE INDEX idx_production_date ON production(production_date);
CREATE INDEX idx_production_product ON production(product_id);
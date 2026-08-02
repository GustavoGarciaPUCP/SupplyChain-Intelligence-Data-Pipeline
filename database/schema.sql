-- database/schema.sql

-- Drop tables if they already exist (useful for resetting the database during tests)
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS production;

-- Create sales table
CREATE TABLE sales (
    sale_id SERIAL PRIMARY KEY,
    order_id VARCHAR(50),
    order_date DATE,
    product_name VARCHAR(100),
    quantity INTEGER,
    unit_price DECIMAL(10, 2),
    client VARCHAR(100)
);

-- Create production table
CREATE TABLE production (
    production_id SERIAL PRIMARY KEY,
    production_date DATE,
    plant_location VARCHAR(50),
    product VARCHAR(100),
    manufactured_qty INTEGER,
    defect_qty INTEGER
);
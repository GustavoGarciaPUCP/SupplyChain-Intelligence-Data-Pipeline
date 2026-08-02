-- View 1: Monthly Sales Ranking using CTEs and Window Functions
CREATE OR REPLACE VIEW vw_monthly_sales_ranking AS
WITH monthly_sales AS (
    SELECT
        DATE_TRUNC('month', order_date)::DATE AS sales_month,
        product_name,
        SUM(quantity * unit_price) AS total_revenue,
        SUM(quantity) AS total_units_sold
    FROM sales
    GROUP BY DATE_TRUNC('month', order_date), product_name
)
SELECT
    sales_month,
    product_name,
    total_revenue,
    total_units_sold,
    RANK() OVER (PARTITION BY sales_month ORDER BY total_revenue DESC) AS revenue_rank
FROM monthly_sales;


-- View 2: Plant Production and Defect Rate
CREATE OR REPLACE VIEW vw_plant_performance AS
SELECT
    DATE_TRUNC('month', production_date)::DATE AS production_month,
    plant_location,
    SUM(manufactured_qty) AS total_manufactured,
    SUM(defect_qty) AS total_defects,
    ROUND((SUM(defect_qty)::DECIMAL / NULLIF(SUM(manufactured_qty), 0)) * 100, 2) AS defect_rate_percentage
FROM production
GROUP BY DATE_TRUNC('month', production_date), plant_location;
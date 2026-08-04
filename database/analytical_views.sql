-- database/analytical_views.sql

-- View 1: Monthly Sales Ranking
CREATE OR REPLACE VIEW vw_monthly_sales_ranking AS
WITH monthly_sales AS (
    SELECT
        DATE_TRUNC('month', s.order_date)::DATE AS sales_month,
        p.product_id,
        p.product_name,
        SUM(s.quantity * s.unit_price) AS total_revenue,
        SUM(s.quantity) AS total_units_sold
    FROM sales s
    JOIN products p ON s.product_id = p.product_id
    GROUP BY DATE_TRUNC('month', s.order_date), p.product_id, p.product_name
)
SELECT
    sales_month,
    product_id,
    product_name,
    total_revenue,
    total_units_sold,
    RANK() OVER (PARTITION BY sales_month ORDER BY total_revenue DESC) AS revenue_rank
FROM monthly_sales;

-- View 2: Plant Production and Defect Rate
CREATE OR REPLACE VIEW vw_plant_performance AS
SELECT
    DATE_TRUNC('month', pr.production_date)::DATE AS production_month,
    p.product_id,
    p.product_name,
    pr.plant_location,
    SUM(pr.manufactured_qty) AS total_manufactured,
    SUM(pr.defect_qty) AS total_defects,
    ROUND((SUM(pr.defect_qty)::DECIMAL / NULLIF(SUM(pr.manufactured_qty), 0)) * 100, 2) AS defect_rate_percentage
FROM production pr
JOIN products p ON pr.product_id = p.product_id
GROUP BY DATE_TRUNC('month', pr.production_date), p.product_id, p.product_name, pr.plant_location;
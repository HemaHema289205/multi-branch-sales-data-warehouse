-- ============================================================
-- validation_queries.sql
-- PHASE 10: DATA QUALITY & VALIDATION
-- ============================================================
-- 12 checks confirming the warehouse data is complete, correctly
-- linked, and correctly calculated. Every "count" query should
-- return 0 — any non-zero result means something needs attention.
-- ============================================================

USE multi_branch_sales_dw;

-- 1. Total records loaded — sanity check against your ETL's printed stats.
SELECT COUNT(*) AS total_sales_records
FROM fact_sales;

-- 2. Total net sales stored — compare against data_transformation.py's
-- printed "Total Net Sales" to confirm nothing was lost in loading.
SELECT ROUND(SUM(net_sales), 2) AS warehouse_total_sales
FROM fact_sales;

-- 3. Invalid product references (should be 0).
SELECT COUNT(*) AS invalid_product_references
FROM fact_sales f
LEFT JOIN dim_product p ON f.product_key = p.product_key
WHERE p.product_key IS NULL;

-- 4. Invalid branch references (should be 0).
SELECT COUNT(*) AS invalid_branch_references
FROM fact_sales f
LEFT JOIN dim_branch b ON f.branch_key = b.branch_key
WHERE b.branch_key IS NULL;

-- 5. Invalid customer references (should be 0).
SELECT COUNT(*) AS invalid_customer_references
FROM fact_sales f
LEFT JOIN dim_customer c ON f.customer_key = c.customer_key
WHERE c.customer_key IS NULL;

-- 6. Invalid date references (should be 0).
SELECT COUNT(*) AS invalid_date_references
FROM fact_sales f
LEFT JOIN dim_date d ON f.date_key = d.date_key
WHERE d.date_key IS NULL;

-- 7. Duplicate transactions (should return no rows).
SELECT transaction_id, COUNT(*) AS transaction_count
FROM fact_sales
GROUP BY transaction_id
HAVING COUNT(*) > 1;

-- 8. Missing values in key fact-table columns (every column should be 0).
SELECT
    SUM(date_key IS NULL)      AS missing_date,
    SUM(product_key IS NULL)   AS missing_product,
    SUM(branch_key IS NULL)    AS missing_branch,
    SUM(customer_key IS NULL)  AS missing_customer,
    SUM(transaction_id IS NULL) AS missing_transaction,
    SUM(quantity IS NULL)      AS missing_quantity,
    SUM(unit_price IS NULL)    AS missing_unit_price,
    SUM(net_sales IS NULL)     AS missing_net_sales,
    SUM(profit IS NULL)        AS missing_profit
FROM fact_sales;

-- 9. Invalid quantities: should never be <= 0 after Phase 3 cleaning.
SELECT COUNT(*) AS invalid_quantity_records
FROM fact_sales
WHERE quantity <= 0;

-- 10. Invalid monetary values: unit price / gross / net sales should be positive.
SELECT COUNT(*) AS invalid_sales_value_records
FROM fact_sales
WHERE unit_price <= 0 OR gross_sales <= 0 OR net_sales <= 0;

-- 11. Profit recalculation check: profit must equal net_sales - cost
-- for every single row (should be 0).
SELECT COUNT(*) AS incorrect_profit_records
FROM fact_sales
WHERE ROUND(profit, 2) <> ROUND(net_sales - cost, 2);

-- 12. Final validation summary — the headline numbers for your report.
SELECT
    COUNT(*) AS total_records,
    ROUND(SUM(net_sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    SUM(quantity) AS total_quantity
FROM fact_sales;

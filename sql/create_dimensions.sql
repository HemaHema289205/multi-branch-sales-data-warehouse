-- ============================================================
-- create_dimensions.sql
-- PHASE 5: MYSQL DATA WAREHOUSE — DIMENSION TABLES
-- ============================================================
-- Creates the 4 dimension tables of the star schema:
--   dim_date, dim_product, dim_branch, dim_customer
--
-- Each dimension has:
--   - a surrogate key (auto-increment integer, used by fact_sales)
--   - a natural/business key from the source data (kept UNIQUE so we
--     never insert the same real-world date/product/branch/customer twice)
--
-- Run AFTER create_database.sql:
--   mysql -u root -p multi_branch_sales_dw < sql/create_dimensions.sql
-- ============================================================

USE multi_branch_sales_dw;

-- ------------------------------------------------------------
-- DIM_DATE
-- Surrogate key = date_key, formatted as YYYYMMDD (e.g. 20240315)
-- so it sorts naturally and is easy to generate in Python without
-- needing a lookup.
-- One row = one calendar day. Loaded once for the full date range
-- your data covers (Phase 7 ETL generates these rows in Python).
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_date (
    date_key        INT PRIMARY KEY,           -- e.g. 20240315
    full_date       DATE        NOT NULL,
    day             TINYINT     NOT NULL,       -- 1-31
    day_name        VARCHAR(10) NOT NULL,       -- 'Monday'
    month           TINYINT     NOT NULL,       -- 1-12
    month_name      VARCHAR(10) NOT NULL,       -- 'March'
    quarter         TINYINT     NOT NULL,       -- 1-4
    year            SMALLINT    NOT NULL,
    is_weekend      TINYINT(1)  NOT NULL DEFAULT 0,
    UNIQUE KEY uq_dim_date_full_date (full_date)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- DIM_PRODUCT
-- One row = one distinct product.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_product (
    product_key     INT AUTO_INCREMENT PRIMARY KEY,
    product_id      VARCHAR(10)  NOT NULL,      -- e.g. 'P001' (business key from source)
    product_name    VARCHAR(150) NOT NULL,
    category        VARCHAR(50)  NOT NULL,
    UNIQUE KEY uq_dim_product_id (product_id)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- DIM_BRANCH
-- One row = one store branch. "branch_name" doubles as the city
-- name in this dataset (each branch is named after its city).
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_branch (
    branch_key      INT AUTO_INCREMENT PRIMARY KEY,
    branch_id       VARCHAR(10) NOT NULL,       -- e.g. 'BR01'
    branch_name     VARCHAR(100) NOT NULL,
    city            VARCHAR(100) NOT NULL,
    region          VARCHAR(100) NOT NULL,
    UNIQUE KEY uq_dim_branch_id (branch_id)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- DIM_CUSTOMER
-- One row = one distinct customer.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_key      INT AUTO_INCREMENT PRIMARY KEY,
    customer_id       VARCHAR(10)  NOT NULL,    -- e.g. 'CUST00123'
    customer_name     VARCHAR(150) NOT NULL,
    customer_segment  VARCHAR(30)  NOT NULL,
    UNIQUE KEY uq_dim_customer_id (customer_id)
) ENGINE=InnoDB;

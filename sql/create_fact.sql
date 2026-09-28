-- ============================================================
-- create_fact.sql
-- PHASE 5: MYSQL DATA WAREHOUSE — FACT TABLE
-- ============================================================
-- GRAIN OF FACT_SALES:
--   One row = one product sold in one transaction at one branch,
--   on one date, to one customer.
--   (Since Transaction_ID in the source data already represents a
--   single product line, transaction_id is effectively 1:1 with
--   sales_key here — there is no separate "order header" table.)
--
-- Run AFTER create_dimensions.sql:
--   mysql -u root -p multi_branch_sales_dw < sql/create_fact.sql
-- ============================================================

USE multi_branch_sales_dw;

CREATE TABLE IF NOT EXISTS fact_sales (
    sales_key           BIGINT AUTO_INCREMENT PRIMARY KEY,

    -- Foreign keys to every dimension (this is what makes it a "star")
    date_key             INT           NOT NULL,
    product_key           INT          NOT NULL,
    branch_key            INT          NOT NULL,
    customer_key          INT          NOT NULL,

    -- Business/natural key, kept for traceability back to the source CSV
    transaction_id         VARCHAR(20) NOT NULL,

    -- Degenerate dimension: low-cardinality attribute stored directly
    -- on the fact table instead of its own dimension table, since it
    -- has no extra attributes of its own worth modelling separately.
    payment_method          VARCHAR(20) NOT NULL,

    -- Measures (the numbers analysts will aggregate/sum/average)
    quantity                INT           NOT NULL,
    unit_price               DECIMAL(10,2) NOT NULL,
    discount                  DECIMAL(5,4)  NOT NULL,    -- fraction, e.g. 0.1000 = 10%
    gross_sales                 DECIMAL(12,2) NOT NULL,
    discount_amount              DECIMAL(12,2) NOT NULL,
    net_sales                     DECIMAL(12,2) NOT NULL,
    cost                            DECIMAL(12,2) NOT NULL,
    profit                           DECIMAL(12,2) NOT NULL,

    UNIQUE KEY uq_fact_transaction_id (transaction_id),

    CONSTRAINT fk_fact_date     FOREIGN KEY (date_key)     REFERENCES dim_date(date_key),
    CONSTRAINT fk_fact_product  FOREIGN KEY (product_key)  REFERENCES dim_product(product_key),
    CONSTRAINT fk_fact_branch   FOREIGN KEY (branch_key)   REFERENCES dim_branch(branch_key),
    CONSTRAINT fk_fact_customer FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key),

    -- Indexes on FK columns speed up every JOIN-heavy analytical query
    -- (SQL analytics in Phase 8, Power BI in Phase 11)
    INDEX idx_fact_date     (date_key),
    INDEX idx_fact_product  (product_key),
    INDEX idx_fact_branch   (branch_key),
    INDEX idx_fact_customer (customer_key)
) ENGINE=InnoDB;

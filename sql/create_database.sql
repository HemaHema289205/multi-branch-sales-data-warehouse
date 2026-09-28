-- ============================================================
-- create_database.sql
-- PHASE 5: MYSQL DATA WAREHOUSE
-- ============================================================
-- Creates the warehouse database. Run this FIRST, before
-- create_dimensions.sql and create_fact.sql.
--
-- Run with:
--   mysql -u root -p < sql/create_database.sql
-- or paste into MySQL Workbench / the MySQL command line.
-- ============================================================

CREATE DATABASE IF NOT EXISTS multi_branch_sales_dw
    CHARACTER SET utf8mb4
    
    COLLATE utf8mb4_unicode_ci;

USE multi_branch_sales_dw;



# Multi-Branch Sales Data Warehouse and Business Intelligence Dashboard

# An Intelligent System to Consolidate Multi-Branch Sales Data for Trend Analysis

## Overview

A B.Tech mini project (Big Data Analytics, Data Warehousing & Visualization) that
builds a complete, working data pipeline for a retail chain with branches across
Andhra Pradesh and Telangana. Raw point-of-sale transaction exports are cleaned,
transformed, loaded into a MySQL star-schema data warehouse, analyzed with SQL,
and visualized in a 4-page Power BI dashboard built for a regional manager.

## Problem

Retail chains with multiple branches generate sales data in disconnected,
inconsistent CSV exports — one per branch, with no shared structure for
cross-branch trend analysis, profitability comparison, or seasonal forecasting.

## Solution

This project builds an end-to-end pipeline that:
1. Generates/ingests realistic multi-branch POS data
2. Cleans and validates it with Python/Pandas
3. Calculates business metrics (profit, margin, discount impact)
4. Loads it into a MySQL star-schema warehouse
5. Answers 20+ business questions with SQL, including OLAP-style operations
6. Presents it all in an interactive Power BI dashboard

## Features

- Synthetic dataset generator producing ~40,000 realistic transactions with
  built-in seasonality, branch performance variation, and intentional data
  messiness (for a genuine cleaning exercise)
- Full data-quality report (before/after cleaning), with rejected records
  tracked separately rather than silently dropped
- Star-schema MySQL warehouse (1 fact table, 4 dimensions)
- Idempotent Python ETL pipeline (safe to re-run without creating duplicates)
- 20 SQL analytics queries + 4 OLAP operations (roll-up, drill-down, slice, dice)
- 12 data-validation queries (referential integrity, duplicates, profit
  recalculation checks)
- 4-page Power BI dashboard: Executive Overview, Branch Performance, Product
  Analysis, Trend Analysis — with 6 DAX measures, cross-filtering slicers, and
  time-intelligence (YoY growth)

## Architecture

```
MULTIPLE BRANCH SALES DATA (5 branches: Eluru, Vijayawada, Rajahmundry,
                              Visakhapatnam, Hyderabad)
          |
     RAW CSV FILES (data/raw/)
          |
   PYTHON + PANDAS (generate_data.py)
          |
DATA CLEANING & TRANSFORMATION (data_cleaning.py, data_transformation.py)
          |
       MYSQL (etl_pipeline.py)
          |
   STAR SCHEMA WAREHOUSE (dim_date, dim_product, dim_branch, dim_customer, fact_sales)
          |
   OLAP / SQL ANALYSIS (sql/analysis_queries.sql, sql/validation_queries.sql)
          |
      POWER BI (4-page dashboard)
          |
REGIONAL MANAGER DASHBOARD
```

## Technologies

| Layer | Technology |
|---|---|
| Data | CSV |
| Processing | Python, Pandas |
| Database / Warehouse | MySQL (star schema) |
| Querying | SQL |
| Visualization | Power BI |
| Dev environment | VS Code, MySQL Workbench |

## Dataset

~40,000 synthetic transactions (2 years, Jan 2023 - Dec 2024) across 5 branches,
22 products in 5 categories, 2,000 customers. Generated with `python/generate_data.py`,
seeded for reproducibility (seed=42), with realistic seasonality (festive-season
spike, summer appliance spike) and intentional data-quality issues for the
cleaning phase to address.

## Star Schema

**Grain of `fact_sales`:** one row = one product sold in one transaction.

```
                    DIM_DATE
                       |
DIM_PRODUCT ---- FACT_SALES ---- DIM_BRANCH
                       |
                 DIM_CUSTOMER
```

- `dim_date` — surrogate key `date_key` (YYYYMMDD), full_date, day, day_name,
  month, month_name, quarter, year, is_weekend
- `dim_product` — product_key, product_id, product_name, category
- `dim_branch` — branch_key, branch_id, branch_name, city, region
- `dim_customer` — customer_key, customer_id, customer_name, customer_segment
- `fact_sales` — 4 foreign keys, transaction_id, payment_method (degenerate
  dimension), and measures: quantity, unit_price, discount, gross_sales,
  discount_amount, net_sales, cost, profit

## ETL Process

`python/etl_pipeline.py` reads `data/processed/transformed_sales_data.csv` and:
1. Loads all 4 dimensions (using `INSERT IGNORE` / `ON DUPLICATE KEY UPDATE`,
   so re-running the script is always safe)
2. Reads the dimension tables back to retrieve MySQL-generated surrogate keys
3. Merges those keys onto every transaction row
4. Bulk-inserts `fact_sales` in batches of 5,000

## SQL Analytics

`sql/analysis_queries.sql` — 20 business queries: totals, branch/region/
product/category breakdowns, monthly/yearly trends, top/bottom performers,
payment method mix, discount analysis, and year-over-year comparison —
plus 4 OLAP-style operations (roll-up, drill-down, slice, dice) demonstrated
using the relational warehouse.

`sql/validation_queries.sql` — 12 data-quality checks: record counts,
referential integrity across all 4 foreign keys, duplicate detection, missing
values, and a recalculation check confirming `profit = net_sales - cost`
for every row.

## Power BI Dashboard

4 pages, built on a live MySQL connection with all 5 tables imported and
`dim_date` marked as the official Date Table:

1. **Executive Overview** — 5 KPI cards, monthly sales trend, sales by branch,
   sales by category, 4 cross-page slicers (date, region, branch, category)
2. **Branch Performance** — branch comparison (sales vs profit), monthly
   trend per branch, totals table, branch ranking
3. **Product Analysis** — Top 10 products by sales, Top 10 by profit,
   category treemap, full product table
4. **Trend Analysis** — quarterly trend, yearly trend, YoY growth %,
   regional trend (Andhra Pradesh vs Telangana)

See `powerbi/dashboard_documentation.md` for the full measure list and
page-by-page breakdown.

## Project Structure

```
multi_branch_sales_dw/
├── data/
│   ├── raw/            # branch CSVs (generated, not committed)
│   └── processed/       # cleaned + transformed CSVs (generated, not committed)
├── python/
│   ├── generate_data.py
│   ├── data_cleaning.py
│   ├── data_transformation.py
│   └── etl_pipeline.py
├── sql/
│   ├── create_database.sql
│   ├── create_dimensions.sql
│   ├── create_fact.sql
│   ├── analysis_queries.sql
│   └── validation_queries.sql
├── powerbi/
│   └── dashboard_documentation.md
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Installation

1. Install Python 3.11+, MySQL Server (or MySQL Workbench), and Power BI Desktop.
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in your MySQL password.

## How to Run

```
python python\generate_data.py
python python\data_cleaning.py
python python\data_transformation.py
mysql -u root -p < sql\create_database.sql
mysql -u root -p multi_branch_sales_dw < sql\create_dimensions.sql
mysql -u root -p multi_branch_sales_dw < sql\create_fact.sql
python python\etl_pipeline.py
```
Then open Power BI Desktop, connect to MySQL (`localhost:3306`,
`multi_branch_sales_dw`), and import all 5 tables.

## Results

- 39,960 clean transaction records loaded (40 rejected for invalid quantity,
  160 duplicates removed)
- Total Sales: ~₹92.9 crore | Total Profit: ~₹17.1 crore | Profit Margin: 18.4%
- Hyderabad is the top-performing branch on both sales and profit
- Flagship Smartphone is the top-selling and top-profit product
- Festive season (Oct-Nov) shows a clear, expected sales spike
- 2024 vs 2023 year-over-year growth: +1.23%

## Future Scope

- Add a proper order-header table to model multi-item transactions
- Automate the ETL pipeline on a schedule (e.g. with Airflow or Task Scheduler)
- Add predictive forecasting (e.g. next-quarter sales) using the historical trend
- Publish the dashboard to Power BI Service for live sharing with branch managers

"""
etl_pipeline.py
-----------------
PHASE 7: ETL PIPELINE (Extract -> Clean/Transform already done -> Load)

WHAT THIS SCRIPT DOES:
  Loads data/processed/transformed_sales_data.csv (output of Phase 4)
  into the MySQL star schema created in Phase 5:

      1. Connect to MySQL using credentials from .env
      2. Build dim_date rows for every unique date in the data and
         INSERT them (skipping dates already loaded)
      3. Build dim_product rows for every unique product and INSERT
      4. Build dim_branch rows for every unique branch and INSERT
      5. Build dim_customer rows for every unique customer and INSERT
      6. Re-read each dimension table back from MySQL to get the
         surrogate keys MySQL just generated (date_key, product_key,
         branch_key, customer_key)
      7. Map every transaction row to its surrogate keys (a simple
         pandas merge) and build the fact_sales rows
      8. Bulk-INSERT fact_sales
      9. Print loading statistics

SAFETY:
  - Every INSERT uses "INSERT IGNORE" or "ON DUPLICATE KEY UPDATE" so
    you can re-run this script safely without creating duplicates.
  - Credentials come from .env (never hard-coded) via python-dotenv.

Run this script from the project root (AFTER data_transformation.py
AND after creating the schema with the 3 SQL scripts):
    python python/etl_pipeline.py
"""

import os
import sys

import mysql.connector
import pandas as pd
from dotenv import load_dotenv

TRANSFORMED_CSV = os.path.join("data", "processed", "transformed_sales_data.csv")


def get_connection():
    """Read credentials from .env and open a MySQL connection.
    Raises a clear, friendly error if .env is missing or connection fails."""
    load_dotenv()
    host = os.getenv("MYSQL_HOST", "localhost")
    port = int(os.getenv("MYSQL_PORT", "3306"))
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD")
    database = os.getenv("MYSQL_DATABASE", "multi_branch_sales_dw")

    if password is None:
        print("ERROR: MYSQL_PASSWORD not found.")
        print("Did you copy .env.example to .env and fill in your password?")
        sys.exit(1)

    try:
        conn = mysql.connector.connect(
            host=host, port=port, user=user, password=password, database=database
        )
        print(f"Connected to MySQL database '{database}' at {host}:{port} as '{user}'.")
        return conn
    except mysql.connector.Error as err:
        print(f"ERROR: Could not connect to MySQL.\n  {err}")
        print("Check: is MySQL running? Is the password in .env correct?")
        sys.exit(1)


# ----------------------------------------------------------------------
# STEP 1: LOAD DIMENSIONS
# ----------------------------------------------------------------------
def load_dim_date(conn, df: pd.DataFrame) -> int:
    dates = pd.to_datetime(df["Transaction_Date"]).dt.date.unique()
    rows = []
    for d in dates:
        d = pd.Timestamp(d)
        rows.append((
            int(d.strftime("%Y%m%d")),   # date_key
            d.date(),                     # full_date
            d.day,
            d.strftime("%A"),             # day_name
            d.month,
            d.strftime("%B"),             # month_name
            (d.month - 1) // 3 + 1,       # quarter
            d.year,
            1 if d.weekday() >= 5 else 0,  # is_weekend
        ))

    sql = """
        INSERT IGNORE INTO dim_date
            (date_key, full_date, day, day_name, month, month_name, quarter, year, is_weekend)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor = conn.cursor()
    cursor.executemany(sql, rows)
    conn.commit()
    cursor.close()
    return len(rows)


def load_dim_product(conn, df: pd.DataFrame) -> int:
    products = df[["Product_ID", "Product_Name", "Category"]].drop_duplicates()
    rows = list(products.itertuples(index=False, name=None))

    sql = """
        INSERT INTO dim_product (product_id, product_name, category)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE product_name = VALUES(product_name), category = VALUES(category)
    """
    cursor = conn.cursor()
    cursor.executemany(sql, rows)
    conn.commit()
    cursor.close()
    return len(rows)


def load_dim_branch(conn, df: pd.DataFrame) -> int:
    branches = df[["Branch_ID", "Branch", "Region"]].drop_duplicates()
    # city == branch name in this dataset (see create_dimensions.sql note)
    rows = [(bid, name, name, region) for bid, name, region in branches.itertuples(index=False, name=None)]

    sql = """
        INSERT INTO dim_branch (branch_id, branch_name, city, region)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE branch_name = VALUES(branch_name), city = VALUES(city), region = VALUES(region)
    """
    cursor = conn.cursor()
    cursor.executemany(sql, rows)
    conn.commit()
    cursor.close()
    return len(rows)


def load_dim_customer(conn, df: pd.DataFrame) -> int:
    customers = df[["Customer_ID", "Customer_Name", "Customer_Segment"]].drop_duplicates()
    rows = list(customers.itertuples(index=False, name=None))

    sql = """
        INSERT INTO dim_customer (customer_id, customer_name, customer_segment)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE customer_name = VALUES(customer_name), customer_segment = VALUES(customer_segment)
    """
    cursor = conn.cursor()
    cursor.executemany(sql, rows)
    conn.commit()
    cursor.close()
    return len(rows)


# ----------------------------------------------------------------------
# STEP 2: RETRIEVE SURROGATE KEYS
# ----------------------------------------------------------------------
def fetch_dim(conn, table: str, key_col: str, business_col: str) -> pd.DataFrame:
    """Read a dimension table back so we can map business keys -> surrogate keys.
    (Uses a plain cursor instead of pandas.read_sql because mysql-connector
    isn't a SQLAlchemy engine and read_sql would print a noisy warning.)"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT {key_col}, {business_col} FROM {table}")
    rows = cursor.fetchall()
    cursor.close()
    return pd.DataFrame(rows, columns=[key_col, business_col])


# ----------------------------------------------------------------------
# STEP 3: BUILD & LOAD FACT_SALES
# ----------------------------------------------------------------------
def load_fact_sales(conn, df: pd.DataFrame) -> int:
    df = df.copy()
    df["date_key"] = pd.to_datetime(df["Transaction_Date"]).dt.strftime("%Y%m%d").astype(int)

    dim_product = fetch_dim(conn, "dim_product", "product_key", "product_id")
    dim_branch = fetch_dim(conn, "dim_branch", "branch_key", "branch_id")
    dim_customer = fetch_dim(conn, "dim_customer", "customer_key", "customer_id")

    df = df.merge(dim_product, left_on="Product_ID", right_on="product_id", how="left")
    df = df.merge(dim_branch, left_on="Branch_ID", right_on="branch_id", how="left")
    df = df.merge(dim_customer, left_on="Customer_ID", right_on="customer_id", how="left")

    # Sanity check: every row must have matched a surrogate key in each dimension.
    missing = df[df[["product_key", "branch_key", "customer_key"]].isna().any(axis=1)]
    if len(missing):
        print(f"WARNING: {len(missing)} rows could not be matched to a dimension key "
              f"and will be skipped. This usually means dim_product/branch/customer "
              f"weren't loaded first — re-run this script.")
        df = df.dropna(subset=["product_key", "branch_key", "customer_key"])

    rows = list(df[[
        "date_key", "product_key", "branch_key", "customer_key",
        "Transaction_ID", "Payment_Method", "Quantity", "Unit_Price", "Discount",
        "Gross_Sales", "Discount_Amount", "Net_Sales", "Cost", "Profit",
    ]].itertuples(index=False, name=None))

    sql = """
        INSERT IGNORE INTO fact_sales
            (date_key, product_key, branch_key, customer_key, transaction_id,
             payment_method, quantity, unit_price, discount,
             gross_sales, discount_amount, net_sales, cost, profit)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor = conn.cursor()
    # Insert in batches to keep memory/roundtrips sane for large datasets
    batch_size = 5000
    inserted = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        cursor.executemany(sql, batch)
        conn.commit()
        inserted += len(batch)
        print(f"  Inserted {inserted:,} / {len(rows):,} fact rows...")
    cursor.close()
    return len(rows)


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
def main():
    print("=" * 60)
    print("PHASE 7 — ETL PIPELINE (Load into MySQL)")
    print("=" * 60)

    if not os.path.exists(TRANSFORMED_CSV):
        print(f"ERROR: {TRANSFORMED_CSV} not found. Run data_transformation.py first.")
        sys.exit(1)

    df = pd.read_csv(TRANSFORMED_CSV)
    print(f"Loaded {len(df):,} transformed records from {TRANSFORMED_CSV}")

    conn = get_connection()

    try:
        print("\n[1/5] Loading dim_date...")
        n_dates = load_dim_date(conn, df)
        print(f"  {n_dates:,} unique dates processed.")

        print("\n[2/5] Loading dim_product...")
        n_products = load_dim_product(conn, df)
        print(f"  {n_products:,} unique products processed.")

        print("\n[3/5] Loading dim_branch...")
        n_branches = load_dim_branch(conn, df)
        print(f"  {n_branches:,} unique branches processed.")

        print("\n[4/5] Loading dim_customer...")
        n_customers = load_dim_customer(conn, df)
        print(f"  {n_customers:,} unique customers processed.")

        print("\n[5/5] Loading fact_sales...")
        n_facts = load_fact_sales(conn, df)

        print("\n" + "-" * 60)
        print("LOADING STATISTICS")
        print("-" * 60)
        print(f"  Date records loaded:     {n_dates:,}")
        print(f"  Product records loaded:  {n_products:,}")
        print(f"  Branch records loaded:   {n_branches:,}")
        print(f"  Customer records loaded: {n_customers:,}")
        print(f"  Fact records loaded:     {n_facts:,}")
        print("-" * 60)
        print("\nDone. Next step: Phase 8 — SQL Analytics queries.")

    except mysql.connector.Error as err:
        print(f"\nERROR during load: {err}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()

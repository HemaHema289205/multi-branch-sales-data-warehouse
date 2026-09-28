"""
generate_data.py
-----------------
Generates a realistic, synthetic multi-branch retail sales dataset for the
"Intelligent System to Consolidate Multi-Branch Sales Data for Trend Analysis"
mini project.

WHAT THIS SCRIPT DOES:
  1. Defines 5 branches (with region + city) that behave differently
     (some are high-performing, some low-performing).
  2. Defines a product catalog across 5 categories with realistic prices.
  3. Generates ~2,000 customers.
  4. Generates ~40,000 sales transactions spread across 2 years, with:
       - seasonal spikes (festive season, summer AC/appliance boost)
       - weekday vs weekend variation
       - branch-level performance differences
       - category-level popularity differences
  5. Writes ONE CSV FILE PER BRANCH into data/raw/, e.g.:
       data/raw/branch_1_eluru_sales.csv
       data/raw/branch_2_vijayawada_sales.csv
       ...

Run this script from the project root:
    python python/generate_data.py

Output:
    5 CSV files inside data/raw/
"""

import os
import random
import uuid
from datetime import date, timedelta

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------
# REPRODUCIBILITY
# We fix the random seed so that every time you run this script you get
# the SAME dataset. This makes debugging and grading easier.
# ----------------------------------------------------------------------
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# ----------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------

# Where raw CSVs will be written. Path is relative to the project root,
# so make sure you run this script from multi_branch_sales_dw/
RAW_DATA_DIR = os.path.join("data", "raw")

# Roughly how many transactions to generate in total across ALL branches.
TARGET_TOTAL_TRANSACTIONS = 40000

# Date range: 2 years of history
START_DATE = date(2023, 1, 1)
END_DATE = date(2024, 12, 31)

# ----------------------------------------------------------------------
# BRANCH DEFINITIONS
# "weight" controls how much of the total transaction volume a branch
# gets -> this is what creates "high-sales" and "low-sales" branches.
# ----------------------------------------------------------------------
BRANCHES = [
    {"branch_id": "BR01", "branch_name": "Eluru",         "region": "Andhra Pradesh", "weight": 0.15},
    {"branch_id": "BR02", "branch_name": "Vijayawada",    "region": "Andhra Pradesh", "weight": 0.25},
    {"branch_id": "BR03", "branch_name": "Rajahmundry",   "region": "Andhra Pradesh", "weight": 0.10},
    {"branch_id": "BR04", "branch_name": "Visakhapatnam", "region": "Andhra Pradesh", "weight": 0.20},
    {"branch_id": "BR05", "branch_name": "Hyderabad",     "region": "Telangana",      "weight": 0.30},
]

# ----------------------------------------------------------------------
# PRODUCT CATALOG
# Each product has: category, name, unit_price range, cost ratio (used
# later in Phase 4 to compute profit), and a "seasonal_boost_months" list
# that increases its sales probability in certain months.
# ----------------------------------------------------------------------
PRODUCT_CATALOG = [
    # Mobile
    {"category": "Mobile", "product_name": "Budget Smartphone 4G",    "price_range": (8000, 14000),   "cost_ratio": 0.80, "boost_months": [10, 11]},
    {"category": "Mobile", "product_name": "Mid-range Smartphone 5G", "price_range": (15000, 28000),  "cost_ratio": 0.78, "boost_months": [10, 11]},
    {"category": "Mobile", "product_name": "Flagship Smartphone",     "price_range": (45000, 90000),  "cost_ratio": 0.75, "boost_months": [10, 11]},
    {"category": "Mobile", "product_name": "Wireless Earbuds",        "price_range": (1500, 6000),    "cost_ratio": 0.55, "boost_months": [10, 11, 12]},

    # Laptop
    {"category": "Laptop", "product_name": "Entry Laptop i3",         "price_range": (28000, 38000),  "cost_ratio": 0.82, "boost_months": [6, 7]},
    {"category": "Laptop", "product_name": "Business Laptop i5",      "price_range": (42000, 60000),  "cost_ratio": 0.80, "boost_months": [6, 7]},
    {"category": "Laptop", "product_name": "Gaming Laptop i7",        "price_range": (75000, 130000), "cost_ratio": 0.78, "boost_months": [10, 11]},
    {"category": "Laptop", "product_name": "Ultrabook Thin & Light",  "price_range": (55000, 95000),  "cost_ratio": 0.79, "boost_months": [6, 7]},

    # Accessories
    {"category": "Accessories", "product_name": "Laptop Bag",         "price_range": (600, 2000),     "cost_ratio": 0.45, "boost_months": [6, 7]},
    {"category": "Accessories", "product_name": "Wireless Mouse",     "price_range": (300, 1500),     "cost_ratio": 0.40, "boost_months": []},
    {"category": "Accessories", "product_name": "Bluetooth Speaker",  "price_range": (1000, 5000),    "cost_ratio": 0.50, "boost_months": [10, 11, 12]},
    {"category": "Accessories", "product_name": "Mobile Charger",     "price_range": (300, 1800),     "cost_ratio": 0.42, "boost_months": []},
    {"category": "Accessories", "product_name": "Power Bank",         "price_range": (800, 2500),     "cost_ratio": 0.48, "boost_months": []},

    # Home Appliances
    {"category": "Home Appliances", "product_name": "Split AC 1.5 Ton",     "price_range": (32000, 48000), "cost_ratio": 0.83, "boost_months": [3, 4, 5]},
    {"category": "Home Appliances", "product_name": "Refrigerator 300L",    "price_range": (25000, 42000), "cost_ratio": 0.82, "boost_months": [3, 4, 5]},
    {"category": "Home Appliances", "product_name": "Washing Machine",      "price_range": (18000, 35000), "cost_ratio": 0.80, "boost_months": [10, 11]},
    {"category": "Home Appliances", "product_name": "Microwave Oven",       "price_range": (6000, 15000),  "cost_ratio": 0.75, "boost_months": [10, 11]},

    # Electronics
    {"category": "Electronics", "product_name": "LED TV 43-inch",     "price_range": (22000, 35000),  "cost_ratio": 0.80, "boost_months": [10, 11]},
    {"category": "Electronics", "product_name": "LED TV 55-inch",     "price_range": (38000, 60000),  "cost_ratio": 0.79, "boost_months": [10, 11]},
    {"category": "Electronics", "product_name": "Home Theatre System","price_range": (5000, 20000),   "cost_ratio": 0.60, "boost_months": [10, 11, 12]},
    {"category": "Electronics", "product_name": "Smart Watch",        "price_range": (2000, 12000),   "cost_ratio": 0.55, "boost_months": [10, 11]},
]

PAYMENT_METHODS = ["Cash", "Debit Card", "Credit Card", "UPI", "Net Banking"]
PAYMENT_WEIGHTS = [0.15, 0.15, 0.15, 0.45, 0.10]  # UPI dominant, realistic for India

FIRST_NAMES = ["Ravi", "Priya", "Suresh", "Lakshmi", "Kiran", "Anitha", "Vikram", "Sneha",
               "Arjun", "Divya", "Manoj", "Pooja", "Naveen", "Swathi", "Ramesh", "Kavya",
               "Srinivas", "Meena", "Sandeep", "Aishwarya", "Praveen", "Deepika", "Ajay", "Harika"]
LAST_NAMES = ["Reddy", "Rao", "Kumar", "Varma", "Naidu", "Sharma", "Chowdary", "Prasad",
              "Devi", "Murthy", "Babu", "Sarma"]

CUSTOMER_SEGMENTS = ["Retail", "Wholesale", "Corporate"]
SEGMENT_WEIGHTS = [0.75, 0.15, 0.10]


def generate_customers(n_customers: int) -> pd.DataFrame:
    """Generate a pool of reusable customers (so repeat purchases happen)."""
    customers = []
    for i in range(1, n_customers + 1):
        customers.append({
            "Customer_ID": f"CUST{i:05d}",
            "Customer_Name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            "Customer_Segment": random.choices(CUSTOMER_SEGMENTS, weights=SEGMENT_WEIGHTS, k=1)[0],
        })
    return pd.DataFrame(customers)


def seasonal_weight(d: date, boost_months: list) -> float:
    """Return a multiplier that increases transaction likelihood in
    a product's boost months (e.g. AC sales spike in summer)."""
    base = 1.0
    if d.month in boost_months:
        base *= 2.2
    # General festive season boost across ALL products (Oct-Nov, India festive season)
    if d.month in (10, 11):
        base *= 1.4
    # Weekend boost (footfall is higher)
    if d.weekday() in (5, 6):
        base *= 1.25
    return base


def random_date(start: date, end: date) -> date:
    delta_days = (end - start).days
    return start + timedelta(days=random.randint(0, delta_days))


def generate_transactions(n_transactions: int, customers_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    branch_ids = [b["branch_id"] for b in BRANCHES]
    branch_weights = [b["weight"] for b in BRANCHES]
    branch_lookup = {b["branch_id"]: b for b in BRANCHES}
    customer_ids = customers_df["Customer_ID"].tolist()

    # Pre-compute a flat list of (product, weight) so popular categories
    # (Mobile / Accessories) appear more often than big-ticket appliances.
    category_popularity = {
        "Mobile": 0.30, "Accessories": 0.28, "Electronics": 0.20,
        "Laptop": 0.14, "Home Appliances": 0.08,
    }
    product_weights = [category_popularity[p["category"]] for p in PRODUCT_CATALOG]

    for i in range(1, n_transactions + 1):
        branch_id = random.choices(branch_ids, weights=branch_weights, k=1)[0]
        branch = branch_lookup[branch_id]

        txn_date = random_date(START_DATE, END_DATE)
        product = random.choices(PRODUCT_CATALOG, weights=product_weights, k=1)[0]

        # Apply seasonal weighting by occasionally re-rolling the date
        # towards a boosted period for this product (simple resampling trick)
        if random.random() < 0.35:
            candidate_date = random_date(START_DATE, END_DATE)
            if seasonal_weight(candidate_date, product["boost_months"]) > seasonal_weight(txn_date, product["boost_months"]):
                txn_date = candidate_date

        low, high = product["price_range"]
        unit_price = round(random.uniform(low, high), 2)

        quantity = 1 if unit_price > 20000 else random.choices([1, 2, 3, 4], weights=[0.55, 0.25, 0.12, 0.08])[0]

        # Discounts: bigger during festive months, occasional 0
        if txn_date.month in (10, 11):
            discount = round(random.choice([0, 0.05, 0.10, 0.15, 0.20, 0.25]), 2)
        else:
            discount = round(random.choice([0, 0, 0.05, 0.10, 0.15]), 2)

        payment_method = random.choices(PAYMENT_METHODS, weights=PAYMENT_WEIGHTS, k=1)[0]
        customer_id = random.choice(customer_ids)
        customer_row = customers_df.loc[customers_df["Customer_ID"] == customer_id].iloc[0]

        rows.append({
            "Transaction_ID": f"TXN{uuid.uuid4().hex[:10].upper()}",
            "Transaction_Date": txn_date.isoformat(),
            "Branch_ID": branch["branch_id"],
            "Branch": branch["branch_name"],
            "Region": branch["region"],
            "Customer_ID": customer_row["Customer_ID"],
            "Customer_Name": customer_row["Customer_Name"],
            "Customer_Segment": customer_row["Customer_Segment"],
            "Product_ID": f"P{PRODUCT_CATALOG.index(product) + 1:03d}",
            "Product_Name": product["product_name"],
            "Category": product["category"],
            "Quantity": quantity,
            "Unit_Price": unit_price,
            "Discount": discount,
            "Cost_Ratio": product["cost_ratio"],
            "Payment_Method": payment_method,
        })

        if i % 5000 == 0:
            print(f"  Generated {i:,} / {n_transactions:,} transactions...")

    return pd.DataFrame(rows)


def inject_realistic_messiness(df: pd.DataFrame) -> pd.DataFrame:
    """
    Real POS exports are never perfectly clean. We intentionally inject a
    small amount of messiness so that Phase 3 (Data Cleaning) has real
    work to do:
      - ~0.5% missing Customer_Name
      - ~0.3% missing Discount
      - ~0.4% duplicate rows
      - ~0.2% inconsistent branch name casing/spacing
      - ~0.1% negative/zero quantity (bad records to be rejected)
    """
    df = df.copy()
    n = len(df)
    rng = np.random.default_rng(RANDOM_SEED)

    # Missing customer names
    idx = rng.choice(n, size=int(n * 0.005), replace=False)
    df.loc[idx, "Customer_Name"] = np.nan

    # Missing discount
    idx = rng.choice(n, size=int(n * 0.003), replace=False)
    df.loc[idx, "Discount"] = np.nan

    # Inconsistent branch name formatting (extra spaces / lowercase)
    idx = rng.choice(n, size=int(n * 0.002), replace=False)
    df.loc[idx, "Branch"] = df.loc[idx, "Branch"].str.lower().str.strip() + "  "

    # Invalid quantity (will be rejected in cleaning)
    idx = rng.choice(n, size=int(n * 0.001), replace=False)
    df.loc[idx, "Quantity"] = 0

    # Duplicate rows (simulate double-export)
    dup_sample = df.sample(n=int(n * 0.004), random_state=RANDOM_SEED)
    df = pd.concat([df, dup_sample], ignore_index=True)

    return df


def main():
    print("=" * 60)
    print("MULTI-BRANCH SALES DATA GENERATOR")
    print("=" * 60)

    os.makedirs(RAW_DATA_DIR, exist_ok=True)

    n_customers = 2000
    print(f"\n[1/3] Generating {n_customers:,} customers...")
    customers_df = generate_customers(n_customers)

    print(f"\n[2/3] Generating ~{TARGET_TOTAL_TRANSACTIONS:,} transactions...")
    transactions_df = generate_transactions(TARGET_TOTAL_TRANSACTIONS, customers_df)

    print("\n[3/3] Injecting realistic data-quality issues (for Phase 3 cleaning)...")
    transactions_df = inject_realistic_messiness(transactions_df)

    print(f"\nTotal raw rows generated (including messiness): {len(transactions_df):,}")

    # Split into one file per branch and write to data/raw/
    for idx, branch in enumerate(BRANCHES, start=1):
        branch_name = branch["branch_name"]
        branch_df = transactions_df[
            transactions_df["Branch"].str.strip().str.lower() == branch_name.lower()
        ]
        filename = f"branch_{idx}_{branch_name.lower()}_sales.csv"
        filepath = os.path.join(RAW_DATA_DIR, filename)
        branch_df.to_csv(filepath, index=False)
        print(f"  Wrote {len(branch_df):,} rows -> {filepath}")

    print("\nDone. Raw CSV files are in data/raw/")
    print("Next step: run python/data_cleaning.py")


if __name__ == "__main__":
    main()

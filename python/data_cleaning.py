"""
data_cleaning.py
-----------------
PHASE 3: DATA CLEANING

WHAT THIS SCRIPT DOES:
  1. Reads all 5 raw branch CSV files from data/raw/ and combines them
     into a single DataFrame (this simulates a real ETL "Extract" step
     where a POS system exports one file per branch).
  2. Prints a DATA QUALITY REPORT (missing values, duplicates, invalid
     records) BEFORE any cleaning is done.
  3. Cleans the data:
       - Standardizes text (branch names, product names, categories)
       - Fixes data types (dates, numeric columns)
       - Fills missing values using LOGICAL rules (explained inline)
       - Removes duplicate transactions
       - Validates business rules (Quantity > 0, Unit_Price >= 0, etc.)
         and separates invalid rows into a "rejected" file instead of
         silently dropping them, so nothing is lost without a trace.
  4. Prints a DATA QUALITY REPORT AFTER cleaning, so you can see the
     before/after improvement.
  5. Saves:
       data/processed/cleaned_sales_data.csv   -> good records
       data/processed/rejected_records.csv     -> records that failed
                                                   validation (with a
                                                   reason column)

Run this script from the project root (AFTER generate_data.py):
    python python/data_cleaning.py
"""

import glob
import os

import numpy as np
import pandas as pd

RAW_DATA_DIR = os.path.join("data", "raw")
PROCESSED_DATA_DIR = os.path.join("data", "processed")

# The "official" list of valid branch names. Anything that doesn't match
# one of these after standardization is flagged as invalid.
VALID_BRANCHES = ["Eluru", "Vijayawada", "Rajahmundry", "Visakhapatnam", "Hyderabad"]


# ----------------------------------------------------------------------
# STEP 1: LOAD & COMBINE
# ----------------------------------------------------------------------
def load_raw_data() -> pd.DataFrame:
    csv_files = sorted(glob.glob(os.path.join(RAW_DATA_DIR, "branch_*.csv")))
    if not csv_files:
        raise FileNotFoundError(
            f"No branch CSV files found in {RAW_DATA_DIR}/. "
            "Run python/generate_data.py first."
        )

    print(f"Found {len(csv_files)} raw branch files:")
    frames = []
    for f in csv_files:
        df = pd.read_csv(f)
        print(f"  {os.path.basename(f):45s} -> {len(df):,} rows")
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    print(f"\nCombined raw dataset: {len(combined):,} rows, {combined.shape[1]} columns")
    return combined


# ----------------------------------------------------------------------
# STEP 2: DATA QUALITY REPORT (used both before and after cleaning)
# ----------------------------------------------------------------------
def data_quality_report(df: pd.DataFrame, label: str) -> None:
    print(f"\n{'-' * 60}")
    print(f"DATA QUALITY REPORT — {label}")
    print(f"{'-' * 60}")
    print(f"Total rows: {len(df):,}")

    print("\nMissing values per column:")
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    print(missing.to_string() if len(missing) else "  (none)")

    dup_count = df.duplicated(subset=["Transaction_ID"]).sum() if "Transaction_ID" in df.columns else df.duplicated().sum()
    print(f"\nDuplicate Transaction_IDs: {dup_count:,}")

    if "Quantity" in df.columns:
        invalid_qty = (pd.to_numeric(df["Quantity"], errors="coerce") <= 0).sum()
        print(f"Rows with Quantity <= 0: {invalid_qty:,}")

    if "Unit_Price" in df.columns:
        invalid_price = (pd.to_numeric(df["Unit_Price"], errors="coerce") < 0).sum()
        print(f"Rows with negative Unit_Price: {invalid_price:,}")

    if "Branch" in df.columns:
        unknown_branches = df[~df["Branch"].astype(str).str.strip().str.title().isin(VALID_BRANCHES)]
        print(f"Rows with unrecognized Branch value: {len(unknown_branches):,}")
    print(f"{'-' * 60}")


# ----------------------------------------------------------------------
# STEP 3: CLEANING
# ----------------------------------------------------------------------
def clean_data(df: pd.DataFrame):
    df = df.copy()
    rejected_frames = []

    # --- 3a. Text cleaning: standardize casing/whitespace -------------
    text_cols = ["Branch", "Region", "Category", "Product_Name", "Customer_Name",
                 "Customer_Segment", "Payment_Method"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df.loc[df[col].isin(["nan", "None", ""]), col] = np.nan

    # Branch names specifically get Title Case so "hyderabad  " -> "Hyderabad"
    df["Branch"] = df["Branch"].str.title()

    # --- 3b. Data type handling ----------------------------------------
    df["Transaction_Date"] = pd.to_datetime(df["Transaction_Date"], errors="coerce")
    numeric_cols = ["Quantity", "Unit_Price", "Discount", "Cost_Ratio"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # --- 3c. Missing value handling (logical rules, not blanket drops) -
    # Customer_Name missing but Customer_ID present -> look up the name
    # from another transaction by the same customer (people appear many
    # times in the data, so this recovers most missing names for free).
    id_to_name = (
        df.dropna(subset=["Customer_Name"])
        .drop_duplicates(subset=["Customer_ID"])
        .set_index("Customer_ID")["Customer_Name"]
    )
    missing_name_mask = df["Customer_Name"].isna()
    df.loc[missing_name_mask, "Customer_Name"] = df.loc[missing_name_mask, "Customer_ID"].map(id_to_name)
    # Anything still missing (customer never appears with a name) -> "Unknown Customer"
    df["Customer_Name"] = df["Customer_Name"].fillna("Unknown Customer")

    # Missing Discount -> logically means "no discount was applied" -> 0
    df["Discount"] = df["Discount"].fillna(0)

    # --- 3d. Duplicate handling -----------------------------------------
    before = len(df)
    df = df.drop_duplicates(subset=["Transaction_ID"], keep="first")
    print(f"\nRemoved {before - len(df):,} duplicate Transaction_ID rows.")

    # --- 3e. Validation: split invalid rows into "rejected" ------------
    def reject(mask, reason):
        nonlocal df
        bad = df[mask].copy()
        if len(bad):
            bad["Rejection_Reason"] = reason
            rejected_frames.append(bad)
        return df[~mask]

    df = reject(df["Quantity"] <= 0, "Invalid Quantity (<= 0)")
    df = reject(df["Unit_Price"] < 0, "Negative Unit_Price")
    df = reject((df["Discount"] < 0) | (df["Discount"] > 0.9), "Discount out of valid range (0-0.9)")
    df = reject(df["Transaction_Date"].isna(), "Invalid/unparseable Transaction_Date")
    df = reject(~df["Branch"].isin(VALID_BRANCHES), "Unrecognized Branch name")

    rejected_df = pd.concat(rejected_frames, ignore_index=True) if rejected_frames else pd.DataFrame()

    return df.reset_index(drop=True), rejected_df.reset_index(drop=True)


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
def main():
    print("=" * 60)
    print("PHASE 3 — DATA CLEANING")
    print("=" * 60)

    raw_df = load_raw_data()
    data_quality_report(raw_df, "BEFORE CLEANING")

    cleaned_df, rejected_df = clean_data(raw_df)

    data_quality_report(cleaned_df, "AFTER CLEANING")

    print(f"\nSUMMARY")
    print(f"  Raw records:      {len(raw_df):,}")
    print(f"  Clean records:    {len(cleaned_df):,}")
    print(f"  Rejected records: {len(rejected_df):,}")

    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    cleaned_path = os.path.join(PROCESSED_DATA_DIR, "cleaned_sales_data.csv")
    rejected_path = os.path.join(PROCESSED_DATA_DIR, "rejected_records.csv")

    cleaned_df.to_csv(cleaned_path, index=False)
    print(f"\nSaved cleaned data -> {cleaned_path}")

    if len(rejected_df):
        rejected_df.to_csv(rejected_path, index=False)
        print(f"Saved rejected records -> {rejected_path}")
        print("\nRejection reason breakdown:")
        print(rejected_df["Rejection_Reason"].value_counts().to_string())
    else:
        print("No rows were rejected.")

    print("\nDone. Next step: run python/data_transformation.py")


if __name__ == "__main__":
    main()

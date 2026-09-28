"""
data_transformation.py
-----------------------
PHASE 4: DATA TRANSFORMATION

WHAT THIS SCRIPT DOES:
  Reads the cleaned dataset (data/processed/cleaned_sales_data.csv) and
  calculates the business metrics that the fact table and every SQL/
  Power BI report will be built on. Every formula below only uses
  columns that actually exist in the cleaned data — nothing is invented.

CALCULATED FIELDS (and why each one exists):

  Gross_Sales = Quantity x Unit_Price
      -> The full sale value BEFORE any discount is applied.
         Needed as the base for every other money calculation.

  Discount_Amount = Gross_Sales x Discount
      -> Discount is stored as a fraction (e.g. 0.10 = 10%).
         This converts it into an actual rupee amount.

  Net_Sales = Gross_Sales - Discount_Amount
      -> What the customer actually paid. This is "Total Sales" /
         "Revenue" everywhere in the SQL queries and Power BI dashboard.

  Cost = Quantity x Unit_Price x Cost_Ratio
      -> Cost_Ratio (generated in Phase 2, e.g. 0.80) represents the
         cost price as a fraction of the unit selling price. This is a
         standard retail modelling assumption used because raw POS
         exports don't usually contain a separate cost column.

  Profit = Net_Sales - Cost
      -> The actual margin earned after discount and cost are removed.

  Profit_Margin_Pct = (Profit / Net_Sales) x 100
      -> Profit as a percentage of revenue. Useful for comparing
         products/branches of very different sizes fairly.

  Year, Month, Month_Name, Quarter (derived from Transaction_Date)
      -> Convenience columns so SQL/Power BI trend queries don't need
         to re-derive these every time. (dim_date in Phase 5 will hold
         the authoritative version of these for the warehouse.)

OUTPUT:
  data/processed/transformed_sales_data.csv
      -> This file is what Phase 7 (ETL pipeline) loads into MySQL.

Run this script from the project root (AFTER data_cleaning.py):
    python python/data_transformation.py
"""

import os

import pandas as pd

INPUT_PATH = os.path.join("data", "processed", "cleaned_sales_data.csv")
OUTPUT_PATH = os.path.join("data", "processed", "transformed_sales_data.csv")


def transform(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Transaction_Date"] = pd.to_datetime(df["Transaction_Date"])

    # --- Money calculations -------------------------------------------
    df["Gross_Sales"] = df["Quantity"] * df["Unit_Price"]
    df["Discount_Amount"] = df["Gross_Sales"] * df["Discount"]
    df["Net_Sales"] = df["Gross_Sales"] - df["Discount_Amount"]
    df["Cost"] = df["Quantity"] * df["Unit_Price"] * df["Cost_Ratio"]
    df["Profit"] = df["Net_Sales"] - df["Cost"]

    # Avoid divide-by-zero if Net_Sales is ever 0 (shouldn't happen after
    # cleaning, since Quantity>0 and Unit_Price>=0, but we guard anyway).
    df["Profit_Margin_Pct"] = (df["Profit"] / df["Net_Sales"].replace(0, pd.NA)) * 100
    df["Profit_Margin_Pct"] = df["Profit_Margin_Pct"].round(2)

    # Round all money columns to 2 decimal places for clean reporting
    money_cols = ["Gross_Sales", "Discount_Amount", "Net_Sales", "Cost", "Profit"]
    df[money_cols] = df[money_cols].round(2)

    # --- Date breakdown columns -----------------------------------------
    df["Year"] = df["Transaction_Date"].dt.year
    df["Month"] = df["Transaction_Date"].dt.month
    df["Month_Name"] = df["Transaction_Date"].dt.strftime("%B")
    df["Quarter"] = df["Transaction_Date"].dt.quarter

    return df


def print_summary(df: pd.DataFrame) -> None:
    print("\n" + "-" * 60)
    print("TRANSFORMATION SUMMARY")
    print("-" * 60)
    print(f"Total records transformed: {len(df):,}")
    print(f"Total Gross Sales:  Rs {df['Gross_Sales'].sum():,.2f}")
    print(f"Total Discount:     Rs {df['Discount_Amount'].sum():,.2f}")
    print(f"Total Net Sales:    Rs {df['Net_Sales'].sum():,.2f}")
    print(f"Total Cost:         Rs {df['Cost'].sum():,.2f}")
    print(f"Total Profit:       Rs {df['Profit'].sum():,.2f}")
    print(f"Overall Profit Margin: {(df['Profit'].sum() / df['Net_Sales'].sum() * 100):.2f}%")

    negative_profit = (df["Profit"] < 0).sum()
    print(f"\nTransactions with negative profit (heavy discount): {negative_profit:,}")
    print("(A few negative-profit rows are realistic — deep discounts sometimes")
    print(" sell below cost. If this number were a large %% of all rows, that")
    print(" would signal a pricing/discount problem worth flagging.)")
    print("-" * 60)


def main():
    print("=" * 60)
    print("PHASE 4 — DATA TRANSFORMATION")
    print("=" * 60)

    if not os.path.exists(INPUT_PATH):
        raise FileNotFoundError(
            f"{INPUT_PATH} not found. Run python/data_cleaning.py first."
        )

    df = pd.read_csv(INPUT_PATH)
    print(f"Loaded {len(df):,} cleaned records from {INPUT_PATH}")

    transformed_df = transform(df)
    print_summary(transformed_df)

    transformed_df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved transformed data -> {OUTPUT_PATH}")
    print(f"Columns now: {list(transformed_df.columns)}")
    print("\nDone. Next step: Phase 5 — MySQL Data Warehouse (star schema).")


if __name__ == "__main__":
    main()

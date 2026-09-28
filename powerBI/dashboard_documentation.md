# Power BI Dashboard Documentation

## Connection

- Source: MySQL database (`Get Data > MySQL database`)
- Server: `localhost:3306`
- Database: `multi_branch_sales_dw`
- Tables imported: `dim_branch`, `dim_customer`, `dim_date`, `dim_product`, `fact_sales`

## Relationships (auto-detected, confirmed in Model view)

All 4 dimensions connect to `fact_sales` in a 1-to-many relationship:
- `dim_date[date_key]` → `fact_sales[date_key]`
- `dim_product[product_key]` → `fact_sales[product_key]`
- `dim_branch[branch_key]` → `fact_sales[branch_key]`
- `dim_customer[customer_key]` → `fact_sales[customer_key]`

`dim_date` is marked as the official **Date Table** (key column: `full_date`),
which enables time-intelligence DAX functions like `SAMEPERIODLASTYEAR`.

`dim_date[month_name]` has its sort order set via **Sort by Column** to
`dim_date[month]`, so month names always display in calendar order
(January→December) instead of alphabetical order.

## DAX Measures

All measures live on the `fact_sales` table.

| Measure | DAX | Format | Purpose |
|---|---|---|---|
| Total Sales | `SUM(fact_sales[net_sales])` | Currency, 2dp | Headline revenue figure |
| Total Profit | `SUM(fact_sales[profit])` | Currency, 2dp | Profit after cost & discount |
| Total Quantity | `SUM(fact_sales[quantity])` | Whole number | Units sold |
| Total Orders | `DISTINCTCOUNT(fact_sales[transaction_id])` | Whole number | Distinct transaction count |
| Average Order Value | `DIVIDE([Total Sales], [Total Orders])` | Currency, 2dp | Revenue per transaction |
| Profit Margin % | `DIVIDE([Total Profit], [Total Sales])` | Percentage | Profit as % of revenue |
| Previous Year Sales | `CALCULATE([Total Sales], SAMEPERIODLASTYEAR(dim_date[full_date]))` | Currency | Prior-year sales for the current filter context |
| YoY Growth % | See below | Percentage | Year-over-year sales growth |

**YoY Growth %** (final version — deliberately does not rely on the date
slicer's range, since a multi-year slicer selection broke a naive
`SAMEPERIODLASTYEAR` comparison):
```dax
YoY Growth % =
VAR CurrentYearSales = CALCULATE([Total Sales], dim_date[year] = MAX(dim_date[year]))
VAR PriorYearSales = CALCULATE([Total Sales], dim_date[year] = MAX(dim_date[year]) - 1)
RETURN DIVIDE(CurrentYearSales - PriorYearSales, PriorYearSales)
```

## Pages

### Page 1 — Executive Overview
- **KPI cards:** Total Sales, Total Profit, Total Orders, Total Quantity, Average Order Value
- **Line chart:** Total Sales by year & month_name (monthly trend)
- **Bar chart:** Total Sales by branch_name
- **Donut chart:** Total Sales by category
- **Slicers:** full_date (range), region, branch_name, category

### Page 2 — Branch Performance
- **Clustered column chart:** Total Sales and Total Profit by branch_name (branch comparison + implicit ranking)
- **Line chart:** Total Sales by year, month_name, legend = branch_name (monthly trend per branch)
- **Table:** Total Sales, Total Profit, Total Orders (branch-level totals)
- **Slicers:** branch_name, region, full_date, category

### Page 3 — Product Analysis
- **Bar chart:** Top 10 Products by Total Sales (Top N filter)
- **Bar chart:** Top 10 Products by Total Profit (Top N filter)
- **Treemap:** Total Sales by category
- **Table:** product_name, category, Total Sales, Total Quantity, Total Profit (all 21 products)
- **Slicers:** branch_name, category, region, full_date

### Page 4 — Trend Analysis
- **Card:** YoY Growth %
- **Line chart:** Total Sales by year, month_name, legend = region (regional trend)
- **Clustered column chart:** Total Sales and Total Profit by year
- **Line chart:** Total Sales by year & quarter (quarterly trend)
- **Slicers:** branch_name, category, region, full_date

## Known Issues & Fixes Applied

- **Month name sorting:** `month_name` sorted alphabetically by default.
  Fixed via Column tools → Sort by Column → `month`.
- **Quarter axis order:** a combined year+quarter axis initially displayed
  out of order because the axis was set to sort descending. Fixed via the
  visual's "Sort axis" → Sort ascending, with `year` listed above `quarter`
  in the X-axis field well.
- **YoY Growth % inflated to ~101%:** caused by `SAMEPERIODLASTYEAR`
  combined with a date slicer spanning both years at once (Total Sales
  summed both years while Previous Year Sales only captured one). Fixed
  by rewriting the measure to explicitly compare `MAX(year)` against
  `MAX(year) - 1`, independent of the slicer's range.
- **Q4 2024 apparent decline:** initially the date slicer was set to end
  on `03-10-2024`, cutting off most of Q4. This produced a misleading
  sharp drop on the quarterly trend chart. Confirmed as a filtering
  artifact (not a real business trend) by widening the slicer to the
  full `01-01-2023` – `31-12-2024` range and observing the chart recover.

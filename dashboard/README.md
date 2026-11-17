# AI/BI dashboard: "Swirl & Sons – Monday Morning"

The dashboard is deployed by the bundle from
[`swirl_monday_morning.lvdash.json`](swirl_monday_morning.lvdash.json)
(see [`resources/dashboard.yml`](../resources/dashboard.yml)). Its two datasets are the metric
views themselves, `sales_metrics` and `waste_metrics`, so the dashboard contains no formulas.
Display names and DKK / % formats come from the metric view YAML.

`embed_credentials` is off: viewers query as themselves, so Unity Catalog row filters
(see [`src/sql/12_row_filter.sql`](../src/sql/12_row_filter.sql)) apply per viewer.

> The JSON references the metric views by full name (`swirl_demo.bakery.*`). If you deploy with
> a different catalog or schema, see "Using a different catalog or schema" in the main README.

## What's on it

**Page: Chain overview**

| Widget | Dataset | Shows |
|---|---|---|
| Filters | sales | Order date (range), Region, Channel |
| 4 counters | sales | Net Revenue, Gross Margin %, Average Basket, Unique Customers |
| Line | sales | Net Revenue by month and region |
| Bar | sales | Net Revenue by store |
| Bar | sales | Unique Customers by store |
| Bar | waste | Waste Rate by store |
| Bar | waste | Waste Cost by category |

DKK is Danish kroner, roughly 7.5 to the euro.

## Try it: add a widget without writing a formula

Edit the dashboard and add a line chart on the **sales** dataset: X = *Order Month*,
Y = *Gross Margin %*, colour = *Region*. You should see:
- the **summer 2025 dip** (costs +10%) and the **recovery after the September 2025 price increase**, and
- **Capital Region separating from the rest from March 2026** (the "Swirl Friday" campaign).

Gross Margin % is defined once in the metric view, as total margin divided by total revenue, so
it's correct at whatever grain you chart it.

The same applies to non-additive measures. Add a table with *Store* and *Unique Customers* and
turn on totals: the total is smaller than the sum of the store rows, because it's a distinct count
evaluated at chain level, not a sum.

## Optional

Ask the dashboard's built-in Genie: *"Why did margin drop in the Capital Region in March 2026?"*
It uses the same metric views.

# AI/BI dashboard: "Swirl & Sons – Monday Morning"

Build it beforehand (about 15 minutes). On stage you add **one** widget live (marked ★).

## Data
Workspace sidebar → **Dashboards** → **Create dashboard** → **Data** tab → **Add data source** →
filter to **Metric views** → add `swirl_demo.bakery.sales_metrics` and `swirl_demo.bakery.waste_metrics`.

Display names and DKK/% formats come straight from the YAML (DKK: Danish kroner, roughly 7.5 to the euro; say it once). You don't format anything by hand,
and that's a talking point.

## Page 1: "Chain overview"
| # | Widget | Dataset | Fields |
|---|---|---|---|
| 1 | Counter | sales_metrics | Net Revenue (filter Order Month = last month) |
| 2 | Counter | sales_metrics | Gross Margin % |
| 3 | Counter | sales_metrics | Average Basket |
| 4 | Counter | sales_metrics | Unique Customers |
| 5 | Line | sales_metrics | X = Order Month, Y = Net Revenue, colour = Region |
| 6 | Bar | sales_metrics | X = Store, Y = Net Revenue, sorted desc |
| 7 | Table | sales_metrics | Store, Net Revenue, Gross Margin %, Average Basket, Unique Customers (**show totals**) |
| 8 | Bar | waste_metrics | X = Store, Y = Waste Rate, filter Product Category = Bread |
| ★ | Line (live) | sales_metrics | X = Order Month, Y = **Gross Margin %**, colour = Region |

Global filters: Order Month (date range), Region, Channel.

## The live widget (★): what to say
Drag *Gross Margin %* by *Order Month*, colour by *Region*. The audience sees:
- the **summer 2025 dip** (costs +10%) and the **recovery after the September price increase**, and
- **Capital Region separating from the rest from March 2026** (the Swirl Friday campaign).

"I didn't write a formula. I can't get margin % wrong here, because the ratio is defined once:
sum of margin over sum of revenue at whatever grain I drop it on."

Point at the table's **total row**: Unique Customers in the total is smaller than the sum of the
store rows, because it's a distinct count evaluated at chain level.

## Optional
Ask the dashboard's built-in Genie: *"Why did margin drop in the Capital Region in March 2026?"* It uses the same metric view.

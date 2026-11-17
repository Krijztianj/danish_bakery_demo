# Genie: "Swirl & Sons – Ask the Bakery"

The Genie space (Genie Agent) is deployed by the bundle from
[`resources/genie_space.yml`](../resources/genie_space.yml). You don't need to build it by hand.

It is configured with:
- **Data:** only the two metric views, `sales_metrics` and `waste_metrics`. No raw tables, so every
  answer goes through the governed measures.
- **Instructions:** what "revenue", "margin", "average basket", "Copenhagen" and "last month" mean
  (see below).
- **Sample questions** and **example SQL** that show Genie how to use `MEASURE()`.

Open it from the workspace sidebar → **Genie**. Run `swirl_setup` first: the space needs the metric views.

## Instructions it uses

```
You answer questions for Swirl & Sons, a Danish bakery chain with 11 stores and a Webshop & App.
- Revenue ALWAYS means the Net Revenue measure (DKK excl. VAT, after discounts, excl. refunds).
  Never use Gross Sales for revenue questions.
- Margin means Gross Margin %, unless the user asks for an amount in DKK.
- Average basket means the Average Basket measure (revenue per order), never an average of lines.
- "Copenhagen" means region = 'Capital Region'.
- "Last month" means the last complete calendar month.
- Amounts are in DKK (Danish kroner).
- Waste questions use waste_metrics; sales questions use sales_metrics.
```

## Questions to try

| Question | What you should see |
|---|---|
| *What was turnover by region last month?* | `MEASURE(net_revenue)` grouped by region. "Turnover" is a synonym on the Net Revenue measure. Open **Show code** to see the `MEASURE()` call. |
| *How did gross margin % develop month by month since January 2025?* | A dip from June 2025 (costs +10%) and a recovery after the September 2025 price increase. |
| *What happened to cinnamon swirl sales and margin on Fridays in Copenhagen after March 2026?* | Units up, Gross Margin % down: the "Swirl Friday" 2-for-1 campaign. Follow up with *"and what did it do to waste?"* to switch to `waste_metrics`. |
| *Which store wastes the most bread, and what does it cost us?* | Esbjerg, around 30% waste rate versus ~10% elsewhere. |
| *Who are our customers in the morning rush vs at lunch?* | Station stores peak 07–09; the campus store is busiest at lunch. |

The same stories as plain SQL are in [`src/sql/11_story_queries.sql`](../src/sql/11_story_queries.sql),
so you can check Genie's answers against them.

## Benchmarks

To measure answer quality, add these as benchmarks in the Genie space (**Benchmarks** tab) and run
them. Replace `swirl_demo.bakery` if you deployed with a different catalog or schema.

```
Q: What was net revenue last month?
SELECT MEASURE(net_revenue) FROM swirl_demo.bakery.sales_metrics
WHERE order_month = date_trunc('MONTH', add_months(current_date(), -1))

Q: Average basket by store format last month
SELECT store_format, MEASURE(avg_basket) FROM swirl_demo.bakery.sales_metrics
WHERE order_month = date_trunc('MONTH', add_months(current_date(), -1)) GROUP BY ALL

Q: Waste rate for bread by store in the last 3 months
SELECT store_name, MEASURE(waste_rate) FROM swirl_demo.bakery.waste_metrics
WHERE product_category = 'Bread' AND bake_date >= add_months(current_date(), -3) GROUP BY ALL

Q: How many unique customers did we have in Aarhus in October 2026?
SELECT MEASURE(unique_customers) FROM swirl_demo.bakery.sales_metrics
WHERE city = 'Aarhus' AND order_month = '2026-10-01'

Q: Gross margin % for Cinnamon Swirl on Fridays in Copenhagen since March 2026
SELECT MEASURE(gross_margin_pct) FROM swirl_demo.bakery.sales_metrics
WHERE product_name = 'Cinnamon Swirl' AND weekday = 'Friday' AND region = 'Capital Region'
  AND order_date >= '2026-03-06'
```

## Optional: compare with a Genie space on raw tables

To see what the semantic layer adds, create a second Genie space by hand on the raw tables
(`fact_sales`, `dim_store`, `dim_product`, `dim_customer`) with no instructions, and ask
*"What was revenue last month?"* a few times. Answers usually vary: VAT included or not,
refunds counted or not, walk-in customers dropped by a join.

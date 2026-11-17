# Genie Agent: "Swirl & Sons – Ask the Bakery"

(Genie Spaces are now called Genie Agents.)

## Create it
1. Workspace sidebar → **Genie** → **New** (Genie Agent).
2. **Data**: add `swirl_demo.bakery.sales_metrics` and `swirl_demo.bakery.waste_metrics`.
   Add only the metric views. Don't mix in the raw tables, so every answer goes through the governed measures.
3. **Settings**: Title = *Swirl & Sons – Ask the Bakery*. Default warehouse = your serverless demo warehouse.
4. **Instructions → Text**: paste the block below.
5. **Sample questions**: add the five "audience-facing" questions below.
6. **Benchmarks**: add the benchmark questions and run them (see the end of this file). Aim for all green before the talk.
7. **Share**: give the demo app's service principal **Can Run**, and anyone presenting with you **Can Edit**.

> Second Genie Agent for the cold open (optional): *"Raw tables – no semantics"* on
> `fact_sales`, `dim_store`, `dim_product`, `dim_customer`. Ask it "What was revenue last month?"
> a few times during rehearsal and screenshot the most wrong-but-confident answer as a backup.

## General instructions (paste)

```
You answer questions for Swirl & Sons, a Danish bakery chain with 11 stores and a Webshop & App.
- Revenue ALWAYS means the Net Revenue measure (DKK excl. VAT, after discounts, excl. refunds).
  Never use Gross Sales for revenue questions.
- Margin means Gross Margin %, unless the user asks for an amount in DKK.
- Average basket means the Average Basket measure (revenue per order), never an average of lines.
- "Copenhagen" means region = 'Capital Region'.
- "Last month" means the last complete calendar month.
- Amounts are in DKK (Danish kroner).
- Waste questions use the waste_metrics view; sales questions use sales_metrics.
```

## Audience-facing sample questions
1. What was turnover by region last month?
2. How did gross margin % develop month by month since January 2025?
3. What happened to cinnamon swirl sales and margin on Fridays in Copenhagen after March 2026?
4. Which store wastes the most bread, and what does it cost us?
5. Who are our customers in the morning rush vs at lunch?

## Live script (3 questions, ~4 min)
| # | Ask | What should happen | Talking point |
|---|---|---|---|
| 1 | *What was turnover by region last month?* | Picks `MEASURE(net_revenue)` through the synonym **turnover** and groups by region | "'Turnover' is finance-speak for revenue in the UK. In the US it usually means staff leaving. The synonym makes it unambiguous here." Open **Show code** and point at `MEASURE(`. |
| 2 | *What happened to cinnamon swirl sales and margin on Fridays in Copenhagen after March 2026?* | Units up, Gross Margin % down, and it should find the SWIRLFRIDAY promo | Campaign story. Follow-up: *"and what did it do to waste?"* → waste_metrics, Friday waste up |
| 3 | *Which store wastes the most bread, and what does it cost us?* | Esbjerg, ~30% waste rate | Second metric view, same semantics. Ratio of sums done correctly |

Fallback if Genie wanders: run the matching query in `src/sql/11_story_queries.sql`.

## Benchmarks (question → expected SQL)
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

-- =====================================================================
-- THREE NUMBERS, ONE BAKERY
-- "What was revenue and average basket last month?" answered by three legacy views
-- (src/03_legacy_views.py), each wrong for a common reason, and then by the metric view.
-- Run in the SQL editor on a SQL warehouse.
-- =====================================================================
-- Change these two lines if you deployed with a different catalog / schema.
USE CATALOG swirl_demo;
USE SCHEMA bakery;

-- 1) The legacy answers: three different numbers for the same question
WITH last_month AS (SELECT date_trunc('MONTH', add_months(current_date(), -1)) AS month),
store_ops AS (
  SELECT month,
         SUM(revenue)    AS revenue,
         AVG(avg_basket) AS avg_basket       -- average of store averages
  FROM legacy_store_ops_report GROUP BY month
)
SELECT '1 · Finance dashboard'  AS report, ROUND(f.revenue) AS revenue_dkk, ROUND(f.avg_basket, 2) AS avg_basket_dkk
FROM legacy_finance_kpis f JOIN last_month USING (month)
UNION ALL
SELECT '2 · Store Ops (Power BI)', ROUND(s.revenue), ROUND(s.avg_basket, 2)
FROM store_ops s JOIN last_month USING (month)
UNION ALL
SELECT '3 · Marketing CRM', ROUND(m.revenue), ROUND(m.avg_basket, 2)
FROM legacy_marketing_kpis m JOIN last_month USING (month)
ORDER BY report;


-- =====================================================================
-- THE GOVERNED ANSWER – the same question through the metric view
-- =====================================================================
WITH truth AS (
  SELECT MEASURE(net_revenue) AS revenue,
         MEASURE(avg_basket)  AS avg_basket
  FROM sales_metrics
  WHERE order_month = date_trunc('MONTH', add_months(current_date(), -1))
)
SELECT '✓ Metric view: sales_metrics' AS report, ROUND(revenue) AS revenue_dkk, ROUND(avg_basket, 2) AS avg_basket_dkk
FROM truth;


-- Why they differ: the revenue bridge (raw table, last month)
SELECT ROUND(SUM(gross_amount))                                 AS `Shelf value incl. VAT (Finance)`,
       ROUND(-SUM(discount_amount))                             AS `− Discounts`,
       ROUND(-SUM(vat_amount))                                  AS `− VAT`,
       ROUND(SUM(net_amount))                                   AS `= Net incl. refunds (Store Ops)`,
       ROUND(-SUM(net_amount) FILTER (WHERE is_refunded))       AS `− Refunds`,
       ROUND(SUM(net_amount) FILTER (WHERE NOT is_refunded))    AS `= Net Revenue (metric view)`,
       ROUND(SUM(net_amount) FILTER (WHERE NOT is_refunded AND customer_id IS NULL)) AS `of which walk-ins (Marketing lost these)`
FROM fact_sales
WHERE order_date >= date_trunc('MONTH', add_months(current_date(), -1))
  AND order_date <  date_trunc('MONTH', current_date());


-- =====================================================================
-- NON-ADDITIVE TOTALS – why "just sum the rows" is wrong
-- =====================================================================
WITH per_store AS (
  SELECT store_name, MEASURE(unique_customers) AS customers
  FROM sales_metrics
  WHERE order_month = date_trunc('MONTH', add_months(current_date(), -1))
  GROUP BY ALL
),
chain AS (
  SELECT MEASURE(unique_customers) AS customers
  FROM sales_metrics
  WHERE order_month = date_trunc('MONTH', add_months(current_date(), -1))
)
SELECT 'Sum of 12 store rows (what a spreadsheet does)' AS method, SUM(customers) AS unique_customers FROM per_store
UNION ALL
SELECT 'MEASURE(unique_customers) at chain level', customers FROM chain;

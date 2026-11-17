-- =====================================================================
-- STORY QUERIES – rehearse these, and keep them as a backup if Genie misbehaves live.
-- Every query reads ONLY the metric views: no joins, no business logic in the query.
-- =====================================================================
USE CATALOG swirl_demo;
USE SCHEMA bakery;

-- A · Margin squeeze & recovery (costs +10% Jun 2025, prices +8% Sep 2025)
SELECT order_month,
       MEASURE(net_revenue)      AS net_revenue,
       MEASURE(gross_margin_pct) AS gross_margin_pct
FROM sales_metrics
WHERE order_month >= '2025-01-01'
GROUP BY ALL ORDER BY order_month;

-- B · "Swirl Friday": what did 2-for-1 on Fridays do in Copenhagen?
SELECT CASE WHEN order_date >= '2026-03-06' THEN 'After campaign start' ELSE 'Before' END AS period,
       MEASURE(units_sold)       AS units,
       MEASURE(net_revenue)      AS net_revenue,
       MEASURE(gross_margin_pct) AS gross_margin_pct
FROM sales_metrics
WHERE region = 'Capital Region' AND weekday = 'Friday' AND product_name = 'Cinnamon Swirl'
  AND order_date >= '2025-09-01'
GROUP BY ALL ORDER BY period DESC;

-- B2 · …and the waste side of the same campaign
SELECT CASE WHEN bake_date >= '2026-03-06' THEN 'After campaign start' ELSE 'Before' END AS period,
       MEASURE(waste_rate) AS waste_rate, MEASURE(waste_cost) AS waste_cost
FROM waste_metrics
WHERE region = 'Capital Region' AND weekday = 'Friday' AND product_name = 'Cinnamon Swirl'
  AND bake_date >= '2025-09-01'
GROUP BY ALL ORDER BY period DESC;

-- C · Who throws away the most bread?
SELECT store_name, MEASURE(waste_rate) AS waste_rate, MEASURE(waste_cost) AS waste_cost
FROM waste_metrics
WHERE product_category = 'Bread' AND bake_date >= add_months(current_date(), -3)
GROUP BY ALL ORDER BY waste_rate DESC;

-- D · Shrovetide (Fastelavn) – the 2026 bun rush
SELECT order_date, MEASURE(units_sold) AS shrovetide_buns
FROM sales_metrics
WHERE product_name = 'Shrovetide Bun' AND order_date BETWEEN '2026-01-25' AND '2026-02-20'
GROUP BY ALL ORDER BY order_date;

-- E · Commuters vs students: when do customers come?
SELECT store_format, daypart, MEASURE(orders) AS orders
FROM sales_metrics
WHERE order_month = date_trunc('MONTH', add_months(current_date(), -1)) AND store_format IN ('Station', 'Campus')
GROUP BY ALL ORDER BY store_format, daypart;

-- F · Staff purchases by store (sets up the live "CFO change")
SELECT store_name,
       MEASURE(net_revenue) AS net_revenue,
       SUM(net_amount) FILTER (WHERE is_staff_purchase AND NOT is_refunded) AS staff_net_revenue
FROM sales_metrics
WHERE order_month = date_trunc('MONTH', add_months(current_date(), -1))
GROUP BY ALL ORDER BY staff_net_revenue DESC;
-- ↑ note: plain SUM() over a measure-input field works on a metric view, which is exactly why
--   measure inputs should be hidden from business users in Power BI.
--   (If your runtime rejects mixing SUM() and MEASURE() in one query, run them as two queries.)

-- G · Window measures (Experimental): rolling 7 days and month-over-month
SELECT order_date, MEASURE(net_revenue) AS day_revenue, MEASURE(net_revenue_trailing_7d) AS prior_7d_revenue
FROM sales_metrics
WHERE order_date >= current_date() - INTERVAL 21 DAYS
GROUP BY ALL ORDER BY order_date;

SELECT order_month, MEASURE(net_revenue) AS net_revenue, MEASURE(net_revenue_mom_growth) AS mom_growth
FROM sales_metrics
WHERE order_month >= '2025-06-01'
GROUP BY ALL ORDER BY order_month;

-- H · Aalborg: the new store (opened 1 Apr 2025)
SELECT order_month, MEASURE(net_revenue) AS net_revenue, MEASURE(unique_customers) AS members
FROM sales_metrics
WHERE store_name LIKE 'Aalborg%'
GROUP BY ALL ORDER BY order_month;

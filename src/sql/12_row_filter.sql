-- =====================================================================
-- OPTIONAL – governance: one row filter, enforced in every tool.
--
-- Row filters live on the TABLES; anyone querying the metric view gets them applied.
-- In Power BI this only holds per viewer when the semantic model uses DirectQuery
-- AND per-user SSO credentials. With a shared credential every viewer sees what
-- the credential owner sees.
--
-- Prereq: create account groups 'swirl_hq' and 'swirl_region_central'
-- (Account console → User management → Groups) and add a test user to the regional group.
-- Group membership changes can take a few minutes to apply.
-- =====================================================================
-- Change these two lines if you deployed with a different catalog / schema.
USE CATALOG swirl_demo;
USE SCHEMA bakery;

CREATE OR REPLACE FUNCTION store_region_filter(store_id BIGINT)
RETURNS BOOLEAN
COMMENT 'HQ sees all stores; regional managers see their region (+ Webshop & App).'
RETURN
  is_account_group_member('swirl_hq')
  OR is_account_group_member('admins')                                   -- don't lock yourself out
  OR (is_account_group_member('swirl_region_central') AND store_id IN (1, 2, 3, 12))
  OR (is_account_group_member('swirl_region_capital') AND store_id IN (5, 6, 7, 8, 12))
  OR (is_account_group_member('swirl_region_south')  AND store_id IN (9, 10, 11, 12))
  OR (is_account_group_member('swirl_region_north') AND store_id IN (4, 12));

ALTER TABLE fact_sales      SET ROW FILTER store_region_filter ON (store_id);
ALTER TABLE fact_production SET ROW FILTER store_region_filter ON (store_id);

-- Check as yourself, then as the regional demo user:
SELECT region, MEASURE(net_revenue) FROM sales_metrics GROUP BY ALL;

-- Remove when you're done (src/00_setup.py also drops them before regenerating data):
-- ALTER TABLE fact_sales      DROP ROW FILTER;
-- ALTER TABLE fact_production DROP ROW FILTER;

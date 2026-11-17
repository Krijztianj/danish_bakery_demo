# Databricks notebook source
# MAGIC %md
# MAGIC # 03 · The "before" world: three legacy definitions of revenue
# MAGIC
# MAGIC Three plausible views that each answer *"What was revenue and average basket last month?"* –
# MAGIC and each gets it wrong for a different, very common reason. They power the cold open.
# MAGIC
# MAGIC | View | Who built it | What's wrong |
# MAGIC |---|---|---|
# MAGIC | `legacy_finance_kpis` | Finance (Excel → dashboard) | Uses shelf value incl. VAT, ignores discounts & refunds; "basket" = average **line** |
# MAGIC | `legacy_store_ops_report` | Store Ops (Power BI, hand-written DAX) | Excl. VAT but **keeps refunds**; total customers = **sum of store rows**; total basket = **average of store averages** |
# MAGIC | `legacy_marketing_kpis` | Marketing / CRM | **INNER JOIN** to members silently drops every walk-in customer |

# COMMAND ----------

dbutils.widgets.text("catalog", "swirl_demo", "Catalog")
dbutils.widgets.text("schema", "bakery", "Schema")
spark.sql(f"USE CATALOG `{dbutils.widgets.get('catalog')}`")
spark.sql(f"USE SCHEMA `{dbutils.widgets.get('schema')}`")

# COMMAND ----------

spark.sql("""
CREATE OR REPLACE VIEW legacy_finance_kpis
COMMENT 'LEGACY – Finance monthly KPIs. Revenue = shelf value incl. VAT. Do not use.'
AS
SELECT date_trunc('MONTH', order_date)  AS month,
       SUM(gross_amount)                AS revenue,
       AVG(gross_amount)                AS avg_basket
FROM fact_sales
GROUP BY ALL
""")

spark.sql("""
CREATE OR REPLACE VIEW legacy_store_ops_report
COMMENT 'LEGACY – Store Ops monthly report per store. Revenue excl. VAT incl. refunds. Do not use.'
AS
SELECT date_trunc('MONTH', f.order_date)              AS month,
       s.store_name,
       SUM(f.net_amount)                              AS revenue,
       COUNT(DISTINCT f.order_id)                     AS orders,
       SUM(f.net_amount) / COUNT(DISTINCT f.order_id) AS avg_basket,
       COUNT(DISTINCT f.customer_id)                  AS customers
FROM fact_sales f
JOIN dim_store s USING (store_id)
GROUP BY ALL
""")

spark.sql("""
CREATE OR REPLACE VIEW legacy_marketing_kpis
COMMENT 'LEGACY – Marketing CRM KPIs. Joins to loyalty members only. Do not use.'
AS
SELECT date_trunc('MONTH', f.order_date)              AS month,
       SUM(f.net_amount)                              AS revenue,
       SUM(f.net_amount) / COUNT(DISTINCT f.order_id) AS avg_basket,
       COUNT(DISTINCT f.customer_id)                  AS customers
FROM fact_sales f
JOIN dim_customer c ON f.customer_id = c.customer_id      -- the silent killer
WHERE NOT f.is_refunded
GROUP BY ALL
""")

print("legacy views created")

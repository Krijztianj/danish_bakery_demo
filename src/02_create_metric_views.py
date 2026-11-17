# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · Create the metric views
# MAGIC
# MAGIC Reads `metric_views/*.yaml`, substitutes catalog/schema and runs
# MAGIC `CREATE OR REPLACE VIEW … WITH METRICS LANGUAGE YAML`.
# MAGIC
# MAGIC Window measures are **Experimental**. If your compute rejects them, the notebook retries
# MAGIC without them (and without measures that depend on them) so the rest of the demo still works.
# MAGIC
# MAGIC Needs a SQL warehouse or compute that supports metric view YAML 1.1 (serverless is fine).

# COMMAND ----------

dbutils.widgets.text("catalog", "swirl_demo", "Catalog")
dbutils.widgets.text("schema", "bakery", "Schema")
CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")

# COMMAND ----------

import mv_utils

for name in ["sales_metrics", "waste_metrics"]:
    print(f"→ {name}")
    mv_utils.apply_metric_view(
        spark,
        f"`{CATALOG}`.`{SCHEMA}`.`{name}`",
        mv_utils.render(f"{name}.yaml", CATALOG, SCHEMA),
    )

# COMMAND ----------

# MAGIC %md ## Smoke test

# COMMAND ----------

display(spark.sql(f"""
SELECT region,
       MEASURE(net_revenue)       AS net_revenue,
       MEASURE(gross_margin_pct)  AS gross_margin_pct,
       MEASURE(avg_basket)        AS avg_basket,
       MEASURE(unique_customers)  AS unique_customers
FROM `{CATALOG}`.`{SCHEMA}`.sales_metrics
WHERE order_date >= add_months(current_date(), -1)
GROUP BY ALL ORDER BY net_revenue DESC
"""))

# COMMAND ----------

display(spark.sql(f"""
SELECT store_name, MEASURE(waste_rate) AS waste_rate, MEASURE(waste_cost) AS waste_cost
FROM `{CATALOG}`.`{SCHEMA}`.waste_metrics
WHERE product_category = 'Bread'
GROUP BY ALL ORDER BY waste_rate DESC
"""))

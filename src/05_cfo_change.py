# Databricks notebook source
# MAGIC %md
# MAGIC # 05 · Change a definition once, everywhere ("the CFO change")
# MAGIC
# MAGIC Scenario: the CFO decides staff purchases no longer count as revenue. You change the
# MAGIC **Net Revenue** measure in one place, and the dashboard, Genie, the app (and Power BI, after
# MAGIC a republish) all show the new number.
# MAGIC
# MAGIC You can make the change by hand in the metric view editor (Catalog Explorer → `sales_metrics`
# MAGIC → Edit) by appending `AND NOT is_staff_purchase` to the Net Revenue filter, or use this notebook:
# MAGIC * `mode = apply` – apply the change.
# MAGIC * `mode = reset` – put the original definition back.
# MAGIC
# MAGIC Uses `ALTER VIEW … AS $$yaml$$`, which keeps grants on the metric view.

# COMMAND ----------

dbutils.widgets.text("catalog", "swirl_demo", "Catalog")
dbutils.widgets.text("schema", "bakery", "Schema")
dbutils.widgets.dropdown("mode", "apply", ["apply", "reset"], "Mode")
CATALOG, SCHEMA, MODE = (dbutils.widgets.get(k) for k in ("catalog", "schema", "mode"))

# COMMAND ----------

import mv_utils

yaml_text = mv_utils.render("sales_metrics.yaml", CATALOG, SCHEMA)

OLD = "SUM(net_amount) FILTER (WHERE NOT is_refunded)"
NEW = "SUM(net_amount) FILTER (WHERE NOT is_refunded AND NOT is_staff_purchase)"
OLD_COMMENT = "after discounts, excluding refunded lines."
NEW_COMMENT = "after discounts, excluding refunded lines and staff purchases (CFO decision)."

if MODE == "apply":
    # Net Revenue and the window measures built on the same expression – not Member Revenue.
    yaml_text = yaml_text.replace(OLD, NEW).replace(OLD_COMMENT, NEW_COMMENT)

fqn = f"`{CATALOG}`.`{SCHEMA}`.sales_metrics"
mv_utils.apply_metric_view(spark, fqn, yaml_text, alter=True)
print(f"{MODE}: done")

# COMMAND ----------

display(spark.sql(f"""
SELECT store_name, MEASURE(net_revenue) AS net_revenue
FROM {fqn}
WHERE order_month = date_trunc('MONTH', add_months(current_date(), -1))
GROUP BY ALL ORDER BY net_revenue DESC
"""))

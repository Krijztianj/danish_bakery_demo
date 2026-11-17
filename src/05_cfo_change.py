# Databricks notebook source
# MAGIC %md
# MAGIC # 05 · The live "CFO change" (fallback + reset)
# MAGIC
# MAGIC **On stage, do this in the metric view editor** (Catalog Explorer → `sales_metrics` → Edit),
# MAGIC by appending `AND NOT is_staff_purchase` to the **Net Revenue** measure. It is more convincing
# MAGIC when the audience sees you type it.
# MAGIC
# MAGIC Use this notebook:
# MAGIC * `mode = apply` – fallback if the editor misbehaves live.
# MAGIC * `mode = reset` – put the original definition back after the rehearsal / talk.
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

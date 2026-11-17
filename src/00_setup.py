# Databricks notebook source
# MAGIC %md
# MAGIC # 00 · Catalog and schema
# MAGIC If you can't create catalogs in this workspace, set the `catalog` widget/variable to an
# MAGIC existing catalog where you have `USE CATALOG` + `CREATE SCHEMA`.

# COMMAND ----------

dbutils.widgets.text("catalog", "swirl_demo", "Catalog")
dbutils.widgets.text("schema", "bakery", "Schema")
CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")

try:
    spark.sql(f"CREATE CATALOG IF NOT EXISTS `{CATALOG}` COMMENT 'Swirl & Sons metric views demo'")
except Exception as e:  # noqa: BLE001
    print(f"Could not create catalog ({type(e).__name__}) – assuming `{CATALOG}` already exists.")

spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{CATALOG}`.`{SCHEMA}` COMMENT 'Fictional Danish bakery chain – demo data'")

# If row filters from src/sql/12_row_filter.sql are active, overwriting the tables fails.
for t in ("fact_sales", "fact_production"):
    try:
        spark.sql(f"ALTER TABLE `{CATALOG}`.`{SCHEMA}`.{t} DROP ROW FILTER")
    except Exception:  # noqa: BLE001 – table doesn't exist yet or has no filter
        pass

print(f"Ready: {CATALOG}.{SCHEMA}")

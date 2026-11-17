# Databricks notebook source
# MAGIC %md
# MAGIC # 01 · Generate demo data — *Swirl & Sons* (fictional Danish bakery chain)
# MAGIC
# MAGIC Creates a small star schema in Unity Catalog:
# MAGIC
# MAGIC | Table | Grain | Approx. rows (scale 0.5) |
# MAGIC |---|---|---|
# MAGIC | `dim_store` | store | 12 |
# MAGIC | `dim_product` | product | 21 |
# MAGIC | `dim_customer` | loyalty member | ~30k |
# MAGIC | `fact_sales` | order line | ~5M |
# MAGIC | `fact_production` | store × product × day | ~170k |
# MAGIC
# MAGIC **Planted stories** (so the demo has something to find), all configured in `demo_config.py`:
# MAGIC 1. **Margin squeeze & recovery** – costs +10% from 1 Jun 2025, shelf prices +8% from 1 Sep 2025.
# MAGIC 2. **"Swirl Friday" campaign** – from 6 Mar 2026, 2-for-1 cinnamon swirls on Fridays in Copenhagen stores → units ↑, margin ↓, waste ↑.
# MAGIC 3. **Shrovetide (Fastelavn)** – Shrovetide buns explode in the 10 days before Shrovetide Sunday.
# MAGIC 4. **New store** – Aalborg opens 1 Apr 2025 (no prior-year comparison).
# MAGIC 5. **Waste problem** – Esbjerg over-bakes bread (~30% waste vs ~10% elsewhere).
# MAGIC 6. **Staff purchases** – ~3% of in-store orders at 50% off; Copenhagen - Vesterbro ~8% (used by the definition change in `05_cfo_change.py`).
# MAGIC 7. **Online growth** – Webshop & App grows ~45% per year, with higher refund rate.
# MAGIC 8. **Commuters vs students** – station stores peak 07–09, campus store collapses in July.
# MAGIC
# MAGIC Runs on serverless or any UC-enabled cluster. Scale 0.5 takes a few minutes on serverless.

# COMMAND ----------

dbutils.widgets.text("catalog", "swirl_demo", "Catalog")
dbutils.widgets.text("schema", "bakery", "Schema")
dbutils.widgets.text("start_date", "2024-01-01", "Start date")
dbutils.widgets.text("end_date", "", "End date (empty = yesterday)")
dbutils.widgets.text("scale", "0.5", "Scale (1.0 ≈ 10M order lines)")

CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")
START = dbutils.widgets.get("start_date")
END = dbutils.widgets.get("end_date").strip()
SCALE = float(dbutils.widgets.get("scale"))

import datetime as _dt
if not END:
    END = str(_dt.date.today() - _dt.timedelta(days=1))
print(f"Generating {START} → {END} at scale {SCALE} into {CATALOG}.{SCHEMA}")

# COMMAND ----------

import itertools

from pyspark.sql import functions as F
from pyspark.sql import Window

import demo_config as cfg

spark.sql(f"USE CATALOG `{CATALOG}`")
spark.sql(f"USE SCHEMA `{SCHEMA}`")

# Every rand()/randn() call gets its own seed – Spark gives identical streams for identical seeds.
_seeds = itertools.count(1001)
def rnd():
    return F.rand(next(_seeds))
def rndn():
    return F.randn(next(_seeds))

def lit_date(d):
    return F.lit(str(d)).cast("date")

# COMMAND ----------

# MAGIC %md ## Dimensions: stores and products

# COMMAND ----------

stores_pdf = cfg.STORES.copy()
stores_pdf["pool_size"] = (stores_pdf["base_orders_per_day"] * 10 * max(SCALE, 0.05)).round().astype(int)
stores_pdf["growth"] = stores_pdf["store_format"].map(cfg.GROWTH_BY_FORMAT)
stores_sdf = spark.createDataFrame(stores_pdf)

(stores_sdf
 .select("store_id", "store_name", "city", "region", "store_format",
         F.col("opened_date").cast("date").alias("opened_date"),
         F.col("latitude").cast("double").alias("latitude"),
         F.col("longitude").cast("double").alias("longitude"))
 .write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("dim_store"))

products_pdf = cfg.PRODUCTS.copy()
products_sdf = spark.createDataFrame(products_pdf)
(products_sdf
 .select("product_id", "product_name", "product_name_local", "category",
         "list_price_incl_vat", F.col("base_unit_cost").alias("unit_cost_excl_vat"),
         "is_seasonal", "is_made_to_order")
 .write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("dim_product"))

display(spark.table("dim_store"))

# COMMAND ----------

# MAGIC %md ## Store-days → orders

# COMMAND ----------

fastelavn_cond = " OR ".join(
    [f"(order_date BETWEEN date_sub(DATE'{d}', 9) AND DATE'{d}')" for d in cfg.FASTELAVN_SUNDAYS]
)

days = (spark.sql(f"SELECT explode(sequence(DATE'{START}', DATE'{END}', INTERVAL 1 DAY)) AS order_date")
        .withColumn("dow", F.dayofweek("order_date"))          # 1 = Sunday … 7 = Saturday
        .withColumn("month", F.month("order_date"))
        .withColumn("is_fastelavn_window", F.expr(fastelavn_cond))
        .withColumn("season_key", F.when(F.col("is_fastelavn_window"), F.lit("FASTELAVN"))
                                   .otherwise(F.col("month").cast("string"))))

dow_sdf = spark.createDataFrame(cfg.dow_table())
month_sdf = spark.createDataFrame(cfg.month_table())

store_days = (days.crossJoin(F.broadcast(stores_sdf))
              .where(F.col("order_date") >= F.col("opened_date").cast("date"))
              .join(F.broadcast(dow_sdf), ["store_format", "dow"])
              .join(F.broadcast(month_sdf), ["store_format", "month"])
              .withColumn("years", F.datediff("order_date", lit_date(START)) / F.lit(365.25))
              .withColumn("trend", F.pow(1 + F.col("growth"), F.col("years")))
              .withColumn("is_campaign_day",
                          (F.col("dow") == 6)
                          & F.col("store_id").isin(cfg.CAMPAIGN_STORES)
                          & (F.col("order_date") >= lit_date(cfg.CAMPAIGN_START)))
              .withColumn("expected_orders",
                          F.col("base_orders_per_day") * F.lit(SCALE)
                          * F.col("dow_factor") * F.col("month_factor") * F.col("trend")
                          * F.when(F.col("is_fastelavn_window"), 1.12).otherwise(1.0)
                          * F.when(F.col("is_campaign_day"), 1.08).otherwise(1.0)
                          * F.exp(rndn() * 0.10))
              .withColumn("n_orders", F.round("expected_orders").cast("int"))
              .where("n_orders > 0"))   # sequence(1, 0) would yield [1, 0] – never explode it

pool_map = F.create_map(*[x for r in stores_pdf.itertuples() for x in (F.lit(int(r.store_id)), F.lit(int(r.pool_size)))])
member_p_instore = F.create_map(*[x for k, v in cfg.MEMBER_P_INSTORE.items() for x in (F.lit(str(k)), F.lit(float(v)))])
hours_sdf = F.broadcast(spark.createDataFrame(cfg.hour_mix()))

orders = (store_days
          .withColumn("order_seq", F.explode(F.sequence(F.lit(1), F.col("n_orders"))))
          .withColumn("u_hour", rnd()))

orders = (orders.join(hours_sdf,
                      (orders.store_format == hours_sdf.hour_format)
                      & (orders.u_hour >= hours_sdf.lo) & (orders.u_hour < hours_sdf.hi))
          .drop("hour_format", "lo", "hi", "weight", "u_hour"))

orders = (orders
    .withColumn("order_minute", F.floor(rnd() * 60).cast("int"))
    .withColumn("order_ts", F.expr("make_timestamp(year(order_date), month(order_date), day(order_date), order_hour, order_minute, 0)"))
    .withColumn("order_id", F.format_string("%02d-%s-%05d", F.col("store_id"),
                                            F.date_format("order_date", "yyyyMMdd"), F.col("order_seq")))
    # channel
    .withColumn("channel",
        F.when(F.col("store_format") == "Online", F.lit("Delivery"))
         .when(rnd() < (0.08 + 0.03 * F.col("years")), F.lit("Click & Collect"))
         .otherwise(F.lit("In-store")))
    # staff purchases (in-store only)
    .withColumn("is_staff_purchase",
        (F.col("channel") == "In-store")
        & (rnd() < F.when(F.col("store_id") == cfg.STAFF_HEAVY_STORE, 0.08).otherwise(0.03)))
    # loyalty member?
    .withColumn("member_p",
        F.when(F.col("is_staff_purchase"), F.lit(0.0))
         .when(F.col("channel") == "Click & Collect", F.lit(1.0))
         .when(F.col("channel") == "Delivery", F.lit(cfg.MEMBER_P_DELIVERY))
         .otherwise(F.element_at(member_p_instore, F.col("store_format"))))
    .withColumn("is_member", rnd() < F.col("member_p"))
    # which customer: mostly from the store's own pool, sometimes a visitor from another store
    .withColumn("pool_store",
        F.when((F.col("channel") != "Delivery") & (rnd() < 0.10), (F.floor(rnd() * 11) + 1).cast("int"))
         .otherwise(F.col("store_id")))
    .withColumn("customer_id",
        F.when(F.col("is_member"),
               (F.col("pool_store").cast("bigint") * 1_000_000 + 1
                + F.floor(F.element_at(pool_map, F.col("pool_store")) * F.pow(rnd(), 2.2))).cast("bigint")))
    # basket size
    .withColumn("n_lines",
        F.when(F.col("store_format") == "Online", (F.floor(rnd() * 4) + 2).cast("int"))
         .otherwise(F.expr(f"CASE WHEN rand({next(_seeds)}) < 0.45 THEN 1 "
                           f"WHEN rand({next(_seeds)}) < 0.64 THEN 2 "
                           f"WHEN rand({next(_seeds)}) < 0.75 THEN 3 ELSE 4 END"))))

# COMMAND ----------

# MAGIC %md ## Orders → order lines

# COMMAND ----------

mix_sdf = F.broadcast(spark.createDataFrame(cfg.product_mix()))
prod_attrs = F.broadcast(products_sdf.select("product_id", "category", "list_price_incl_vat", "base_unit_cost"))

lines = (orders
         .withColumn("line_no", F.explode(F.sequence(F.lit(1), F.col("n_lines"))))
         .withColumn("u_prod", rnd()))

lines = (lines.join(mix_sdf,
                    (lines.store_format == mix_sdf.mix_format)
                    & (lines.season_key == mix_sdf.mix_season_key)
                    & (lines.u_prod >= mix_sdf.lo) & (lines.u_prod < mix_sdf.hi))
         .drop("mix_format", "mix_season_key", "lo", "hi", "weight", "u_prod")
         .join(prod_attrs, "product_id"))

is_campaign_line = F.col("is_campaign_day") & (F.col("product_id") == cfg.CAMPAIGN_PRODUCT_ID)

lines = (lines
    .withColumn("price_factor", F.when(F.col("order_date") >= lit_date(cfg.PRICE_INCREASE_DATE),
                                       cfg.PRICE_INCREASE_FACTOR).otherwise(1.0))
    .withColumn("cost_factor", F.when(F.col("order_date") >= lit_date(cfg.COST_INFLATION_DATE),
                                      cfg.COST_INFLATION_FACTOR).otherwise(1.0))
    .withColumn("unit_price", F.round(F.col("list_price_incl_vat") * F.col("price_factor") * 2) / 2)   # nearest 0.50 DKK
    .withColumn("unit_cost", F.round(F.col("base_unit_cost") * F.col("cost_factor"), 2))
    .withColumn("base_qty",
        F.when(F.col("product_id").isin(8, 9),
               F.floor(rnd() * 5) + 2 + F.when(F.col("store_format") == "Online", 2).otherwise(0))
         .otherwise(F.expr(f"CASE WHEN rand({next(_seeds)}) < 0.72 THEN 1 "
                           f"WHEN rand({next(_seeds)}) < 0.70 THEN 2 ELSE 3 END")))
    .withColumn("quantity", (F.col("base_qty") * F.when(is_campaign_line, 2).otherwise(1)).cast("int"))
    .withColumn("promo_code", F.when(is_campaign_line, F.lit(cfg.CAMPAIGN_PROMO_CODE)))
    .withColumn("gross_amount", F.round(F.col("quantity") * F.col("unit_price"), 2))
    .withColumn("discount_amount", F.round(
        F.when(is_campaign_line | F.col("is_staff_purchase"), F.col("gross_amount") * 0.5).otherwise(0.0), 2))
    .withColumn("net_amount", F.round((F.col("gross_amount") - F.col("discount_amount")) / (1 + cfg.SALES_TAX_RATE), 2))
    .withColumn("vat_amount", F.round(F.col("gross_amount") - F.col("discount_amount") - F.col("net_amount"), 2))
    .withColumn("cost_amount", F.round(F.col("quantity") * F.col("unit_cost"), 2))
    .withColumn("is_refunded", rnd() < F.when(F.col("channel") == "Delivery", 0.03).otherwise(0.006)))

fact_sales = lines.select(
    F.concat_ws("-", "order_id", F.col("line_no").cast("string")).alias("order_line_id"),
    "order_id", "line_no", "order_date", "order_ts", "order_hour", "store_id", "product_id", "customer_id",
    "channel", "quantity", "unit_price", "gross_amount", "discount_amount", "net_amount", "vat_amount",
    "cost_amount", "promo_code", "is_staff_purchase", "is_refunded")

(fact_sales.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("fact_sales"))
print(f"fact_sales rows: {spark.table('fact_sales').count():,}")

# COMMAND ----------

# MAGIC %md ## Loyalty members (`dim_customer`) – derived from who actually bought something

# COMMAND ----------

seg_sdf = F.broadcast(spark.createDataFrame(cfg.segment_table()))
fs = spark.table("fact_sales")

cust = (fs.where("customer_id IS NOT NULL")
        .groupBy("customer_id")
        .agg(F.min("order_date").alias("member_since"),
             F.sum(F.when(~F.col("is_refunded"), F.col("net_amount")).otherwise(0)).alias("lifetime_net"))
        .withColumn("home_store_id", F.floor(F.col("customer_id") / 1_000_000).cast("int"))
        .join(F.broadcast(spark.table("dim_store").select(F.col("store_id").alias("home_store_id"),
                                                          F.col("store_format").alias("home_format"))),
              "home_store_id")
        .withColumn("u_seg", (F.abs(F.xxhash64("customer_id")) % 100000) / F.lit(100000.0)))

cust = (cust.join(seg_sdf, (cust.home_format == seg_sdf.seg_format)
                  & (cust.u_seg >= seg_sdf.lo) & (cust.u_seg < seg_sdf.hi))
        .withColumn("spend_rank", F.percent_rank().over(Window.orderBy(F.col("lifetime_net").desc())))
        .withColumn("loyalty_tier", F.when(F.col("spend_rank") < 0.10, "Gold")
                                     .when(F.col("spend_rank") < 0.40, "Silver")
                                     .otherwise("Bronze"))
        .select("customer_id", "home_store_id", "segment", "loyalty_tier", "member_since"))

cust.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("dim_customer")
print(f"dim_customer rows: {spark.table('dim_customer').count():,}")

# COMMAND ----------

# MAGIC %md ## Daily production & waste (`fact_production`)

# COMMAND ----------

sold = (fs.where("NOT is_refunded")
        .groupBy("order_date", "store_id", "product_id")
        .agg(F.sum("quantity").alias("sold_units"),
             F.max(F.col("promo_code").isNotNull()).alias("had_campaign")))

prod = (sold.join(F.broadcast(spark.table("dim_product")
                              .select("product_id", "category", "is_made_to_order", "unit_cost_excl_vat")),
                  "product_id")
        .where("NOT is_made_to_order")
        .withColumn("overbake",
            F.when(F.col("store_id") == 12, 1.02 + rnd() * 0.02)                               # central bakery, made to order
             .when((F.col("store_id") == cfg.WASTE_PROBLEM_STORE) & (F.col("category") == "Bread"),
                   1.40 + rnd() * 0.12)                                                         # Esbjerg bread problem
             .when(F.col("had_campaign"), 1.25 + rnd() * 0.10)                                 # campaign Fridays
             .otherwise(1.07 + rnd() * 0.07 + F.when(F.dayofweek("order_date") == 1, 0.05).otherwise(0.0)))
        .withColumn("produced_units", F.greatest(F.round(F.col("sold_units") * F.col("overbake")), F.col("sold_units")).cast("int"))
        .withColumn("wasted_units", (F.col("produced_units") - F.col("sold_units")).cast("int"))
        .withColumn("unit_cost", F.round(F.col("unit_cost_excl_vat")
                                         * F.when(F.col("order_date") >= lit_date(cfg.COST_INFLATION_DATE),
                                                  cfg.COST_INFLATION_FACTOR).otherwise(1.0), 2))
        .select(F.col("order_date").alias("bake_date"), "store_id", "product_id",
                "produced_units", F.col("sold_units").cast("int").alias("sold_units"), "wasted_units", "unit_cost"))

prod.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("fact_production")
print(f"fact_production rows: {spark.table('fact_production').count():,}")

# COMMAND ----------

# MAGIC %md ## Layout, keys and comments (comments help Genie *and* show up in Power BI descriptions)

# COMMAND ----------

def try_sql(stmt):
    try:
        spark.sql(stmt)
    except Exception as e:  # noqa: BLE001 – best-effort niceties
        print(f"skipped: {stmt[:80]}… ({type(e).__name__})")

try_sql("ALTER TABLE fact_sales CLUSTER BY (order_date, store_id)")
try_sql("ALTER TABLE fact_production CLUSTER BY (bake_date, store_id)")
try_sql("OPTIMIZE fact_sales")
try_sql("OPTIMIZE fact_production")

comments = {
    "dim_store": ("Swirl & Sons bakery locations (11 physical stores + Webshop & App).", {
        "store_format": "Flagship, Station, Campus, Neighbourhood or Online.",
        "region": "Danish region. Webshop and App is National."}),
    "dim_product": ("Products sold by Swirl & Sons. Prices in DKK incl. 25% VAT.", {
        "product_name": "Product name, e.g. Cinnamon Swirl.",
        "product_name_local": "Original Danish product name, e.g. Kanelsnegl.",
        "list_price_incl_vat": "Original shelf price in DKK incl. VAT (before the Sep 2025 price increase)."}),
    "dim_customer": ("Loyalty club members. Anonymous walk-in customers are not in this table.", {
        "segment": "Student, Commuter, Family or Business.",
        "loyalty_tier": "Gold (top 10% spend), Silver (next 30%), Bronze."}),
    "fact_sales": ("Order lines from all stores and the webshop. One row per order line.", {
        "gross_amount": "quantity × unit_price, DKK incl. VAT, before discounts.",
        "discount_amount": "Discount in DKK incl. VAT (campaigns and staff discount).",
        "net_amount": "DKK excl. VAT after discounts. Includes refunded lines – filter is_refunded.",
        "vat_amount": "25% Danish VAT on the discounted amount.",
        "cost_amount": "Cost of goods in DKK excl. VAT.",
        "customer_id": "Loyalty member id; NULL for anonymous walk-ins and staff purchases.",
        "is_staff_purchase": "Employee purchase at 50% staff discount.",
        "is_refunded": "Line was refunded after purchase.",
        "promo_code": "SWIRLFRIDAY = 2-for-1 cinnamon swirls on Fridays in Copenhagen (from Mar 2026)."}),
    "fact_production": ("Units baked, sold and wasted per store, product and day (drinks excluded).", {
        "wasted_units": "Units baked but not sold (produced_units - sold_units).",
        "unit_cost": "Cost per unit in DKK excl. VAT on that day."}),
}
for tbl, (tcomment, cols) in comments.items():
    try_sql(f"COMMENT ON TABLE {tbl} IS '{tcomment}'")
    for col, c in cols.items():
        try_sql(f"ALTER TABLE {tbl} ALTER COLUMN {col} COMMENT '{c}'")

# COMMAND ----------

# MAGIC %md ## Sanity checks – do the planted stories show up?

# COMMAND ----------

display(spark.sql("""
SELECT date_trunc('MONTH', order_date) AS month,
       round(sum(net_amount) FILTER (WHERE NOT is_refunded))                                         AS net_revenue,
       round(1 - sum(cost_amount) FILTER (WHERE NOT is_refunded)
                 / sum(net_amount) FILTER (WHERE NOT is_refunded), 3)                                AS gross_margin_pct
FROM fact_sales GROUP BY ALL ORDER BY month
"""))

# COMMAND ----------

display(spark.sql("""
SELECT s.store_name, p.category,
       round(sum(wasted_units) / sum(produced_units), 3) AS waste_rate
FROM fact_production f JOIN dim_store s USING (store_id) JOIN dim_product p USING (product_id)
WHERE p.category = 'Bread'
GROUP BY ALL ORDER BY waste_rate DESC
"""))

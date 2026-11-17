"""
Static configuration for the Swirl & Sons demo data (fictional Danish bakery chain).

Plain Python + pandas only, so it can be unit-tested outside Databricks.
The generator notebook (01_generate_data.py) imports this module.

Everything that makes the data "tell a story" lives here, so you can tune it
without touching the Spark code.
"""
from datetime import date

import pandas as pd

# --------------------------------------------------------------------------
# Planted stories (the things Genie / dashboards should "discover")
# --------------------------------------------------------------------------
COST_INFLATION_DATE = date(2025, 6, 1)    # flour/butter costs +10%  -> margin dip summer 2025
COST_INFLATION_FACTOR = 1.10
PRICE_INCREASE_DATE = date(2025, 9, 1)    # shelf prices +8%          -> margin recovers
PRICE_INCREASE_FACTOR = 1.08

CAMPAIGN_START = date(2026, 3, 6)         # "Swirl Friday": 2-for-1 cinnamon swirls on Fridays
CAMPAIGN_STORES = [5, 6, 7, 8]            # Copenhagen area stores only
CAMPAIGN_PRODUCT_ID = 1                   # Cinnamon Swirl
CAMPAIGN_PROMO_CODE = "SWIRLFRIDAY"

# Fastelavn (Shrovetide) Sundays: Shrovetide buns peak in the 10 days before
FASTELAVN_SUNDAYS = [date(2024, 2, 11), date(2025, 3, 2), date(2026, 2, 15), date(2027, 2, 7)]

WASTE_PROBLEM_STORE = 10                  # Esbjerg over-bakes bread
STAFF_HEAVY_STORE = 7                     # Vesterbro: generous staff discounts
SALES_TAX_RATE = 0.25                     # Danish VAT, shelf prices include VAT

# --------------------------------------------------------------------------
# Stores
# --------------------------------------------------------------------------
STORES = pd.DataFrame(
    [
        # id, name, city, region, format, opened, base orders/day, lat, lon
        (1, "Aarhus - City Centre", "Aarhus", "Central Denmark", "Flagship", "2015-05-01", 520, 56.1557, 10.2075),
        (2, "Aarhus - Central Station", "Aarhus", "Central Denmark", "Station", "2018-03-01", 450, 56.1503, 10.2045),
        (3, "Aarhus - University", "Aarhus", "Central Denmark", "Campus", "2019-08-15", 380, 56.1685, 10.2030),
        (4, "Aalborg - Old Town", "Aalborg", "North Denmark", "Neighbourhood", "2025-04-01", 330, 57.0496, 9.9187),
        (5, "Copenhagen - Central Station", "Copenhagen", "Capital Region", "Station", "2016-02-01", 650, 55.6727, 12.5647),
        (6, "Copenhagen - Norrebro", "Copenhagen", "Capital Region", "Neighbourhood", "2017-04-01", 420, 55.6930, 12.5440),
        (7, "Copenhagen - Vesterbro", "Copenhagen", "Capital Region", "Neighbourhood", "2017-09-01", 400, 55.6690, 12.5550),
        (8, "Copenhagen - Frederiksberg", "Copenhagen", "Capital Region", "Flagship", "2020-06-01", 480, 55.6780, 12.5450),
        (9, "Odense - City Centre", "Odense", "Southern Denmark", "Neighbourhood", "2019-10-01", 340, 55.3959, 10.3833),
        (10, "Esbjerg - City Centre", "Esbjerg", "Southern Denmark", "Neighbourhood", "2021-03-01", 260, 55.4670, 8.4520),
        (11, "Vejle - City Centre", "Vejle", "Southern Denmark", "Neighbourhood", "2022-05-01", 240, 55.7090, 9.5350),
        (12, "Webshop & App", "Online", "National", "Online", "2023-01-01", 300, 56.1930, 10.1700),  # central bakery
    ],
    columns=["store_id", "store_name", "city", "region", "store_format", "opened_date",
             "base_orders_per_day", "latitude", "longitude"],
)
STORES["opened_date"] = pd.to_datetime(STORES["opened_date"]).dt.date

# Yearly organic growth by format (online grows fast)
GROWTH_BY_FORMAT = {"Flagship": 0.06, "Station": 0.06, "Campus": 0.05, "Neighbourhood": 0.06, "Online": 0.45}

# --------------------------------------------------------------------------
# Products (prices in DKK incl. 25% VAT, cost excl. VAT)
# --------------------------------------------------------------------------
PRODUCTS = pd.DataFrame(
    [
        # id, name, local (Danish) name, category, price, cost, base weight
        (1, "Cinnamon Swirl", "Kanelsnegl", "Pastry", 28.0, 6.5, 14),
        (2, "Poppy Seed Danish", "Tebirkes", "Pastry", 22.0, 5.0, 9),
        (3, "Custard Danish", "Spandauer", "Pastry", 26.0, 6.8, 6),
        (4, "Croissant", "Croissant", "Pastry", 24.0, 5.5, 8),
        (5, "Chocolate Swirl", "Chokoladesnegl", "Pastry", 32.0, 8.0, 5),
        (6, "Rye Bread", "Rugbrød", "Bread", 45.0, 9.0, 6),
        (7, "Sourdough Loaf", "Surdejsbrød", "Bread", 55.0, 11.0, 5),
        (8, "Wholegrain Bun", "Grovbolle", "Bread", 9.0, 2.0, 10),
        (9, "White Roll", "Rundstykke", "Bread", 7.0, 1.6, 9),
        (10, "Raspberry Slice", "Hindbærsnitte", "Cakes", 30.0, 7.5, 4),
        (11, "Rum Ball", "Romkugle", "Cakes", 22.0, 4.5, 3),
        (12, "Marzipan Log", "Træstamme", "Cakes", 26.0, 6.0, 2),
        (13, "Kringle (sharing)", "Kringle", "Cakes", 89.0, 20.0, 1.5),
        (14, "Shrovetide Bun", "Fastelavnsbolle", "Seasonal", 38.0, 9.5, 0),
        (15, "Christmas Pancake Balls (6)", "Æbleskiver", "Seasonal", 45.0, 10.0, 0),
        (16, "Filter Coffee", "Kaffe", "Drinks", 30.0, 3.0, 10),
        (17, "Caffe Latte", "Caffè latte", "Drinks", 45.0, 6.0, 9),
        (18, "Chai Latte", "Chai latte", "Drinks", 48.0, 7.0, 3),
        (19, "Apple Juice", "Æblejuice", "Drinks", 35.0, 9.0, 3),
        (20, "Open Sandwich", "Smørrebrød", "Lunch", 69.0, 22.0, 4),
        (21, "Chicken Sandwich", "Sandwich med kylling", "Lunch", 75.0, 25.0, 4),
    ],
    columns=["product_id", "product_name", "product_name_local", "category",
             "list_price_incl_vat", "base_unit_cost", "base_weight"],
)
PRODUCTS["is_seasonal"] = PRODUCTS["category"].eq("Seasonal")
PRODUCTS["is_made_to_order"] = PRODUCTS["category"].eq("Drinks")   # no production waste

# Category affinity per store format
CATEGORY_AFFINITY = {
    "Station":       {"Drinks": 2.5, "Lunch": 1.5, "Bread": 0.4, "Cakes": 0.7},
    "Campus":        {"Drinks": 2.0, "Bread": 0.5, "Lunch": 1.3},
    "Neighbourhood": {"Bread": 1.6, "Cakes": 1.2, "Drinks": 0.7},
    "Flagship":      {"Cakes": 1.4, "Drinks": 1.1},
    "Online":        {"Bread": 1.8, "Cakes": 1.5, "Drinks": 0.1, "Lunch": 0.5},
}
PRODUCT_AFFINITY = {
    ("Campus", 1): 1.3,     # students love cinnamon swirls
    ("Flagship", 13): 2.0,  # kringle for the weekend crowd
}

# Seasonal product weights by "season key" (month number as str, or FASTELAVN)
SEASONAL_WEIGHTS = {
    14: {"1": 3, "2": 10, "FASTELAVN": 45},     # Shrovetide Bun
    15: {"11": 5, "12": 16},                    # Christmas Pancake Balls
}

SEASON_KEYS = [str(m) for m in range(1, 13)] + ["FASTELAVN"]
FORMATS = ["Flagship", "Station", "Campus", "Neighbourhood", "Online"]

# --------------------------------------------------------------------------
# Traffic shape
# --------------------------------------------------------------------------
# Spark dayofweek(): 1 = Sunday ... 7 = Saturday
DOW_FACTORS = {
    "Station":       {1: .55, 2: 1.15, 3: 1.15, 4: 1.15, 5: 1.15, 6: 1.20, 7: .65},
    "Campus":        {1: .35, 2: 1.25, 3: 1.25, 4: 1.25, 5: 1.25, 6: 1.10, 7: .40},
    "Neighbourhood": {1: 1.45, 2: .80, 3: .80, 4: .85, 5: .90, 6: 1.05, 7: 1.55},
    "Flagship":      {1: 1.20, 2: .85, 3: .85, 4: .90, 5: .95, 6: 1.15, 7: 1.50},
    "Online":        {1: 1.35, 2: .90, 3: .90, 4: .90, 5: .95, 6: 1.05, 7: 1.20},
}
_DEFAULT_MONTH = {1: .92, 2: 1.0, 3: .98, 4: 1.0, 5: 1.02, 6: 1.0, 7: .85, 8: .97, 9: 1.02, 10: 1.0, 11: 1.03, 12: 1.18}
MONTH_FACTORS = {
    "Flagship": dict(_DEFAULT_MONTH),
    "Neighbourhood": dict(_DEFAULT_MONTH),
    "Station": {**_DEFAULT_MONTH, 7: .75},
    "Campus": {**_DEFAULT_MONTH, 1: .85, 6: .80, 7: .35, 8: .70, 12: .90},
    "Online": {**_DEFAULT_MONTH, 7: .90, 12: 1.35},
}

HOUR_WEIGHTS = {
    "Station":       {6: 4, 7: 12, 8: 14, 9: 9, 10: 5, 11: 5, 12: 7, 13: 5, 14: 4, 15: 5, 16: 7, 17: 8, 18: 5, 19: 3, 20: 2},
    "Campus":        {7: 3, 8: 6, 9: 9, 10: 12, 11: 12, 12: 14, 13: 12, 14: 9, 15: 7, 16: 5, 17: 3, 18: 2},
    "Neighbourhood": {6: 2, 7: 6, 8: 11, 9: 13, 10: 12, 11: 9, 12: 7, 13: 6, 14: 5, 15: 6, 16: 7, 17: 6, 18: 3},
    "Flagship":      {7: 3, 8: 6, 9: 9, 10: 11, 11: 11, 12: 11, 13: 10, 14: 9, 15: 9, 16: 8, 17: 6, 18: 4, 19: 2},
    "Online":        {7: 2, 8: 5, 9: 7, 10: 8, 11: 9, 12: 9, 13: 8, 14: 7, 15: 8, 16: 9, 17: 10, 18: 9, 19: 6, 20: 3},
}

# Probability that an order is made by a loyalty member (in-store); app channels are always members
MEMBER_P_INSTORE = {"Campus": .55, "Station": .25, "Neighbourhood": .33, "Flagship": .30}
MEMBER_P_DELIVERY = 0.92   # 8% guest checkout

SEGMENT_MIX = {   # segment of a loyalty member, by home store format
    "Campus":        [("Student", .70), ("Commuter", .10), ("Family", .10), ("Business", .10)],
    "Station":       [("Commuter", .65), ("Student", .10), ("Family", .10), ("Business", .15)],
    "Neighbourhood": [("Family", .60), ("Commuter", .15), ("Student", .15), ("Business", .10)],
    "Flagship":      [("Family", .35), ("Business", .30), ("Commuter", .20), ("Student", .15)],
    "Online":        [("Family", .50), ("Business", .30), ("Commuter", .15), ("Student", .05)],
}


# --------------------------------------------------------------------------
# Lookup-table builders (pandas) -> broadcast-joined in Spark
# --------------------------------------------------------------------------
def _cumulate(df: pd.DataFrame, group_cols: list, weight_col: str) -> pd.DataFrame:
    """Add [lo, hi) cumulative probability bounds per group, for range-join sampling."""
    df = df[df[weight_col] > 0].copy()
    df["p"] = df[weight_col] / df.groupby(group_cols)[weight_col].transform("sum")
    df["hi"] = df.groupby(group_cols)["p"].cumsum()
    df["lo"] = df["hi"] - df["p"]
    # make the last bucket of each group close at exactly 1.0 (float safety)
    last = df.groupby(group_cols)["hi"].transform("max") == df["hi"]
    df.loc[last, "hi"] = 1.0000001
    return df.drop(columns=["p"])


def product_mix() -> pd.DataFrame:
    """Probability of each product per (store_format, season_key)."""
    rows = []
    for fmt in FORMATS:
        for sk in SEASON_KEYS:
            for p in PRODUCTS.itertuples():
                if p.product_id in SEASONAL_WEIGHTS:
                    w = SEASONAL_WEIGHTS[p.product_id].get(sk, 0)
                else:
                    w = p.base_weight
                w *= CATEGORY_AFFINITY.get(fmt, {}).get(p.category, 1.0)
                w *= PRODUCT_AFFINITY.get((fmt, p.product_id), 1.0)
                rows.append((fmt, sk, p.product_id, float(w)))
    df = pd.DataFrame(rows, columns=["mix_format", "mix_season_key", "product_id", "weight"])
    return _cumulate(df, ["mix_format", "mix_season_key"], "weight")


def hour_mix() -> pd.DataFrame:
    rows = [(fmt, h, float(w)) for fmt, hw in HOUR_WEIGHTS.items() for h, w in hw.items()]
    df = pd.DataFrame(rows, columns=["hour_format", "order_hour", "weight"])
    return _cumulate(df, ["hour_format"], "weight")


def dow_table() -> pd.DataFrame:
    return pd.DataFrame([(f, d, v) for f, m in DOW_FACTORS.items() for d, v in m.items()],
                        columns=["store_format", "dow", "dow_factor"])


def month_table() -> pd.DataFrame:
    return pd.DataFrame([(f, mo, v) for f, m in MONTH_FACTORS.items() for mo, v in m.items()],
                        columns=["store_format", "month", "month_factor"])


def segment_table() -> pd.DataFrame:
    rows = []
    for fmt, mix in SEGMENT_MIX.items():
        acc = 0.0
        for seg, p in mix:
            rows.append((fmt, seg, acc, acc + p))
            acc += p
    df = pd.DataFrame(rows, columns=["seg_format", "segment", "lo", "hi"])
    df.loc[df.groupby("seg_format")["hi"].transform("max") == df["hi"], "hi"] = 1.0000001
    return df

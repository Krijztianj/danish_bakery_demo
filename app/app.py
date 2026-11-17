"""
Swirl & Sons – Store Cockpit (Databricks App)

Point of the app in the demo: a custom app gets the SAME governed numbers as the dashboard,
Genie and Power BI, because it only selects dimensions and MEASURE()s from the metric views.
There is no business logic in this file.

Auth: if user authorization is enabled for the app (scopes: sql, dashboards.genie), queries run
as the signed-in user, so Unity Catalog row filters apply per user. Otherwise they run as the
app's service principal.
"""
import os

import pandas as pd
import streamlit as st
from databricks import sql
from databricks.sdk import WorkspaceClient
from databricks.sdk.core import Config

CATALOG = os.getenv("MV_CATALOG", "swirl_demo")
SCHEMA = os.getenv("MV_SCHEMA", "bakery")
WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID", "")
GENIE_SPACE_ID = os.getenv("GENIE_SPACE_ID", "")
SALES = f"{CATALOG}.{SCHEMA}.sales_metrics"
WASTE = f"{CATALOG}.{SCHEMA}.waste_metrics"

cfg = Config()
st.set_page_config(page_title="Swirl & Sons – Store Cockpit", page_icon="🥐", layout="wide")


# ---------------------------------------------------------------- auth & querying
def _headers() -> dict:
    try:
        return dict(st.context.headers)
    except Exception:  # noqa: BLE001 – running locally
        return {}


def user_token() -> str | None:
    return _headers().get("X-Forwarded-Access-Token") or _headers().get("x-forwarded-access-token")


def user_email() -> str:
    h = _headers()
    return h.get("X-Forwarded-Email") or h.get("x-forwarded-email") or "service-principal"


def _connect():
    host = cfg.host.replace("https://", "")
    http_path = f"/sql/1.0/warehouses/{WAREHOUSE_ID}"
    token = user_token()
    if token:  # on-behalf-of-user: UC row filters apply to the viewer
        return sql.connect(server_hostname=host, http_path=http_path, access_token=token)
    return sql.connect(server_hostname=host, http_path=http_path, credentials_provider=lambda: cfg.authenticate)


@st.cache_data(ttl=300, show_spinner=False)
def run_query(query: str, params: dict | None, _cache_user: str) -> pd.DataFrame:
    # _cache_user is part of the cache key on purpose: never share one user's
    # row-filtered results with another user.
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(query, params or {})
        return cur.fetchall_arrow().to_pandas()


def q(query: str, params: dict | None = None) -> pd.DataFrame:
    return run_query(query, params, user_email())


def workspace_client() -> WorkspaceClient:
    token = user_token()
    if token:
        return WorkspaceClient(host=cfg.host, token=token, auth_type="pat")
    return WorkspaceClient()


# ---------------------------------------------------------------- sidebar
st.sidebar.title("🥐 Swirl & Sons")
st.sidebar.caption(f"Signed in as **{user_email()}**")

stores = q(f"SELECT store_name FROM {SALES} GROUP BY ALL ORDER BY store_name")["store_name"].tolist()
store = st.sidebar.selectbox("Store", ["All stores"] + stores)
store_filter = "" if store == "All stores" else "AND store_name = :store"
params = {} if store == "All stores" else {"store": store}

st.sidebar.divider()
st.sidebar.markdown(
    "Every number on this page comes from **Unity Catalog metric views**: "
    f"`{SALES}` and `{WASTE}`. The app contains no revenue, margin or waste formulas."
)

# ---------------------------------------------------------------- KPIs
st.title(f"Store Cockpit · {store}")
st.caption("Last 28 days vs. the 28 days before")

KPI_SQL = f"""
SELECT CASE WHEN order_date >= current_date() - INTERVAL 28 DAYS THEN 'current' ELSE 'previous' END AS period,
       MEASURE(net_revenue)       AS net_revenue,
       MEASURE(gross_margin_pct)  AS gross_margin_pct,
       MEASURE(avg_basket)        AS avg_basket,
       MEASURE(unique_customers)  AS unique_customers
FROM {SALES}
WHERE order_date >= current_date() - INTERVAL 56 DAYS {store_filter}
GROUP BY ALL
"""
WASTE_SQL = f"""
SELECT CASE WHEN bake_date >= current_date() - INTERVAL 28 DAYS THEN 'current' ELSE 'previous' END AS period,
       MEASURE(waste_rate) AS waste_rate,
       MEASURE(waste_cost) AS waste_cost
FROM {WASTE}
WHERE bake_date >= current_date() - INTERVAL 56 DAYS {store_filter}
GROUP BY ALL
"""

kpi = q(KPI_SQL, params).set_index("period")
waste = q(WASTE_SQL, params).set_index("period")


def delta(df, col, pct_points=False):
    if "previous" not in df.index or "current" not in df.index:
        return None
    cur, prev = df.at["current", col], df.at["previous", col]
    if prev in (None, 0) or pd.isna(prev):
        return None
    return f"{(cur - prev) * 100:+.1f} pp" if pct_points else f"{(cur / prev - 1) * 100:+.1f}%"


if "current" in kpi.index:
    c = kpi.loc["current"]
    cols = st.columns(5)
    cols[0].metric("Net Revenue", f"{c.net_revenue:,.0f} kr.", delta(kpi, "net_revenue"))
    cols[1].metric("Gross Margin %", f"{c.gross_margin_pct:.1%}", delta(kpi, "gross_margin_pct", True))
    cols[2].metric("Average Basket", f"{c.avg_basket:,.2f} kr.", delta(kpi, "avg_basket"))
    cols[3].metric("Unique Customers", f"{c.unique_customers:,.0f}", delta(kpi, "unique_customers"))
    if "current" in waste.index:
        cols[4].metric("Waste Rate", f"{waste.at['current', 'waste_rate']:.1%}",
                       delta(waste, "waste_rate", True), delta_color="inverse")

tab_trend, tab_products, tab_genie, tab_sql = st.tabs(["📈 Trend", "🥐 Products", "💬 Ask Genie", "🔎 The SQL"])

# ---------------------------------------------------------------- trend
TREND_SQL = f"""
SELECT order_week,
       MEASURE(net_revenue)      AS net_revenue,
       MEASURE(gross_margin_pct) AS gross_margin_pct
FROM {SALES}
WHERE order_date >= current_date() - INTERVAL 26 WEEKS {store_filter}
GROUP BY ALL ORDER BY order_week
"""
with tab_trend:
    trend = q(TREND_SQL, params).set_index("order_week")
    left, right = st.columns(2)
    left.subheader("Net Revenue per week")
    left.bar_chart(trend["net_revenue"])
    right.subheader("Gross Margin % per week")
    right.line_chart(trend["gross_margin_pct"])

# ---------------------------------------------------------------- products
PRODUCTS_SQL = f"""
SELECT product_name AS product, product_category AS category,
       MEASURE(units_sold)        AS units,
       MEASURE(net_revenue)       AS net_revenue,
       MEASURE(gross_margin_pct)  AS gross_margin_pct
FROM {SALES}
WHERE order_date >= current_date() - INTERVAL 28 DAYS {store_filter}
GROUP BY ALL ORDER BY net_revenue DESC
"""
with tab_products:
    products = q(PRODUCTS_SQL, params)
    products["gross_margin_pct"] = products["gross_margin_pct"] * 100
    st.dataframe(
        products,
        hide_index=True, use_container_width=True,
        column_config={
            "net_revenue": st.column_config.NumberColumn("Net Revenue", format="%.0f kr."),
            "gross_margin_pct": st.column_config.ProgressColumn("Gross Margin %", min_value=0, max_value=100, format="%.1f%%"),
        },
    )

# ---------------------------------------------------------------- genie
with tab_genie:
    if not GENIE_SPACE_ID:
        st.info("Set GENIE_SPACE_ID (app resource 'genie-space') to enable this tab.")
    else:
        st.caption("Same Genie Agent as in the workspace → same metric views → same answers.")
        question = st.chat_input("Ask about sales, margin, customers or waste…")
        st.session_state.setdefault("genie_history", [])

        for role, payload in st.session_state.genie_history:
            with st.chat_message(role):
                if isinstance(payload, str):
                    st.markdown(payload)
                else:
                    st.markdown(payload.get("text", ""))
                    if payload.get("sql"):
                        with st.expander("Generated SQL"):
                            st.code(payload["sql"], language="sql")
                    if payload.get("df") is not None:
                        st.dataframe(payload["df"], hide_index=True)

        if question:
            st.session_state.genie_history.append(("user", question))
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"), st.spinner("Genie is thinking…"):
                w = workspace_client()
                conv_id = st.session_state.get("genie_conversation_id")
                if conv_id:
                    msg = w.genie.create_message_and_wait(GENIE_SPACE_ID, conv_id, question)
                else:
                    msg = w.genie.start_conversation_and_wait(GENIE_SPACE_ID, question)
                    st.session_state.genie_conversation_id = msg.conversation_id

                answer = {"text": "", "sql": None, "df": None}
                for att in msg.attachments or []:
                    if att.text and att.text.content:
                        answer["text"] += att.text.content + "\n\n"
                    if att.query and att.query.query:
                        answer["text"] += att.query.description or ""
                        answer["sql"] = att.query.query
                        res = w.genie.get_message_attachment_query_result(
                            GENIE_SPACE_ID, msg.conversation_id, msg.id, att.attachment_id)
                        sr = res.statement_response
                        if sr and sr.result and sr.manifest:
                            cols_ = [c.name for c in sr.manifest.schema.columns]
                            answer["df"] = pd.DataFrame(sr.result.data_array or [], columns=cols_)
                st.markdown(answer["text"] or "_(no text answer)_")
                if answer["sql"]:
                    with st.expander("Generated SQL – look for MEASURE()"):
                        st.code(answer["sql"], language="sql")
                if answer["df"] is not None:
                    st.dataframe(answer["df"], hide_index=True)
                st.session_state.genie_history.append(("assistant", answer))

        if st.session_state.genie_history and st.button("New conversation"):
            st.session_state.genie_history = []
            st.session_state.pop("genie_conversation_id", None)
            st.rerun()

# ---------------------------------------------------------------- the SQL
with tab_sql:
    st.markdown("This is **all** the SQL behind this page. Dimensions and `MEASURE()` only, with no formulas:")
    for title, text in [("KPIs", KPI_SQL), ("Waste", WASTE_SQL), ("Trend", TREND_SQL), ("Products", PRODUCTS_SQL)]:
        st.markdown(f"**{title}**")
        st.code(text.strip(), language="sql")

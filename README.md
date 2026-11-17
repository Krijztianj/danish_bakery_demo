# Swirl & Sons: Unity Catalog metric views demo

One semantic layer, defined once as **Unity Catalog metric views**, feeding an AI/BI dashboard,
a Genie space, a Databricks App and (optionally) Power BI. Every tool shows the same revenue,
margin, basket and waste numbers, because none of them contains a formula of its own.

The data is a fictional Danish bakery chain: 11 stores plus a Webshop & App, about 5 million
order lines, generated with a set of planted stories to discover (a margin squeeze, a Friday
campaign, a waste problem, a new store and more).

Everything is deployed as a [Databricks Asset Bundle](https://docs.databricks.com/dev-tools/bundles/).

## What's in the box

```
databricks.yml                     bundle: variables, setup + refresh jobs, Store Cockpit app
metric_views/*.yaml                THE semantic layer: sales_metrics and waste_metrics
src/00_setup.py                    creates the catalog (if allowed) and schema
src/01_generate_data.py            synthetic star schema with planted stories (tuned in demo_config.py)
src/02_create_metric_views.py      creates the metric views from metric_views/*.yaml
src/03_legacy_views.py             three "legacy" revenue views, each wrong in a common way
src/05_cfo_change.py               change the Net Revenue definition once, see it change everywhere
src/sql/10_three_revenue_numbers.sql  legacy answers vs the metric view, and why they differ
src/sql/11_story_queries.sql       one query per planted story
src/sql/12_row_filter.sql          optional: row-level security that every tool respects
resources/dashboard.yml            AI/BI dashboard        → dashboard/README.md
resources/genie_space.yml          Genie space            → genie/README.md
resources/powerbi_job.yml          optional Power BI publish job (not deployed by default)
app/                               Streamlit "Store Cockpit" app
```

## Prerequisites

- A Databricks workspace with **Unity Catalog** and **serverless** compute for jobs (any cloud).
- A **serverless SQL warehouse**. You need its ID: SQL Warehouses → *your warehouse* →
  Connection details → HTTP path (the last segment).
- Permission to create a catalog, **or** an existing catalog where you have `USE CATALOG` and
  `CREATE SCHEMA` (see [Using a different catalog or schema](#using-a-different-catalog-or-schema)).
- **Databricks Apps** enabled. For the app to query as the signed-in user (so row filters apply
  per user), also enable **user authorization** for apps; otherwise it queries as the app's
  service principal.
- [Databricks CLI](https://docs.databricks.com/dev-tools/cli/install.html), tested with v1.22.1,
  authenticated against your workspace: `databricks auth login --host <workspace-url>`.

## Deploy

```bash
databricks bundle deploy --var warehouse_id=<warehouse-id>
databricks bundle run swirl_setup     # generates the data and creates the metric views (a few minutes)
databricks bundle run swirl_cockpit   # starts the app
```

`swirl_setup` must finish before you open the dashboard, Genie space or app, because they all read
the metric views. If the first `deploy` fails while creating the Genie space or dashboard because
the metric views don't exist yet, run `swirl_setup` and then `deploy` again.

To avoid retyping variables, add them to the target in `databricks.yml`:

```yaml
targets:
  dev:
    mode: development
    default: true
    variables:
      warehouse_id: <warehouse-id>
```

## Explore the demo

1. **The problem.** Run [`src/sql/10_three_revenue_numbers.sql`](src/sql/10_three_revenue_numbers.sql)
   in the SQL editor: three legacy views give three different answers to "What was revenue last
   month?". The same file then shows the metric view's answer and a revenue bridge explaining
   the differences.
2. **The semantic layer.** Open `sales_metrics` in Catalog Explorer, or read
   [`metric_views/sales_metrics.yaml`](metric_views/sales_metrics.yaml): dimensions, measures,
   display names, formats and synonyms, defined once.
3. **The dashboard.** Open *Swirl & Sons – Monday Morning*. See [dashboard/README.md](dashboard/README.md).
4. **Genie.** Ask *Swirl & Sons – Ask the Bakery* questions in plain language.
   See [genie/README.md](genie/README.md) for questions to try.
5. **The app.** Open the *swirl-store-cockpit* app. Its **The SQL** tab shows that it only selects
   dimensions and `MEASURE()`s.
6. **Change a definition once.** Run [`src/05_cfo_change.py`](src/05_cfo_change.py) with
   `mode = apply` to exclude staff purchases from Net Revenue, then refresh the dashboard, Genie
   and the app. Run it with `mode = reset` to undo.
7. **Optional: governance.** [`src/sql/12_row_filter.sql`](src/sql/12_row_filter.sql) adds a row
   filter on the tables; every tool querying the metric views respects it.

The planted stories and the queries that surface them are in
[`src/sql/11_story_queries.sql`](src/sql/11_story_queries.sql) and described at the top of
[`src/01_generate_data.py`](src/01_generate_data.py).

## Using a different catalog or schema

The defaults are catalog `swirl_demo` and schema `bakery`. To use others, pass
`--var catalog=<catalog> --var schema=<schema>` to `deploy` (or set them under the target).
The jobs, Genie space and app follow the variables. Two things don't:

- **The dashboard.** Metric view datasets in the dashboard JSON use full names. Update them before
  deploying:
  ```bash
  sed -i 's/swirl_demo\.bakery\./<catalog>.<schema>./g' dashboard/swirl_monday_morning.lvdash.json
  ```
- **The SQL files** in `src/sql/` start with `USE CATALOG` / `USE SCHEMA`. Change those two lines.

## Optional: Power BI

[`resources/powerbi_job.yml`](resources/powerbi_job.yml) publishes `sales_metrics` to Power BI as a
DirectQuery semantic model. It isn't deployed by default, because it needs:

- The **Publish Metric Views To Power BI** preview enabled on the workspace (ask your Databricks
  account team), then turned on by a workspace admin under **Previews**.
- A **Unity Catalog connection of type Power BI**: Catalog → ⚙ → **Connections** →
  **Create connection** → *Power BI*. Grant yourself `USE CONNECTION`.
- A Power BI workspace in **Premium per-user**, Premium or Fabric capacity, with the
  **XMLA endpoint** set to **Read Write**.
- Entra consent for the **Databricks Dataset Publishing Integration** app (requested on first
  publish; a tenant admin may need to approve it).

Then uncomment `resources/powerbi_job.yml` under `include` in `databricks.yml` and run:

```bash
databricks bundle deploy --var warehouse_id=<warehouse-id> \
  --var powerbi_workspace="<Power BI workspace name>" \
  --var powerbi_connection=<UC Power BI connection name>
databricks bundle run swirl_publish_powerbi
```

Run the job again after any metric view change. After the first publish, set up SSO once in
Power BI (semantic model → Settings → Data source credentials → Edit credentials → OAuth2 →
tick *Report viewers can only access this data source with their own Power BI identities using
DirectQuery*) so row filters apply per viewer.

## Notes

- **Window measures** (rolling 7 days, month-over-month) are *Experimental*. If your compute
  rejects them, `02_create_metric_views.py` recreates the view without them and prints what it
  dropped. Querying them needs a regular serverless SQL warehouse: Real-Time (`REALTIME`)
  warehouses reject window measures with month ranges (`net_revenue_mom_growth`). The dashboard
  and app don't use window measures, so they work on either.
- **Dates.** The data runs from 1 Jan 2024 to yesterday, and "last month" is always relative to
  today. The planted stories have fixed dates (for example the campaign starts 6 Mar 2026), set in
  [`src/demo_config.py`](src/demo_config.py). The `swirl_refresh` job regenerates the data
  nightly; it's paused by default.
- Re-running the generator overwrites the tables, and numbers shift slightly with the date range.
- **Clean up** with `databricks bundle destroy`, then drop the catalog or schema.
- Everything is fictional: stores, products, prices and customers.

## License

[MIT](LICENSE)

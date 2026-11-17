# Swirl & Sons: Metric Views demo bundle

One semantic layer (Unity Catalog metric views) feeding an AI/BI dashboard, a Genie Agent,
a Databricks App and Power BI. The data is a fictional Danish bakery chain.

```
databricks.yml                 bundle: setup job, nightly refresh job, Store Cockpit app
src/00_setup.py                catalog + schema
src/01_generate_data.py        synthetic star schema with planted stories (config in demo_config.py)
src/02_create_metric_views.py  creates sales_metrics + waste_metrics from metric_views/*.yaml
src/03_legacy_views.py         three "wrong" legacy definitions for the cold open
src/05_cfo_change.py           fallback/reset for the live definition change
src/sql/10_…sql                cold open + reveal queries (SQL editor)
src/sql/11_…sql                story queries (rehearsal + Genie fallback)
src/sql/12_…sql                optional row filter (governance moment)
metric_views/*.yaml            THE semantic layer
genie/genie_agent_setup.md     Genie Agent config, instructions, benchmarks, live script
dashboard/dashboard_build.md   AI/BI dashboard spec
app/                           Streamlit Store Cockpit
```

## Prerequisites

### Databricks (Azure)
- [ ] Unity Catalog workspace with **serverless** compute (jobs + SQL warehouse).
- [ ] A **serverless SQL warehouse**. Note its ID: SQL Warehouses → *your warehouse* → Connection details → HTTP path (the last segment).
- [ ] Permission to create a catalog, or an existing catalog with `CREATE SCHEMA`.
- [ ] **Publish Metric Views To Power BI** private preview. Your account team enrols the workspace, then a workspace admin turns it on: profile menu (top right) → **Previews** → search *Publish Metric Views* → On.
- [ ] Databricks Apps enabled, plus **user authorization** for apps (Settings → Advanced / Previews, depending on your workspace) so the app can query as the signed-in user.
- [ ] Databricks CLI ≥ 0.250 authenticated against the workspace (`databricks auth login --host https://adb-….azuredatabricks.net`).

### Power BI
- [ ] Demo workspace in **Premium per-user** (or Fabric/Premium capacity) license mode: Power BI → workspace → **Workspace settings → License info**.
- [ ] **XMLA endpoint = Read Write**: Admin portal → **Premium Per User** → XMLA endpoint (for PPU), or Admin portal → Capacity settings → *capacity* → Power BI workloads → XMLA Endpoint (for capacity).
- [ ] Entra consent for the **Databricks Dataset Publishing Integration** app. This happens on the first publish; you need a tenant admin if users can't consent themselves.
- [ ] For the scheduled republish: a **Power BI connection in Unity Catalog**: Catalog → ⚙ (gear) → **Connections** → **Create connection** → type *Power BI*. Grant yourself `USE CONNECTION`.

## Deploy
Everything is a bundle resource now: data jobs, metric views (via the setup job), the AI/BI
dashboard, the Genie space, the app (wired to the Genie space) and the Power BI publish job.

```bash
databricks bundle deploy --var warehouse_id=<id> \
  --var powerbi_workspace="<Power BI workspace name>" \
  --var powerbi_connection=<UC Power BI connection name>
databricks bundle run swirl_setup            # data + metric views (skip if already run)
databricks bundle run swirl_publish_powerbi  # creates / updates the Power BI semantic model
databricks bundle run swirl_cockpit          # starts the app
```
Tip: put the three vars under `targets.dev.variables` in databricks.yml so you don't retype them.

Order matters only the first time: the dashboard and Genie space need the metric views,
so run `swirl_setup` before you open them.

After the first Power BI publish, set SSO once in Power BI (semantic model → Settings →
Data source credentials → Edit credentials → OAuth2 → tick *Report viewers can only access
this data source with their own Power BI identities using DirectQuery*).

## Notes
- Window measures are *Experimental*. If your compute rejects them, `02_create_metric_views.py` recreates the view without them and prints what it dropped.
- Re-running the generator overwrites the tables. Numbers shift slightly with the date range, so rehearse with the data you'll present.
- Everything is fictional: stores, products, prices and customers.

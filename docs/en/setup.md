# Setup guide

This guide goes from an empty machine to the dashboard running on your own BigQuery. File and folder names follow the structure in the README.

## 1. Requirements

| Component | Notes |
|---|---|
| Python 3.11+ | `pip install -r requirements.txt` (faker, numpy, pandas pinned; scipy, statsmodels, pyarrow, google-cloud-bigquery, db-dtypes) |
| Google Cloud project with BigQuery | The free BigQuery sandbox works; in the sandbox, every table and view is deleted automatically after 60 days |
| Google Cloud CLI (`gcloud`, `bq`) | To create the dataset and load tables |
| Power BI Desktop | Needed only if you want to refresh the dashboard from your own data |

The generator needs a lot of RAM at full scale: a 4 GB machine cannot run it; Google Colab can.

**Versions verified for reproduction** (13/11/2026, Google Colab): Python 3.13.18 · Faker 40.54.0 · pandas 2.2.3 · numpy 2.4.6, pinned in `requirements.txt`. Do not upgrade Faker: customer birth dates are generated with a Faker function, and the way it consumes random numbers can change between versions.

## 2. Configuration

**Authentication.** On your own machine:

```bash
gcloud auth login
gcloud auth application-default login     # for the Python libraries
gcloud config set project YOUR_PROJECT
```

On Colab: `from google.colab import auth; auth.authenticate_user()`.

**Create the dataset.** The original project uses location `asia-southeast1`. Any location works, as long as every table and view sits in the same dataset.

```bash
bq --location=asia-southeast1 mk -f --dataset YOUR_PROJECT:JM_Synthetic_Data     # -f: no error if it already exists
```

**Change the project name.** The name `jm-synthetic-data.JM_Synthetic_Data` is written directly into the code in these places:

| File | What to change |
|---|---|
| Every `sql/*.sql` file | The string `jm-synthetic-data.JM_Synthetic_Data` |
| Every `models/*.py` file | No code change: set the environment variables `export JM_PROJECT=YOUR_PROJECT JM_DATASET=YOUR_DATASET` |

```bash
sed -i 's/jm-synthetic-data\.JM_Synthetic_Data/YOUR_PROJECT.YOUR_DATASET/g' sql/*.sql
# macOS: sed -i '' 's/.../.../g' sql/*.sql
```

## 3. Generate the data and run the quality checks

```bash
python data-generator/generate_data.py      # writes to the folder jm_synthetic_data_v2/
python data-generator/qa_checks.py          # must finish with 0 FAIL
```

The seed is fixed (42), and so is the reference date for anything computed "from today" (`generation_date` = 7 September 2026 in `CONFIG`). A run on any date therefore reproduces the dataset used in the report, with the library versions in section 1. Verified on 13/11/2026: the 6 source tables match the reference dataset in every row and every column, except the columns that record the machine time of the run ([Reference dataset](reference-dataset.md)). `WARN` is a warning to review, not a blocker.

## 4. Load the 8 tables into BigQuery

Use `--replace` and `--autodetect` for every table. `--replace` replaces the whole existing table, so rerunning this step does not duplicate data. BigQuery infers the schema again on every load; for this dataset the schema is identical across loads (verified). The SQL in this repository is written against the types BigQuery infers (for example `bill_type` is INT64, `mobile` is INT64), so do not declare a different schema yourself.

**Tables with nested columns (NDJSON).** The list of products on each invoice is kept as an array (`ARRAY<STRUCT>`); the SQL unpacks it with `UNNEST`, so there is no need to flatten it first.

```bash
D=YOUR_PROJECT:JM_Synthetic_Data
O=jm_synthetic_data_v2
bq load --replace --source_format=NEWLINE_DELIMITED_JSON --autodetect $D.bills_raw           $O/retail_data/bills_raw.ndjson
bq load --replace --source_format=NEWLINE_DELIMITED_JSON --autodetect $D.orders_raw          $O/order_data/orders_raw.ndjson
bq load --replace --source_format=NEWLINE_DELIMITED_JSON --autodetect $D.nhanh_products_full $O/product_data/nhanh_products_full.ndjson
```

**Flat tables (CSV).**

```bash
for t in shop_data/depots product_data/nhanh_categories product_data/nhanh_internal_categories \
         customer_data/nhanh_customers_full customer_data/t_customer_tier_final; do
  bq load --replace --source_format=CSV --autodetect --skip_leading_rows=1 $D.$(basename $t) $O/$t.csv
done
```

**Expected row counts:** `bills_raw` 542,301 · `orders_raw` 417,981 · `nhanh_products_full` 7,213 · `nhanh_customers_full` 39,534 · `depots` 32. If any count differs, stop and recheck step 3.

## 5. Build tables and views in order

| Step | Run | Creates |
|---:|---|---|
| 1 | `sql/01_staging_views.sql` | `stg_offline_revenue`, `stg_online_revenue` |
| 2 | `sql/02_core_views.sql` | `fct_retail_revenue`, `dim_price_band`, `fct_product_revenue` |
| 3 | `sql/03_derived_tables.sql` | `customer_analytic_base`, `dim_platform_fee` |
| 4 | One of the two options below | `customer_clv` (38,446 rows) |
| 5 | `sql/04_analysis_views.sql` | 4 views used during the analysis |
| 6 | `sql/05_powerbi_views.sql` | 7 `pbi_*` views; `pbi_dim_khach` needs `customer_clv` from step 4 |

**Step 4 — the CLV table, choose one option:**

- **Reproduce the report's figures exactly:** load the reference table.
  ```bash
  bq load --replace --source_format=PARQUET $D.customer_clv data/reference/customer_clv.parquet
  ```
- **Rerun the model yourself:** `python models/clv_model.py`, then `python models/upload_clv.py`. The model is written in scipy (the `lifetimes` library used originally does not run with numpy 2.x) and follows the same formulas and the same optimisation objective as `lifetimes`. Add `--compare <project.dataset.customer_clv>` to compare with the reference table. Result of the check on 13/11/2026, over the 32,118 customers with a CLV: Spearman rank correlation 0.9998, 97.2% of customers in the same decile, 100% within one decile, total CLV 1.0% above the reference table.

The scripts read directly from BigQuery rather than from a downloaded file: the download button in the BigQuery console only exports about 273,000 rows, while the CLV input has 706,121 rows.

**Optional:** `python models/promo_uplift.py` reruns the promotion model from section 4 of the report. The dashboard does not need this step.

After step 6, run the check figures written in `05_powerbi_views.sql`. For example, `pbi_giao_dich` must have 826,943 rows, and revenue for Jan–Aug 2026 must be VND 203,716,541,898. Both figures match exactly with the library versions in section 1; if they differ, check the versions before checking the SQL.

## 6. Open the dashboard

1. Open `dashboard/jm-dashboard.pbix` in Power BI Desktop.
2. **Transform data → Data source settings → Change Source**, and select your project.
3. **Refresh**, then reconcile the figures with section 4 of the [Technical documentation](technical-notes.md).

Four small static tables (waterfall, dead SKUs, promotion calendar, uplift) are entered directly in the `.pbix` and do not need refreshing.

The dashboard, view names (`pbi_giao_dich`, `pbi_dim_khach`, …) and some column names are in Vietnamese.

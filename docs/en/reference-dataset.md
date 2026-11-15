# Reference dataset

The dataset used to run the SQL, build the dashboard and compute every figure in the report. This document records what is known for certain about it, so that anyone rerunning the project has something to check against.

## Generation details

| Item | Value |
|---|---|
| Generated at | 7 September 2026, 16:21 UTC (read from the `synced_at` column) |
| Seed | 42 |
| Reference date for anything computed "from today" | 7 September 2026 (`CONFIG["generation_date"]`) |
| Python and library versions at generation | Unknown: the original Colab session was not saved |
| Generator source at generation | The original file was not kept; the version in this repository is a rebuild, verified to reproduce the dataset (below) |

## Reproduction check (13/11/2026)

The generator in this repository was run with Python 3.13.18, Faker 40.54.0, pandas 2.2.3 and numpy 2.4.6, then compared with the reference tables in BigQuery.

| Table | Rows | Reference fingerprint | Rerun |
|---|---:|---:|---|
| `bills_raw` | 542,301 | −4569247701102636566 | Match |
| `orders_raw` | 417,981 | 8827476989136951127 | Match |
| `nhanh_products_full` | 7,213 | 8790336357152967021 | Match |
| `depots` | 32 | −4171054977091630743 | Match |
| `nhanh_categories` | 7 | 1884346674075919173 | Match |
| `nhanh_internal_categories` | 20 | 4999991797804160506 | Match |

- **Fingerprint** = `BIT_XOR(FARM_FINGERPRINT(TO_JSON_STRING(row)))` in BigQuery, over every column except those that record the machine time of the run: `synced_at` (`bills_raw`, `orders_raw`, `depots`), `updated_at` (`nhanh_products_full`) and `_loaded_at` (the two category tables). Business date columns such as `bill_datetime`, `created_at` and `sync_batch` are kept.
- **The two customer tables** `nhanh_customers_full` and `t_customer_tier_final` are no longer in the reference BigQuery dataset (they were replaced by the derived table `customer_analytic_base`). They were checked **indirectly** only: name, birth date and loyalty tier of all 39,531 customers match `customer_analytic_base`. Columns that did not go into the derived table (for example points and gender) have not been checked.
- The generator was run twice and the tables loaded into BigQuery twice (`--replace`): row counts and schemas did not change.

## Derived tables in the reference dataset

| Table | Rows | Fingerprint (all columns) |
|---|---:|---:|
| `customer_analytic_base` | 39,531 | 1323647500215354808 |
| `customer_clv` | 38,446 | 3320820529174453961 |
| `dim_platform_fee` | 12 | 6860662034617566833 |

## Key check figures

- Revenue for Jan–Aug 2026 (`fct_retail_revenue`): **VND 203,716,541,898** across 164,384 transactions.
- A Parquet copy of the 9 tables above (6 source tables and 3 derived tables) is kept separately by the author, because tables in the BigQuery sandbox are deleted automatically after 60 days.

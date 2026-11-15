"""
Nạp kết quả CLV (clv_output.csv do models/clv_model.py ghi ra) lên BigQuery thành bảng `customer_clv`.

Thêm hai cột:
  clv_decile    : chia khách có CLV thành 10 nhóm bằng nhau theo CLV giảm dần (như NTILE(10));
                  decile 1 = CLV cao nhất. Khách mua đúng một ngày (frequency = 0) không có CLV,
                  để NULL — không gán 0 hay 10.
  snapshot_date : 2026-08-31.
Bảng được ghi đè (WRITE_TRUNCATE).

Chạy:
    export JM_PROJECT=your-project JM_DATASET=your_dataset   # mặc định: bộ gốc
    python models/upload_clv.py

Muốn ra đúng bảng của bộ tham chiếu thay vì chạy lại mô hình, nạp thẳng file Parquet:
    bq load --replace --source_format=PARQUET your_dataset.customer_clv data/reference/customer_clv.parquet
"""
import os

import pandas as pd
from google.cloud import bigquery

PROJECT = os.environ.get("JM_PROJECT", "jm-synthetic-data")
DATASET = os.environ.get("JM_DATASET", "JM_Synthetic_Data")
CSV_PATH = "clv_output.csv"
SNAPSHOT_DATE = "2026-08-31"
TABLE_ID = f"{PROJECT}.{DATASET}.customer_clv"

# Số kiểm của bộ dữ liệu tham chiếu
N_ROWS_EXPECTED = 38_446
N_NULL_CLV_EXPECTED = 6_328

COLS = ["customer_id", "frequency", "recency", "T", "monetary_value",
        "predicted_purchases", "prob_alive", "expected_avg_value", "clv"]


def fail(msg):
    raise SystemExit(f"\n[DỪNG] {msg}\n")


df = pd.read_csv(CSV_PATH)
missing = [c for c in COLS if c not in df.columns]
if missing:
    fail(f"Thiếu cột: {missing}")

n_null = int(df["clv"].isna().sum())
print(f"{len(df):,} dòng · {n_null:,} khách không có CLV "
      f"(tham chiếu {N_ROWS_EXPECTED:,} / {N_NULL_CLV_EXPECTED:,})")
if int(((df["frequency"] == 0) != df["clv"].isna()).sum()) != 0:
    fail("Nhóm CLV rỗng phải trùng đúng nhóm frequency = 0.")

# clv_decile: ((hạng − 1) × 10) // n + 1 cho đúng cách NTILE chia phần dư vào các nhóm đầu
mask = df["clv"].notna()
n_ranked = int(mask.sum())
rank = df.loc[mask, "clv"].rank(method="first", ascending=False).astype("int64")
df["clv_decile"] = pd.NA
df.loc[mask, "clv_decile"] = ((rank - 1) * 10) // n_ranked + 1
df["clv_decile"] = df["clv_decile"].astype("Int64")

mean_by_decile = df.loc[mask].groupby("clv_decile")["clv"].mean()
if not (mean_by_decile.idxmax() == 1 and mean_by_decile.idxmin() == 10):
    fail("clv_decile bị ngược chiều: decile 1 phải là nhóm CLV cao nhất.")

df["snapshot_date"] = pd.to_datetime(SNAPSHOT_DATE).date()
for c in ["customer_id", "frequency", "recency", "T"]:
    df[c] = df[c].astype("Int64")
for c in ["monetary_value", "predicted_purchases", "prob_alive", "expected_avg_value", "clv"]:
    df[c] = df[c].astype("float64")
df = df[COLS + ["clv_decile", "snapshot_date"]]

schema = [bigquery.SchemaField("customer_id", "INT64", mode="REQUIRED")] + \
         [bigquery.SchemaField(c, "INT64") for c in ["frequency", "recency", "T"]] + \
         [bigquery.SchemaField(c, "FLOAT64") for c in
          ["monetary_value", "predicted_purchases", "prob_alive", "expected_avg_value", "clv"]] + \
         [bigquery.SchemaField("clv_decile", "INT64"),
          bigquery.SchemaField("snapshot_date", "DATE", mode="REQUIRED")]

client = bigquery.Client(project=PROJECT)
job = client.load_table_from_dataframe(
    df, TABLE_ID, job_config=bigquery.LoadJobConfig(schema=schema, write_disposition="WRITE_TRUNCATE"))
job.result()

r = client.query(f"""
select count(*) n, countif(clv is null) n_null,
       countif((clv is null) != (clv_decile is null)) loi_decile, count(distinct customer_id) n_khach
from `{TABLE_ID}`""").result().to_dataframe().iloc[0]
print(f"Đã nạp {TABLE_ID}: {r.n:,} dòng · {r.n_null:,} CLV rỗng · {r.n_khach:,} khách · lỗi decile {r.loi_decile}")
if r.loi_decile != 0 or r.n != r.n_khach:
    fail("Kiểm sau khi nạp không đạt.")
print("[OK]")

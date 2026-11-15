# Hướng dẫn tái dựng

Tài liệu này đi từ một máy chưa có gì đến dashboard chạy trên BigQuery của bạn. Tên file và thư mục theo cấu trúc trong README.

## 1. Cần có

| Thành phần | Ghi chú |
|---|---|
| Python 3.11+ | `pip install -r requirements.txt` (faker, numpy, pandas đã pin; scipy, statsmodels, pyarrow, google-cloud-bigquery, db-dtypes) |
| Google Cloud project có BigQuery | BigQuery sandbox miễn phí dùng được; ở sandbox, mọi bảng và view tự xóa sau 60 ngày |
| Google Cloud CLI (`gcloud`, `bq`) | Để tạo dataset và nạp bảng |
| Power BI Desktop | Chỉ cần nếu muốn refresh dashboard từ dữ liệu của bạn |

Generator cần nhiều RAM ở quy mô đầy đủ: máy 4 GB không chạy được, Google Colab chạy được.

**Phiên bản đã kiểm tái lập** (13/11/2026, Google Colab): Python 3.13.18 · Faker 40.54.0 · pandas 2.2.3 · numpy 2.4.6, đã pin trong `requirements.txt`. Đừng nâng phiên bản Faker: ngày sinh khách được sinh bằng một hàm của Faker, và cách hàm này dùng số ngẫu nhiên có thể đổi giữa các phiên bản.

## 2. Cấu hình

**Xác thực.** Trên máy cá nhân:

```bash
gcloud auth login
gcloud auth application-default login     # cho thư viện Python
gcloud config set project YOUR_PROJECT
```

Trên Colab: `from google.colab import auth; auth.authenticate_user()`.

**Tạo dataset.** Dự án gốc dùng location `asia-southeast1`. Location nào cũng được, miễn là mọi bảng và view nằm cùng một dataset.

```bash
bq --location=asia-southeast1 mk -f --dataset YOUR_PROJECT:JM_Synthetic_Data     # -f: không báo lỗi nếu đã có
```

**Đổi tên project.** Tên `jm-synthetic-data.JM_Synthetic_Data` được ghi trực tiếp trong code ở các chỗ sau:

| File | Cần đổi |
|---|---|
| Mọi file `sql/*.sql` | Chuỗi `jm-synthetic-data.JM_Synthetic_Data` |
| Mọi file `models/*.py` | Không sửa code: đặt biến môi trường `export JM_PROJECT=YOUR_PROJECT JM_DATASET=YOUR_DATASET` |

```bash
sed -i 's/jm-synthetic-data\.JM_Synthetic_Data/YOUR_PROJECT.YOUR_DATASET/g' sql/*.sql
# macOS: sed -i '' 's/.../.../g' sql/*.sql
```

## 3. Sinh dữ liệu và kiểm chất lượng

```bash
python data-generator/generate_data.py      # ghi ra thư mục jm_synthetic_data_v2/
python data-generator/qa_checks.py          # phải kết thúc bằng 0 FAIL
```

Seed cố định (42) và ngày gốc cố định cho các phép tính "tính từ hôm nay" (`generation_date` = 07/09/2026 trong `CONFIG`), nên chạy lại vào ngày nào cũng ra đúng bộ dữ liệu đã dùng trong báo cáo, với các phiên bản thư viện ở mục 1. Đã kiểm ngày 13/11/2026: 6 bảng nguồn khớp bộ dữ liệu tham chiếu ở mọi dòng và mọi cột, trừ các cột ghi giờ máy lúc chạy ([Bộ dữ liệu tham chiếu](reference-dataset.md)). `WARN` là cảnh báo cần xem, không chặn.

## 4. Nạp 8 bảng lên BigQuery

Dùng `--replace` và `--autodetect` cho mọi bảng. `--replace` thay toàn bộ bảng cũ, nên chạy lại bước này không làm nhân đôi dữ liệu. BigQuery suy lại schema mỗi lần nạp; với bộ dữ liệu này, schema giống nhau qua các lần nạp (đã kiểm). SQL trong repo viết theo kiểu dữ liệu mà BigQuery tự suy ra (ví dụ `bill_type` là INT64, `mobile` là INT64), nên đừng tự khai schema khác.

**Bảng có cột lồng (NDJSON).** Danh sách sản phẩm trong hóa đơn được giữ nguyên dạng mảng (`ARRAY<STRUCT>`); SQL tách bằng `UNNEST`, không cần làm phẳng trước.

```bash
D=YOUR_PROJECT:JM_Synthetic_Data
O=jm_synthetic_data_v2
bq load --replace --source_format=NEWLINE_DELIMITED_JSON --autodetect $D.bills_raw           $O/retail_data/bills_raw.ndjson
bq load --replace --source_format=NEWLINE_DELIMITED_JSON --autodetect $D.orders_raw          $O/order_data/orders_raw.ndjson
bq load --replace --source_format=NEWLINE_DELIMITED_JSON --autodetect $D.nhanh_products_full $O/product_data/nhanh_products_full.ndjson
```

**Bảng phẳng (CSV).**

```bash
for t in shop_data/depots product_data/nhanh_categories product_data/nhanh_internal_categories \
         customer_data/nhanh_customers_full customer_data/t_customer_tier_final; do
  bq load --replace --source_format=CSV --autodetect --skip_leading_rows=1 $D.$(basename $t) $O/$t.csv
done
```

**Số dòng kỳ vọng:** `bills_raw` 542.301 · `orders_raw` 417.981 · `nhanh_products_full` 7.213 · `nhanh_customers_full` 39.534 · `depots` 32. Lệch là dừng lại, kiểm bước 3.

## 5. Dựng bảng và view theo thứ tự

| Bước | Chạy | Tạo ra |
|---:|---|---|
| 1 | `sql/01_staging_views.sql` | `stg_offline_revenue`, `stg_online_revenue` |
| 2 | `sql/02_core_views.sql` | `fct_retail_revenue`, `dim_price_band`, `fct_product_revenue` |
| 3 | `sql/03_derived_tables.sql` | `customer_analytic_base`, `dim_platform_fee` |
| 4 | Một trong hai cách bên dưới | `customer_clv` (38.446 dòng) |
| 5 | `sql/04_analysis_views.sql` | 4 view dùng trong giai đoạn phân tích |
| 6 | `sql/05_powerbi_views.sql` | 7 view `pbi_*`; `pbi_dim_khach` cần `customer_clv` từ bước 4 |

**Bước 4 — bảng CLV, chọn một cách:**

- **Ra đúng số trong báo cáo:** nạp bảng của bộ tham chiếu.
  ```bash
  bq load --replace --source_format=PARQUET $D.customer_clv data/reference/customer_clv.parquet
  ```
- **Tự chạy lại mô hình:** `python models/clv_model.py`, rồi `python models/upload_clv.py`. Mô hình viết bằng scipy (thư viện `lifetimes` dùng ở bản gốc không chạy được với numpy 2.x), làm theo cùng công thức và cùng cách tối ưu với `lifetimes`. Thêm `--compare <project.dataset.customer_clv>` để so với bảng tham chiếu. Kết quả kiểm 13/11/2026 trên 32.118 khách có CLV: tương quan thứ hạng Spearman 0,9998, 97,2% khách cùng decile, 100% lệch tối đa 1 decile, tổng CLV cao hơn bảng tham chiếu 1,0%.

Script đọc thẳng từ BigQuery, không qua file tải về: nút tải kết quả của BigQuery console chỉ lấy khoảng 273 nghìn dòng, trong khi đầu vào CLV có 706.121 dòng.

**Tùy chọn:** `python models/promo_uplift.py` chạy lại mô hình khuyến mãi của báo cáo mục 4. Dashboard không cần bước này.

Sau bước 6, chạy các số kiểm ghi trong `05_powerbi_views.sql`. Ví dụ `pbi_giao_dich` phải có 826.943 dòng, doanh thu T1–T8/2026 là 203.716.541.898 đ. Hai con số này khớp chính xác khi dùng đúng phiên bản thư viện ở mục 1; nếu lệch, kiểm lại phiên bản trước khi kiểm SQL.

## 6. Mở dashboard

1. Mở `dashboard/jm-dashboard.pbix` bằng Power BI Desktop.
2. **Transform data → Data source settings → Change Source**, chọn project của bạn.
3. **Refresh**, rồi đối chiếu số theo [Tài liệu kỹ thuật](technical-notes.md) mục 4.

Bốn bảng tĩnh nhỏ (waterfall, SKU chết, lịch khuyến mãi, uplift) được nhập thẳng trong `.pbix`, không cần refresh.

# Bộ dữ liệu tham chiếu

Bộ dữ liệu đã dùng để chạy SQL, dựng dashboard và tính mọi con số trong báo cáo. Tài liệu này ghi lại những gì biết chắc về nó, để người chạy lại có điểm đối chiếu.

## Thông tin sinh dữ liệu

| Mục | Giá trị |
|---|---|
| Thời điểm sinh | 07/09/2026, 16:21 UTC (đọc từ cột `synced_at`) |
| Seed | 42 |
| Ngày gốc cho phép tính "tính từ hôm nay" | 07/09/2026 (`CONFIG["generation_date"]`) |
| Phiên bản Python và thư viện lúc sinh | Không rõ: phiên Colab gốc không lưu lại |
| Mã nguồn generator lúc sinh | Không còn bản gốc; bản trong repo là bản dựng lại và đã kiểm tái lập (bên dưới) |

## Kiểm tái lập (13/11/2026)

Chạy generator trong repo với Python 3.13.18, Faker 40.54.0, pandas 2.2.3, numpy 2.4.6, rồi so với bộ tham chiếu trên BigQuery.

| Bảng | Số dòng | Dấu vân tay tham chiếu | Bản chạy lại |
|---|---:|---:|---|
| `bills_raw` | 542.301 | −4569247701102636566 | Khớp |
| `orders_raw` | 417.981 | 8827476989136951127 | Khớp |
| `nhanh_products_full` | 7.213 | 8790336357152967021 | Khớp |
| `depots` | 32 | −4171054977091630743 | Khớp |
| `nhanh_categories` | 7 | 1884346674075919173 | Khớp |
| `nhanh_internal_categories` | 20 | 4999991797804160506 | Khớp |

- **Dấu vân tay** = `BIT_XOR(FARM_FINGERPRINT(TO_JSON_STRING(dòng)))` trên BigQuery, tính trên mọi cột trừ các cột ghi giờ máy lúc chạy: `synced_at` (`bills_raw`, `orders_raw`, `depots`), `updated_at` (`nhanh_products_full`), `_loaded_at` (hai bảng danh mục). Các cột ngày nghiệp vụ như `bill_datetime`, `created_at`, `sync_batch` được giữ lại.
- **Hai bảng khách** `nhanh_customers_full` và `t_customer_tier_final` không còn trên BigQuery tham chiếu (đã thay bằng bảng dẫn xuất `customer_analytic_base`). Chúng chỉ được **đối chiếu gián tiếp**: tên, ngày sinh và hạng thẻ của 39.531 khách khớp với `customer_analytic_base`. Các cột không đi vào bảng dẫn xuất (ví dụ điểm, giới tính) chưa được đối chiếu.
- Chạy generator hai lần, nạp BigQuery hai lần (`--replace`): số dòng và schema không đổi.

## Bảng dẫn xuất trong bộ tham chiếu

| Bảng | Số dòng | Dấu vân tay (mọi cột) |
|---|---:|---:|
| `customer_analytic_base` | 39.531 | 1323647500215354808 |
| `customer_clv` | 38.446 | 3320820529174453961 |
| `dim_platform_fee` | 12 | 6860662034617566833 |

## Số kiểm chính

- Doanh thu T1–T8/2026 (`fct_retail_revenue`): **203.716.541.898 đ** trên 164.384 giao dịch.
- Bản sao Parquet của 9 bảng trên (6 bảng nguồn và 3 bảng dẫn xuất) được tác giả lưu riêng, vì bảng trên BigQuery sandbox tự xóa sau 60 ngày.

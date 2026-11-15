-- =============================================================================
-- 03 · Bảng dẫn xuất (bảng vật lý, tính một lần rồi dùng lại)
-- Cần có: 02_core_views.sql, nhanh_customers_full, t_customer_tier_final
-- Tạo ra: customer_analytic_base, dim_platform_fee
-- =============================================================================

-- Bảng khách phân tích: một dòng mỗi khách định danh (bỏ 3 tài khoản dùng chung id 1, 2, 3).
-- RFM tính trên cả hai kênh, kèm cột tách theo kênh; hạng thẻ lấy từ nhanh_customers_full,
-- phân hạng khách lấy từ t_customer_tier_final. Sau bước này, mọi phân tích khách đọc từ bảng này.
CREATE OR REPLACE TABLE `jm-synthetic-data.JM_Synthetic_Data.customer_analytic_base` AS
WITH rfm_all AS (
  SELECT
    customer_id,
    MAX(transaction_date) AS last_purchase_date,
    COUNT(DISTINCT transaction_id) AS frequency,
    SUM(revenue_net) AS monetary
  FROM `jm-synthetic-data.JM_Synthetic_Data.fct_retail_revenue`
  WHERE customer_id NOT IN (1, 2, 3)
  GROUP BY customer_id
),
rfm_offline AS (
  SELECT
    customer_id,
    COUNT(DISTINCT transaction_id) AS frequency_offline,
    SUM(revenue_net) AS monetary_offline
  FROM `jm-synthetic-data.JM_Synthetic_Data.fct_retail_revenue`
  WHERE customer_id NOT IN (1, 2, 3) AND channel = 'offline'
  GROUP BY customer_id
),
rfm_online AS (
  SELECT
    customer_id,
    COUNT(DISTINCT transaction_id) AS frequency_online,
    SUM(revenue_net) AS monetary_online
  FROM `jm-synthetic-data.JM_Synthetic_Data.fct_retail_revenue`
  WHERE customer_id NOT IN (1, 2, 3) AND channel = 'online'
  GROUP BY customer_id
),
anchor AS (
  SELECT MAX(transaction_date) AS anchor_date
  FROM `jm-synthetic-data.JM_Synthetic_Data.fct_retail_revenue`
)
SELECT
  c.id AS customer_id,
  c.name AS customer_name,
  c.mobile,
  c.birthday,
  c.membership_tier,

  -- RFM trên cả hai kênh
  DATE_DIFF((SELECT anchor_date FROM anchor), r.last_purchase_date, DAY) AS recency_days,
  IFNULL(r.frequency, 0) AS frequency,
  IFNULL(r.monetary, 0) AS monetary,

  -- Tách theo kênh
  IFNULL(ro.frequency_offline, 0) AS frequency_offline,
  IFNULL(ro.monetary_offline, 0) AS monetary_offline,
  IFNULL(rn.frequency_online, 0) AS frequency_online,
  IFNULL(rn.monetary_online, 0) AS monetary_online,

  t.Potential_Tier,
  t.Activity_Status,
  t.Final_Tier
FROM `jm-synthetic-data.JM_Synthetic_Data.nhanh_customers_full` c
LEFT JOIN rfm_all     r  ON c.id = r.customer_id
LEFT JOIN rfm_offline ro ON c.id = ro.customer_id
LEFT JOIN rfm_online  rn ON c.id = rn.customer_id
LEFT JOIN `jm-synthetic-data.JM_Synthetic_Data.t_customer_tier_final` t ON c.id = t.customer_id
WHERE c.id NOT IN (1, 2, 3);
-- Số kiểm: 39.531 dòng.

-- Biểu phí sàn theo khoảng hiệu lực: mỗi dòng là một khoản phí của một sàn trong một khoảng thời gian.
-- Khớp biểu phí trong generator (PLATFORM_FEES). Facebook, Instagram, Website, Admin không có phí sàn.
--   ti_le            : phí theo % giá trị đơn (NULL nếu là phí cố định)
--   phi_co_dinh_vnd  : phí cố định mỗi đơn, VNĐ (NULL nếu là phí theo %)
--   hoan_khi_tra     : phí được sàn hoàn lại khi khách trả hàng
--   hieu_luc_den NULL: còn hiệu lực đến nay
--   do_tin_cay       : XÁC NHẬN = có nguồn công khai; SUY LUẬN = chưa xác nhận được
CREATE OR REPLACE TABLE `jm-synthetic-data.JM_Synthetic_Data.dim_platform_fee` AS
SELECT * FROM UNNEST([
  STRUCT<sale_channel STRING, loai_phi STRING, thu_tu INT64, hieu_luc_tu DATE, hieu_luc_den DATE,
         ti_le NUMERIC, phi_co_dinh_vnd INT64, hoan_khi_tra BOOL, muc_hien_thi STRING, do_tin_cay STRING>
  ('Shopee',      'Phí giao dịch', 1, DATE '2024-01-01', DATE '2025-06-30', 0.04,   NULL, FALSE, '4%',          'XÁC NHẬN'),
  ('Shopee',      'Phí giao dịch', 1, DATE '2025-07-01', DATE '2026-04-30', 0.0491, NULL, FALSE, '4,91%',       'XÁC NHẬN'),
  ('Shopee',      'Phí giao dịch', 1, DATE '2026-05-01', NULL,              0.06,   NULL, FALSE, '6%',          'XÁC NHẬN'),
  ('Shopee',      'Hoa hồng',      2, DATE '2024-01-01', NULL,              0.03,   NULL, TRUE,  '3%',          'SUY LUẬN'),
  ('TikTok Shop', 'Phí giao dịch', 1, DATE '2024-01-01', DATE '2026-05-08', 0.05,   NULL, FALSE, '5%',          'XÁC NHẬN'),
  ('TikTok Shop', 'Phí giao dịch', 1, DATE '2026-05-09', NULL,              0.06,   NULL, FALSE, '6%',          'XÁC NHẬN'),
  ('TikTok Shop', 'Hoa hồng',      2, DATE '2024-01-01', DATE '2026-05-08', 0.08,   NULL, TRUE,  '8%',          'XÁC NHẬN'),
  ('TikTok Shop', 'Hoa hồng',      2, DATE '2026-05-09', NULL,              0.125,  NULL, TRUE,  '12,5%',       'XÁC NHẬN'),
  ('TikTok Shop', 'Phí xử lý đơn', 3, DATE '2025-10-27', NULL,              NULL,   3000, FALSE, '3.000 đ/đơn', 'XÁC NHẬN'),
  ('Lazada',      'Phí thanh toán',1, DATE '2024-01-01', NULL,              0.04,   NULL, FALSE, '4%',          'XÁC NHẬN'),
  ('Lazada',      'Phí cố định',   2, DATE '2024-01-01', NULL,              0.0399, NULL, TRUE,  '3,99%',       'XÁC NHẬN'),
  ('Lazada',      'Phí hạ tầng',   3, DATE '2024-01-01', NULL,              NULL,   2000, FALSE, '2.000 đ/đơn', 'XÁC NHẬN')
]);
-- Số kiểm: 12 dòng.

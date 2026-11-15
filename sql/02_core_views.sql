-- =============================================================================
-- 02 · Định nghĩa dùng chung: doanh thu (mỗi giao dịch) và doanh số (mỗi dòng hàng)
-- Cần có: 01_staging_views.sql, nhanh_products_full
-- Tạo ra: fct_retail_revenue, dim_price_band, fct_product_revenue
-- Mọi chỉ số doanh thu, doanh số trong dự án đọc từ hai view fct_* ở đây.
-- =============================================================================

-- Doanh thu: một dòng mỗi giao dịch, cả hai kênh.
-- revenue_net là doanh thu sau trả hàng; mọi báo cáo dùng cột này.
CREATE OR REPLACE VIEW `jm-synthetic-data.JM_Synthetic_Data.fct_retail_revenue` AS
select
  bill_id as transaction_id,
  bill_date as transaction_date,
  customer_id,
  'offline' as channel,
  store_name as diem_ban,
  revenue_contribution as revenue_gross,
  revenue_contribution as revenue_net
from `jm-synthetic-data.JM_Synthetic_Data.stg_offline_revenue`

union all

select
  order_id as transaction_id,
  cast(created_at as date) as transaction_date,
  customer_id,
  channel,
  sale_channel as diem_ban,
  cod_amount as revenue_gross,
  business_payment as revenue_net
from `jm-synthetic-data.JM_Synthetic_Data.stg_online_revenue`;

-- Phân khúc giá: chia dải giá niêm yết của từng dòng hàng thành ba phần bằng nhau.
CREATE OR REPLACE VIEW `jm-synthetic-data.JM_Synthetic_Data.dim_price_band` AS
select code, category_id, retail, price_band
from (
  select
    category_id,
    p.prices.retail,
    p.code,
    case p.category_id
      when 101 then -- Áo, niêm yết 250–650 nghìn
        case
          when p.prices.retail < 250000 + (650000-250000)*0.33 then 'Thấp'
          when p.prices.retail < 250000 + (650000-250000)*0.66 then 'Trung'
          else 'Cao'
        end
      when 102 then -- Đầm, 450–1.200 nghìn
        case
          when p.prices.retail < 450000 + (1200000-450000)*0.33 then 'Thấp'
          when p.prices.retail < 450000 + (1200000-450000)*0.66 then 'Trung'
          else 'Cao'
        end
      when 103 then -- Quần, 350–750 nghìn
        case
          when p.prices.retail < 350000 + (750000-350000)*0.33 then 'Thấp'
          when p.prices.retail < 350000 + (750000-350000)*0.66 then 'Trung'
          else 'Cao'
        end
      when 104 then -- Chân váy, 300–700 nghìn
        case
          when p.prices.retail < 300000 + (700000-300000)*0.33 then 'Thấp'
          when p.prices.retail < 300000 + (700000-300000)*0.66 then 'Trung'
          else 'Cao'
        end
      when 105 then -- Set bộ, 600–1.500 nghìn
        case
          when p.prices.retail < 600000 + (1500000-600000)*0.33 then 'Thấp'
          when p.prices.retail < 600000 + (1500000-600000)*0.66 then 'Trung'
          else 'Cao'
        end
      when 106 then -- Áo khoác, 700–1.800 nghìn
        case
          when p.prices.retail < 700000 + (1800000-700000)*0.33 then 'Thấp'
          when p.prices.retail < 700000 + (1800000-700000)*0.66 then 'Trung'
          else 'Cao'
        end
      when 107 then -- Phụ kiện, 150–350 nghìn
        case
          when p.prices.retail < 150000 + (350000-150000)*0.33 then 'Thấp'
          when p.prices.retail < 150000 + (350000-150000)*0.66 then 'Trung'
          else 'Cao'
        end
    end as price_band
  from `jm-synthetic-data.JM_Synthetic_Data.nhanh_products_full` p
);

-- Doanh số: một dòng mỗi dòng hàng đã bán (sau giảm giá, trước trả hàng).
-- Chỉ lấy phiếu bán offline và đơn "Giao hàng tận nhà": phiếu trả offline và dòng trả online
-- cũng mang danh sách sản phẩm (số dương); không lọc theo loại chứng từ thì doanh số bị cộng trùng
-- (lỗi này từng làm doanh số online dư 11,1%).
CREATE OR REPLACE VIEW `jm-synthetic-data.JM_Synthetic_Data.fct_product_revenue` AS
select
  b.bill_id as transaction_id,
  b.bill_date as transaction_date,
  'offline' as channel,
  p.code,
  p2.category_id,
  p2.internal_category_id,
  regexp_extract(p.code, r'^([A-Z0-9]+\.[0-9]+)-[A-Z]{2}-[A-Za-z0-9]+$') as product_line,  -- mã sản phẩm cha
  p.quantity,
  (p.price * p.quantity - p.discount) as revenue_gross_line,
  p.discount as discount_line,
  p2.prices.avg_cost * p.quantity as cost_line,
  p2.status
from `jm-synthetic-data.JM_Synthetic_Data.bills_raw` b, unnest(b.products) as p
join `jm-synthetic-data.JM_Synthetic_Data.nhanh_products_full` p2 on p.id = p2.id
where b.bill_id in (select bill_id from `jm-synthetic-data.JM_Synthetic_Data.stg_offline_revenue`)
  and b.bill_type = 2

union all

select
  o.order_id as transaction_id,
  cast(o.created_at as date) as transaction_date,
  'online' as channel,
  p.code,
  p2.category_id,
  p2.internal_category_id,
  regexp_extract(p.code, r'^([A-Z0-9]+\.[0-9]+)-[A-Z]{2}-[A-Za-z0-9]+$') as product_line,
  p.quantity,
  (p.price * p.quantity - p.discount) as revenue_gross_line,
  p.discount as discount_line,
  p2.prices.avg_cost * p.quantity as cost_line,
  p2.status
from `jm-synthetic-data.JM_Synthetic_Data.orders_raw` o, unnest(o.products) as p
join `jm-synthetic-data.JM_Synthetic_Data.nhanh_products_full` p2 on p.id = p2.id
where o.order_id in (select order_id from `jm-synthetic-data.JM_Synthetic_Data.stg_online_revenue`)
  and o.order_type = 'Giao hàng tận nhà';

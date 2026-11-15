-- =============================================================================
-- 04 · View dùng trong giai đoạn phân tích (trước khi dựng dashboard)
-- Cần có: 02_core_views.sql
-- Tạo ra: dim_diem_ban, dim_product, fct_offline_bill, fct_online_order
-- Dashboard không đọc các view này; chúng được giữ để chạy lại các truy vấn phân tích.
-- =============================================================================

-- Điểm bán: cửa hàng (kèm nhóm thị trường, mặt bằng, vị trí) và các sàn online.
CREATE OR REPLACE VIEW `jm-synthetic-data.JM_Synthetic_Data.dim_diem_ban` AS
select
  d.name                    as diem_ban,
  'offline'                 as channel,
  cast(d.id as string)      as depot_id,
  d.city_name               as tinh_thanh,
  case
    when d.city_name = 'Hà Nội'                            then 'Tier 1'
    when d.city_name like '%Hồ Chí Minh%'
      or d.city_name like '%HCM%'
      or d.city_name like '%Hải Phòng%'
      or d.city_name like '%Đà Nẵng%'                      then 'Tier 2'
    else 'Tier 3'
  end                       as jm_operational_tier,
  d.store_format,
  d.location_type
from `jm-synthetic-data.JM_Synthetic_Data.depots` d
where d.name in (
  select distinct diem_ban
  from `jm-synthetic-data.JM_Synthetic_Data.fct_retail_revenue`
  where channel = 'offline'
)

union all

select distinct
  diem_ban,
  'online',
  cast(null as string),
  cast(null as string),
  cast(null as string),
  cast(null as string),
  cast(null as string)
from `jm-synthetic-data.JM_Synthetic_Data.fct_retail_revenue`
where channel = 'online';

-- Sản phẩm: mã SKU, mã cha, dòng hàng, BST, phân khúc giá.
CREATE OR REPLACE VIEW `jm-synthetic-data.JM_Synthetic_Data.dim_product` AS
select
  p.id                                                                   as product_id,
  p.code,
  regexp_extract(p.code, r'^([A-Z0-9]+\.[0-9]+)-[A-Z]{2}-[A-Za-z0-9]+$') as product_line,
  c.name                                                                 as category,
  bst.name                                                               as bst,
  pb.price_band,
  p.prices.retail                                                        as gia_niem_yet
from `jm-synthetic-data.JM_Synthetic_Data.nhanh_products_full` p
left join `jm-synthetic-data.JM_Synthetic_Data.nhanh_categories` c
  on c.id = p.category_id
left join `jm-synthetic-data.JM_Synthetic_Data.nhanh_internal_categories` bst
  on bst.id = p.internal_category_id
left join `jm-synthetic-data.JM_Synthetic_Data.dim_price_band` pb
  on pb.code = p.code;

-- Phiếu offline: doanh thu và số món mỗi phiếu.
CREATE OR REPLACE VIEW `jm-synthetic-data.JM_Synthetic_Data.fct_offline_bill` AS
select
  s.bill_id,
  cast(s.bill_date as date)                                      as transaction_date,
  s.customer_id,
  s.store_name                                                   as diem_ban,
  s.bill_type,
  case s.bill_type when 2 then 'Bán' when 1 then 'Trả' end       as loai_phieu,
  s.sale_user_id,
  s.sale_user_name,
  s.revenue_contribution                                         as revenue_net,
  (select ifnull(sum(p.quantity), 0) from unnest(b.products) p)  as so_mon
from `jm-synthetic-data.JM_Synthetic_Data.stg_offline_revenue` s
join `jm-synthetic-data.JM_Synthetic_Data.bills_raw` b
  on b.bill_id = s.bill_id;

-- Đơn online: một dòng mỗi đơn gốc, kèm nhóm trạng thái và thông tin trả hàng sau giao.
CREATE OR REPLACE VIEW `jm-synthetic-data.JM_Synthetic_Data.fct_online_order` AS
with tra as (
  select
    order_id,
    abs(cod_amount)            as tien_hoan_tra,
    cast(created_at as date)   as ngay_tra,
    cast(reason as string)     as ma_ly_do
  from `jm-synthetic-data.JM_Synthetic_Data.orders_raw`
  where order_type = 'Khách trả lại hàng'
)
select
  o.order_id,
  cast(o.created_at as date)                                      as order_date,
  o.customer_id,
  o.sale_channel                                                  as diem_ban,
  o.status,
  case
    when o.status = 'Thành công'                                  then 'Thành công'
    when o.status in ('Đang chuyển hoàn', 'Đã chuyển hoàn',
                      'Xác nhận hoàn')                            then 'Chuyển hoàn'
    when o.status in ('Thất bại', 'Khách hủy', 'Hệ thống hủy',
                      'Hết hàng')                                 then 'Hủy / thất bại'
    else 'Khác'
  end                                                             as nhom_trang_thai,
  o.cod_amount,
  o.ecom_fee,
  o.business_payment,
  t.order_id is not null                                          as bi_tra_sau_giao,
  t.tien_hoan_tra,
  t.ngay_tra,
  case t.ma_ly_do
    when '31' then 'Sai size'
    when '32' then 'Không như mô tả'
    when '33' then 'Lỗi sản phẩm'
    when '34' then 'Giao nhầm'
    when '35' then 'Thất lạc vận chuyển'
  end                                                             as ly_do_tra
from `jm-synthetic-data.JM_Synthetic_Data.orders_raw` o
left join tra t
  on t.order_id = o.order_id
where o.order_type = 'Giao hàng tận nhà';

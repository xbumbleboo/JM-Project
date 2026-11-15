-- =============================================================================
-- 05 · 7 view cho dashboard Power BI (mỗi view khớp grain của một bảng trong mô hình)
-- Cần có: 02_core_views.sql, 03_derived_tables.sql, customer_clv (models/, bước 4 của setup)
-- Tạo ra: pbi_giao_dich, pbi_dong_hang, pbi_don_online, pbi_ngay_mua,
--         pbi_dim_diem_ban, pbi_dim_san_pham, pbi_dim_khach
-- Số kiểm của bộ dữ liệu tham chiếu ghi sau mỗi view; chạy truy vấn ở cuối file để đối chiếu.
-- =============================================================================

-- Giao dịch (cả hai kênh), kèm hạng thẻ lúc mua.
-- Hạng lúc mua suy từ điểm tích trên mỗi 100.000 đ của phiếu bán: 1, 2, 3, 5, 8 điểm ứng với
-- Member, Silver, Gold, Platinum, Diamond. Phiếu dưới 100.000 đ không suy được hạng.
CREATE OR REPLACE VIEW `jm-synthetic-data.JM_Synthetic_Data.pbi_giao_dich` AS
with phieu as (
  select
    cast(bill_id as string)                                       as bill_id,
    cast(depot_id as string)                                      as depot_id,
    bill_type,                                                    -- 2 bán, 1 trả
    payment_points,
    div(cast(floor(payment_amount) as int64), 100000)             as so_khoi_100k,
    payment_used_points_value                                     as gia_tri_diem_dung,
    (select ifnull(sum(p.quantity), 0) from unnest(products) p)   as so_mon
  from `jm-synthetic-data.JM_Synthetic_Data.bills_raw`
),
san as (
  select cast(order_id as string) as order_id, any_value(sale_channel) as sale_channel
  from `jm-synthetic-data.JM_Synthetic_Data.orders_raw`
  where order_type = 'Giao hàng tận nhà'
  group by order_id
)
select
  cast(f.transaction_id as string)                                as transaction_id,
  f.transaction_date                                              as ngay,
  f.channel                                                       as kenh,          -- 'offline' / 'online'
  f.customer_id,
  f.revenue_net,
  f.revenue_gross,
  if(f.channel = 'offline', ph.depot_id, s.sale_channel)          as diem_ban_key,
  coalesce(ph.bill_type = 2, false)                               as la_phieu_ban,
  coalesce(ph.bill_type = 1, false)                               as la_phieu_tra,
  if(ph.bill_type = 2, ph.so_mon, null)                           as so_mon_ban,
  coalesce(ph.gia_tri_diem_dung, 0) > 0                           as dung_diem,
  f.customer_id in (1, 2, 3)                                      as dung_chung,
  case
    when f.channel != 'offline'          then null
    when f.customer_id in (1, 2, 3)      then '0 Không định danh'
    when ph.bill_type != 2               then null                -- phiếu trả
    when ph.so_khoi_100k = 0             then null                -- phiếu dưới 100.000 đ
    when ph.payment_points = 0           then '1 Member'
    else case safe_divide(ph.payment_points, ph.so_khoi_100k)
      when 1 then '1 Member'   when 2 then '2 Silver'  when 3 then '3 Gold'
      when 5 then '4 Platinum' when 8 then '5 Diamond' else 'X Không khớp'
    end
  end                                                             as hang_luc_mua
from `jm-synthetic-data.JM_Synthetic_Data.fct_retail_revenue` f
left join phieu ph on f.channel = 'offline' and ph.bill_id = cast(f.transaction_id as string)
left join san s    on f.channel = 'online'  and s.order_id = cast(f.transaction_id as string);
-- Số kiểm: 826.943 dòng · doanh thu T1–T8/2026 = 203.716.541.898 đ · cả năm 2025 = 347.528.780.193 đ.

-- Dòng hàng. ban_thuong = dòng online, hoặc dòng offline trên phiếu không dùng điểm:
-- phiếu dùng điểm ghi chiết khấu bằng 0, nên biên gộp và tỉ lệ giảm giá chỉ tính trên nhóm này.
CREATE OR REPLACE VIEW `jm-synthetic-data.JM_Synthetic_Data.pbi_dong_hang` AS
with phieu as (
  select bill_id, any_value(payment_used_points_value) as diem
  from `jm-synthetic-data.JM_Synthetic_Data.bills_raw`
  where bill_type = 2
  group by bill_id
),
san as (
  select cast(order_id as string) as order_id, any_value(sale_channel) as sale_channel
  from `jm-synthetic-data.JM_Synthetic_Data.orders_raw`
  where order_type = 'Giao hàng tận nhà'
  group by order_id
)
select
  f.transaction_date                                              as ngay,
  f.channel                                                       as kenh,
  f.code,
  f.quantity                                                      as sl,
  f.revenue_gross_line                                            as gt,
  f.discount_line                                                 as giam,
  f.cost_line                                                     as cost,
  (f.channel = 'online' or coalesce(p.diem, 0) = 0)               as ban_thuong,
  if(f.channel = 'offline', 'Offline', s.sale_channel)            as san
from `jm-synthetic-data.JM_Synthetic_Data.fct_product_revenue` f
left join phieu p on f.channel = 'offline' and f.transaction_id = p.bill_id
left join san s   on f.channel = 'online'  and s.order_id = cast(f.transaction_id as string);
-- Số kiểm: 1.136.072 dòng · doanh số T1–T8/2026 = 215.179.363.973 đ.

-- Đơn online gốc: nhóm trạng thái, trả hàng sau giao, doanh thu còn lại.
-- Ba cách mất đơn (hủy, chuyển hoàn, trả hàng) giữ riêng, mỗi cách một mẫu số.
CREATE OR REPLACE VIEW `jm-synthetic-data.JM_Synthetic_Data.pbi_don_online` AS
with orig as (
  select
    cast(order_id as string) as order_id, sale_channel, status,
    cod_amount, ship_fee, business_payment, cast(created_at as date) as ngay_dat
  from `jm-synthetic-data.JM_Synthetic_Data.orders_raw`
  where order_type = 'Giao hàng tận nhà'
),
ret as (
  select
    cast(order_id as string)              as order_id,
    -sum(cod_amount)                      as refund,
    any_value(safe_cast(reason as int64)) as ma_ly_do
  from `jm-synthetic-data.JM_Synthetic_Data.orders_raw`
  where order_type = 'Khách trả lại hàng'
  group by 1
)
select
  o.order_id,
  o.ngay_dat,
  o.sale_channel                                                  as san,
  case
    when o.status = 'Thành công' then 'Giao thành công'
    when o.status in ('Thất bại', 'Khách hủy', 'Hệ thống hủy', 'Hết hàng') then 'Hủy'
    when o.status in ('Đang chuyển hoàn', 'Đã chuyển hoàn', 'Xác nhận hoàn') then 'Chuyển hoàn'
    else 'Khác'
  end                                                             as nhom,
  o.status = 'Thành công' and r.order_id is not null              as tra_sau_giao,
  o.status = 'Thành công' and r.order_id is not null
    and o.business_payment = 0                                    as tra_toan_phan,
  o.status = 'Thành công' and o.business_payment > 0              as con_doanh_thu,
  if(o.status = 'Thành công', o.business_payment, 0)              as doanh_thu,
  if(o.status = 'Thành công', o.cod_amount, 0)                    as gt_giu_lai,
  case
    when o.status = 'Thành công' and r.order_id is not null and o.cod_amount = 0 then r.refund + o.ship_fee
    when o.status = 'Thành công' and r.order_id is not null                      then r.refund
    else 0
  end                                                             as gt_tra_hang,
  case r.ma_ly_do
    when 31 then 'Sai size'        when 32 then 'Không như mô tả'
    when 33 then 'Lỗi sản phẩm'    when 34 then 'Giao nhầm'
    when 35 then 'Thất lạc vận chuyển'
  end                                                             as ly_do_tra
from orig o
left join ret r using (order_id);
-- Số kiểm: 384.873 dòng.

-- Ngày mua của khách định danh: một dòng mỗi khách mỗi ngày có doanh thu, bỏ phiếu trả.
-- Cũng là đầu vào của mô hình CLV.
CREATE OR REPLACE VIEW `jm-synthetic-data.JM_Synthetic_Data.pbi_ngay_mua` AS
with tra as (
  select cast(bill_id as string) as bill_id
  from `jm-synthetic-data.JM_Synthetic_Data.bills_raw`
  where bill_type = 1
)
select
  f.customer_id,
  f.transaction_date      as ngay,
  sum(f.revenue_net)      as doanh_thu
from `jm-synthetic-data.JM_Synthetic_Data.fct_retail_revenue` f
left join tra t on f.channel = 'offline' and t.bill_id = cast(f.transaction_id as string)
where f.revenue_net > 0
  and t.bill_id is null
  and f.customer_id not in (1, 2, 3)
group by 1, 2;
-- Số kiểm: 706.121 dòng.

-- Điểm bán: cửa hàng có hóa đơn (bỏ kho) và các sàn online.
CREATE OR REPLACE VIEW `jm-synthetic-data.JM_Synthetic_Data.pbi_dim_diem_ban` AS
select
  cast(d.id as string)                                            as diem_ban_key,
  d.name                                                          as ten,
  'offline'                                                       as kenh,
  d.city_name                                                     as tinh,
  case when d.city_name = 'Hà Nội' then 1
       when d.city_name in ('TP. Hồ Chí Minh', 'Hải Phòng', 'Đà Nẵng') then 2
       else 3 end                                                 as jm_operational_tier,
  d.store_format                                                  as mat_bang,
  d.location_type                                                 as vi_tri
from `jm-synthetic-data.JM_Synthetic_Data.depots` d
where cast(d.id as string) in (select distinct cast(depot_id as string) from `jm-synthetic-data.JM_Synthetic_Data.bills_raw`)
union all
select distinct
  sale_channel, sale_channel, 'online', cast(null as string), cast(null as int64),
  cast(null as string), cast(null as string)
from `jm-synthetic-data.JM_Synthetic_Data.orders_raw`;
-- Số kiểm: 36 dòng (29 cửa hàng + 7 kênh online).

-- Sản phẩm: SKU, mã cha, dòng hàng, BST.
CREATE OR REPLACE VIEW `jm-synthetic-data.JM_Synthetic_Data.pbi_dim_san_pham` AS
select
  f.code,
  any_value(f.product_line)                                       as sp_cha,
  any_value(f.category_id)                                        as dong_hang_id,
  case any_value(f.category_id)
    when 101 then 'Áo'       when 102 then 'Đầm'    when 103 then 'Quần'
    when 104 then 'Chân váy' when 105 then 'Set bộ' when 106 then 'Áo khoác'
    when 107 then 'Phụ kiện' end                                  as dong_hang,
  any_value(f.internal_category_id)                               as bst_id,
  any_value(n.name)                                               as ten_bst,
  any_value(split(p.name, ' - ')[safe_offset(0)])                 as ten_sp_cha
from `jm-synthetic-data.JM_Synthetic_Data.fct_product_revenue` f
left join `jm-synthetic-data.JM_Synthetic_Data.nhanh_internal_categories` n on n.id = f.internal_category_id
left join `jm-synthetic-data.JM_Synthetic_Data.nhanh_products_full` p       on p.code = f.code
group by f.code;
-- Số kiểm: 7.213 dòng.

-- Khách: hạng thẻ, phân hạng khách, CLV và decile, ngày mua đầu.
-- Khách chưa từng mua offline có hạng thẻ 'Outside' (chương trình thành viên chỉ áp dụng tại cửa hàng).
CREATE OR REPLACE VIEW `jm-synthetic-data.JM_Synthetic_Data.pbi_dim_khach` AS
with dau as (
  select f.customer_id, min(f.transaction_date) as ngay_mua_dau
  from `jm-synthetic-data.JM_Synthetic_Data.fct_retail_revenue` f
  left join (select cast(bill_id as string) as bill_id
             from `jm-synthetic-data.JM_Synthetic_Data.bills_raw` where bill_type = 1) t
    on f.channel = 'offline' and t.bill_id = cast(f.transaction_id as string)
  where f.revenue_net > 0 and t.bill_id is null and f.customer_id not in (1, 2, 3)
  group by 1
)
select
  c.customer_id,
  if(c.frequency_offline > 0, c.membership_tier, 'Outside')       as hang_the,
  c.Final_Tier                                                    as final_tier,
  v.clv,
  v.clv_decile,
  d.ngay_mua_dau
from `jm-synthetic-data.JM_Synthetic_Data.customer_analytic_base` c
left join `jm-synthetic-data.JM_Synthetic_Data.customer_clv` v using (customer_id)
left join dau d using (customer_id);
-- Số kiểm: 39.531 dòng.

-- -----------------------------------------------------------------------------
-- Đối chiếu nhanh sau khi chạy file này (kết quả phải khớp số kiểm ở trên).
-- -----------------------------------------------------------------------------
select 'pbi_giao_dich' v, count(*) n,
       sum(if(ngay between '2026-01-01' and '2026-08-31', revenue_net, 0)) doanh_thu_t1_t8_2026
from `jm-synthetic-data.JM_Synthetic_Data.pbi_giao_dich`
union all select 'pbi_dong_hang', count(*), sum(if(ngay between '2026-01-01' and '2026-08-31', gt, 0))
from `jm-synthetic-data.JM_Synthetic_Data.pbi_dong_hang`
union all select 'pbi_don_online', count(*), null from `jm-synthetic-data.JM_Synthetic_Data.pbi_don_online`
union all select 'pbi_ngay_mua', count(*), null from `jm-synthetic-data.JM_Synthetic_Data.pbi_ngay_mua`
union all select 'pbi_dim_diem_ban', count(*), null from `jm-synthetic-data.JM_Synthetic_Data.pbi_dim_diem_ban`
union all select 'pbi_dim_san_pham', count(*), null from `jm-synthetic-data.JM_Synthetic_Data.pbi_dim_san_pham`
union all select 'pbi_dim_khach', count(*), null from `jm-synthetic-data.JM_Synthetic_Data.pbi_dim_khach`;

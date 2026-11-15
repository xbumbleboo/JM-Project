-- =============================================================================
-- 01 · Staging: chuẩn hóa từng kênh
-- Cần có: bills_raw, orders_raw, depots
-- Tạo ra: stg_offline_revenue, stg_online_revenue
-- Đổi `jm-synthetic-data.JM_Synthetic_Data` thành project.dataset của bạn (xem setup).
-- =============================================================================

-- Offline: mỗi dòng một phiếu (bán hoặc trả).
-- Doanh thu của phiếu bán = payment_amount; của phiếu trả = phí đổi hàng (payment_return_fee),
-- vì offline luôn là đổi hàng: khi khách đổi sang món rẻ hơn, phần chênh không hoàn lại mà ghi vào cột này.
CREATE OR REPLACE VIEW `jm-synthetic-data.JM_Synthetic_Data.stg_offline_revenue` AS
select
  b.bill_id, b.bill_date, b.customer_id, b.depot_id,
  d.name as store_name, b.bill_type, b.sale_user_id, b.sale_user_name,
  b.payment_amount, b.payment_discount, b.payment_points, b.payment_return_fee,
  case
    when b.bill_type = 2 then b.payment_amount        -- phiếu bán
    when b.bill_type = 1 then b.payment_return_fee    -- phiếu trả
    else 0
  end as revenue_contribution,
  'offline' as channel
from `jm-synthetic-data.JM_Synthetic_Data.bills_raw` b
left join `jm-synthetic-data.JM_Synthetic_Data.depots` d
  on b.depot_id = d.id;

-- Online: chỉ đơn giao thành công, bỏ dòng "Khách trả lại hàng".
-- Dòng trả dùng lại order_id của đơn gốc; khi khách trả, generator đã trừ tiền ngay trên đơn gốc,
-- nên business_payment của đơn gốc là doanh thu còn lại.
CREATE OR REPLACE VIEW `jm-synthetic-data.JM_Synthetic_Data.stg_online_revenue` AS
select
  o.order_id, o.created_at, o.customer_id, o.sale_channel, o.order_type,
  o.status, o.cod_amount, o.business_payment, o.ecom_fee, o.ship_fee,
  'online' as channel
from `jm-synthetic-data.JM_Synthetic_Data.orders_raw` o
where status = 'Thành công' and order_type != 'Khách trả lại hàng';

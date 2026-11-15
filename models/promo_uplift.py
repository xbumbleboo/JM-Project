"""
Hiệu quả khuyến mãi: hồi quy quasi-Poisson theo ngày.

    log E[y_ngày] = năm + tháng + cuối tuần + chương trình
    y = số hóa đơn bán offline · doanh thu phiếu bán (triệu đồng) · số đơn online đặt

- Sai số hiệu chỉnh phân tán: scale = Pearson χ² / bậc tự do (quasi-Poisson).
- Uplift = e^β − 1, so với ngày nền (không có chương trình).
- Khoảng tin cậy 95% in ra là nửa độ rộng ±1,96 × SE × e^β (xấp xỉ delta, khớp báo cáo insight).
  Khoảng chính xác trên thang log: [e^(β − 1,96·SE) − 1 ; e^(β + 1,96·SE) − 1]; với bộ tham chiếu
  hai cách lệch tối đa 0,6 điểm phần trăm.
- Ngày trùng nhiều chương trình gán cho chương trình có hệ số tác động lớn nhất.
- "Ra mắt BST mới" phủ kín T10–T12 nên gộp vào nền; Black Friday vì vậy đo so với nền đó.
- Thay đổi AOV = (1 + uplift doanh thu) ÷ (1 + uplift hóa đơn) − 1 = e^(β_doanh thu − β_hóa đơn) − 1.
Uplift là so với ngày nền, không phải doanh thu tăng thêm: khách có thể chỉ dời ngày mua.

Chạy:
    export JM_PROJECT=your-project JM_DATASET=your_dataset   # mặc định: bộ gốc
    python models/promo_uplift.py          # in bảng, ghi promo_uplift.csv
Kết quả với bộ dữ liệu tham chiếu: báo cáo insight mục 4 (Hot Sale 8/3 +44,2% ±3,5 hóa đơn, …;
hệ số phân tán 1,48 hóa đơn, 2,77 doanh thu).
"""
import os

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

PROJECT = os.environ.get("JM_PROJECT", "jm-synthetic-data")
DATASET = os.environ.get("JM_DATASET", "JM_Synthetic_Data")

# (tên, tháng/ngày bắt đầu, tháng/ngày kết thúc, thứ tự ưu tiên khi trùng ngày, mức giảm thêm)
# Cột thứ tư chỉ dùng để quyết định ngày trùng nhiều chương trình thuộc chương trình nào.
PROM = [
    ("Xả kho & Chào Xuân", 1, 1, 1, 25, 1.30, .15),
    ("Hot Sale 8/3", 3, 1, 3, 8, 1.45, .20),
    ("30/4 - 1/5", 4, 27, 5, 3, 1.25, .10),
    ("Sinh nhật JM", 6, 20, 7, 15, 1.25, .15),
    ("Sale giữa tháng 15/7", 7, 13, 7, 17, 1.20, .10),
    ("End of Season", 7, 20, 8, 20, 1.15, .15),
    ("Black Friday", 10, 30, 11, 13, 1.45, .30),
    ("Ra mắt BST mới", 10, 1, 12, 31, 1.10, .05),
]

QUERY = f"""
with off as (
  select bill_date as ngay,
         countif(bill_type = 2) as n_phieu_ban,
         sum(if(bill_type = 2, payment_amount, 0)) as dt_phieu_ban
  from `{PROJECT}.{DATASET}.bills_raw` group by 1),
onl as (
  select cast(created_at as date) as ngay, count(distinct order_id) as n_don_online
  from `{PROJECT}.{DATASET}.orders_raw`
  where order_type = 'Giao hàng tận nhà' group by 1)
select o.ngay, o.n_phieu_ban, o.dt_phieu_ban, ifnull(n.n_don_online, 0) as n_don_online
from off o left join onl n using (ngay)
where o.ngay <= '2026-08-31'
order by o.ngay
"""


def in_window(d, m1, d1, m2, d2):
    if m1 == m2:
        return d.month == m1 and d1 <= d.day <= d2
    if d.month == m1:
        return d.day >= d1
    if d.month == m2:
        return d.day <= d2
    return m1 < d.month < m2


def program_of(d):
    best = ("Không", 1.0)
    for name, m1, d1, m2, d2, traf, _ in PROM:
        if in_window(d, m1, d1, m2, d2) and traf > best[1]:
            best = (name, traf)
    return "Không" if best[0] == "Ra mắt BST mới" else best[0]


def main():
    from google.cloud import bigquery
    d = bigquery.Client(project=PROJECT).query(QUERY).to_dataframe()
    d["ngay"] = pd.to_datetime(d["ngay"])
    print(f"{len(d)} ngày (bộ tham chiếu: 974)")

    d["ct"] = d.ngay.apply(program_of)
    d["nam"] = d.ngay.dt.year
    d["thang"] = d.ngay.dt.month
    d["cuoi_tuan"] = (d.ngay.dt.weekday >= 5).astype(int)
    d["dt_tr"] = d.dt_phieu_ban.astype(float) / 1e6
    rhs = "C(nam) + C(thang) + cuoi_tuan + C(ct, Treatment('Không'))"
    fit = {y: smf.glm(f"{y} ~ {rhs}", d, family=sm.families.Poisson()).fit(scale="X2")
           for y in ["n_phieu_ban", "dt_tr", "n_don_online"]}

    rows = []
    for name, *_ in PROM:
        if name == "Ra mắt BST mới":
            continue
        k = f"C(ct, Treatment('Không'))[T.{name}]"
        b, se = fit["n_phieu_ban"].params[k], fit["n_phieu_ban"].bse[k]
        r, rse = fit["dt_tr"].params[k], fit["dt_tr"].bse[k]
        o = fit["n_don_online"].params[k]
        rows.append({
            "chuong_trinh": name, "so_ngay": int((d.ct == name).sum()),
            "uplift_hoa_don_pct": 100 * (np.exp(b) - 1), "ci95_hoa_don": 100 * 1.96 * se * np.exp(b),
            "uplift_doanh_thu_pct": 100 * (np.exp(r) - 1), "ci95_doanh_thu": 100 * 1.96 * rse * np.exp(r),
            "thay_doi_aov_pct": 100 * (np.exp(r - b) - 1),
            "uplift_don_online_pct": 100 * (np.exp(o) - 1),
        })
    out = pd.DataFrame(rows).round(1)
    print(out.to_string(index=False))
    for y, m in fit.items():
        print(f"{y}: hệ số phân tán {m.scale:.2f} · cuối tuần +{100 * (np.exp(m.params['cuoi_tuan']) - 1):.1f}%")
    out.to_csv("promo_uplift.csv", index=False)


if __name__ == "__main__":
    main()

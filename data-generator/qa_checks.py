"""
================================================================================
JM SYNTHETIC DATA — QA CHECK v3
================================================================================
Kiểm tra bộ dữ liệu ĐÃ SINH (đọc từ thư mục output), không sinh lại dữ liệu.

CÁCH DÙNG:
    1. Chạy generator trước:   python3 jm_synthetic_generator_v3.py
    2. Rồi chạy QA:            python3 jm_qa_check_v3.py [đường_dẫn_thư_mục]
       (mặc định: jm_synthetic_data_v2 — đúng CONFIG["output_dir"])

    Trên Colab:
       !python3 jm_synthetic_generator_v3.py
       !python3 jm_qa_check_v3.py

ĐỌC KẾT QUẢ:
    [PASS]  đạt
    [FAIL]  SAI — phải sửa generator, không được vá bằng SQL
    [WARN]  lệch nhẹ / cần mắt người xem, không chặn
    [INFO]  số liệu tham khảo để hiệu chỉnh tham số (không tính PASS/FAIL)

Cuối script có PHẦN HIỆU CHỈNH TỒN KHO — đây là phần cần đọc kỹ nhất ở lần chạy
full-scale đầu tiên, vì lot_size/replen_days chưa được calibrate ở quy mô thật.
"""
import json
import os
import sys
from datetime import date

import numpy as np
import pandas as pd

OUT = sys.argv[1] if len(sys.argv) > 1 else "jm_synthetic_data_v2"

PASS, FAIL, WARN = [], [], []


def _p(tag, name, detail=""):
    print(f"  [{tag}] {name}" + (f"  — {detail}" if detail else ""))


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    _p("PASS" if cond else "FAIL", name, detail)


def warn(name, cond, detail=""):
    if cond:
        PASS.append(name)
        _p("PASS", name, detail)
    else:
        WARN.append(name)
        _p("WARN", name, detail)


def info(name, detail):
    _p("INFO", name, detail)


def section(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def load_ndjson(path, cols=None):
    recs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            recs.append({k: r.get(k) for k in cols} if cols else r)
    return pd.DataFrame(recs)


def main():
    if not os.path.isdir(OUT):
        print(f"KHÔNG TÌM THẤY thư mục '{OUT}'.")
        print("Chạy generator trước, hoặc truyền đường dẫn: python3 jm_qa_check_v3.py <thư_mục>")
        sys.exit(2)

    P = lambda *a: os.path.join(OUT, *a)

    # ------------------------------------------------------------------
    section("0. TẢI DỮ LIỆU")
    depots = pd.read_csv(P("shop_data", "depots.csv"))
    emp = pd.read_csv(P("retail_data", "employees.csv"))
    cust = pd.read_csv(P("customer_data", "nhanh_customers_full.csv"))
    tier = pd.read_csv(P("customer_data", "t_customer_tier_final.csv"))
    snap = pd.read_csv(P("inventory_data", "daily_snapshot.csv"))
    prod = load_ndjson(P("product_data", "nhanh_products_full.ndjson"),
                       ["id", "parentId", "code", "name", "status"])
    bills = load_ndjson(P("retail_data", "bills_raw.ndjson"))
    orders = load_ndjson(P("order_data", "orders_raw.ndjson"))
    xnk = load_ndjson(P("bill_data", "nhanh_bills_full.ndjson"),
                      ["id", "orderId", "depotId", "date", "type", "mode",
                       "description", "products", "paymentAmount"])
    for n, d in [("depots", depots), ("products", prod), ("bills_raw", bills),
                 ("orders_raw", orders), ("nhanh_bills_full", xnk),
                 ("customers", cust), ("daily_snapshot", snap)]:
        print(f"  {n:<20} {len(d):>10,} dòng")

    # ------------------------------------------------------------------
    section("1. SCHEMA — số cột phải khớp tuyệt đối")
    EXPECT = {"depots": 14, "bills_raw": 34, "orders_raw": 41,
              "nhanh_bills_full": 26, "nhanh_customers_full": 19,
              "t_customer_tier_final": 8, "daily_snapshot": 11,
              "employees": 7}
    xnk_full = load_ndjson(P("bill_data", "nhanh_bills_full.ndjson"))
    prod_full = load_ndjson(P("product_data", "nhanh_products_full.ndjson"))
    actual = {"depots": depots.shape[1], "bills_raw": bills.shape[1],
              "orders_raw": orders.shape[1], "nhanh_bills_full": xnk_full.shape[1],
              "nhanh_customers_full": cust.shape[1],
              "t_customer_tier_final": tier.shape[1],
              "daily_snapshot": snap.shape[1], "employees": emp.shape[1]}
    for k, v in EXPECT.items():
        check(f"schema {k}: {v} cột", actual[k] == v, f"thực tế {actual[k]}")
    check("orders_raw KHÔNG còn cột order_mode (M1)",
          "order_mode" not in orders.columns)
    check("products_full: 29 cột", prod_full.shape[1] == 29,
          f"thực tế {prod_full.shape[1]}")

    # ------------------------------------------------------------------
    section("2. TOÀN VẸN THAM CHIẾU & KHÓA")
    check("mã SKU DUY NHẤT (lỗi mã màu XA đã sửa)", prod["code"].is_unique,
          f"{len(prod):,} SP / {prod['code'].nunique():,} mã distinct")
    check("depot_id trong bills_raw join được về depots",
          set(bills["depot_id"]) <= set(depots["id"]))
    check("depot_id trong orders_raw join được về depots",
          set(orders["depot_id"]) <= set(depots["id"]))
    check("warehouse_code trong daily_snapshot join được về depots",
          set(snap["warehouse_code"]) <= set(depots["code"]),
          f"mã lạ: {set(snap['warehouse_code']) - set(depots['code']) or 'không có'}")
    check("depotId trong nhanh_bills_full join được về depots",
          set(xnk["depotId"].dropna()) <= set(depots["id"]))

    sku = set(prod["code"])
    bad_b = sum(1 for it in bills["products"] if isinstance(it, list)
                for i in it if i["code"] not in sku)
    bad_o = sum(1 for it in orders["products"] if isinstance(it, list)
                for i in it if i["code"] not in sku)
    check("mọi dòng SP trong bills_raw resolve về products", bad_b == 0, f"{bad_b} dòng lỗi")
    check("mọi dòng SP trong orders_raw resolve về products", bad_o == 0, f"{bad_o} dòng lỗi")

    # ------------------------------------------------------------------
    section("3. M1-M6 — 6 MANDATORY RULES")
    PH = {1, 2, 3}
    check("M3: KHÔNG có đơn online nào của khách placeholder",
          not (set(orders["customer_id"]) & PH),
          f"{orders['customer_id'].isin(PH).sum()} đơn")
    ph_off = bills["customer_id"].isin(PH).mean()
    warn("M3: offline VẪN có placeholder (đúng nghiệp vụ, ~8%)",
         0.03 <= ph_off <= 0.15, f"{ph_off:.1%} hóa đơn")

    # pandas có thể suy ra dtype "str" (Arrow) thay vì object -> không so dtype,
    # chỉ kiểm chính giá trị có phải chuỗi không-phải-số hay không.
    check("M6: status là NHÃN CHỮ, không phải số",
          orders["status"].map(lambda v: isinstance(v, str) and not v.isdigit()).all(),
          f"ví dụ: {orders['status'].iloc[0]!r}")
    check("M6: order_type là nhãn chữ",
          orders["order_type"].map(lambda v: isinstance(v, str) and not v.isdigit()).all(),
          f"ví dụ: {orders['order_type'].iloc[0]!r}")
    check("M6: sale_channel là nhãn chữ",
          orders["sale_channel"].map(lambda v: isinstance(v, str) and not v.isdigit()).all(),
          f"ví dụ: {orders['sale_channel'].iloc[0]!r}")

    ret = orders[orders["order_type"] == "Khách trả lại hàng"]
    sale = orders[orders["order_type"] != "Khách trả lại hàng"]
    ok_ids = set(sale[sale["status"] == "Thành công"]["order_id"])
    traced = ret["order_id"].isin(ok_ids).sum()
    check("M4: mọi dòng hoàn trace được về đơn gốc Thành công",
          len(ret) == 0 or traced == len(ret), f"{traced}/{len(ret)} trace được")
    check("M4: dòng hoàn mang cod_amount ÂM (khấu trừ thật)",
          len(ret) == 0 or (ret["cod_amount"] <= 0).all(),
          f"tổng hoàn = {ret['cod_amount'].sum():,.0f}đ")

    parent = prod[prod["parentId"].isna()]
    child = prod[prod["parentId"].notna()]
    check("M2: mọi SP con có parentId map được về SP cha",
          set(child["parentId"]) <= set(parent["id"]),
          f"{len(parent):,} cha / {len(child):,} con")

    # ------------------------------------------------------------------
    section("4. HẠNG THẺ & ĐIỂM (M5 — chỉ offline)")
    real = cust[~cust["id"].isin(PH)]
    dist = real["membership_tier"].value_counts(normalize=True)
    order_t = ["Member", "Silver", "Gold", "Platinum", "Diamond"]
    pcts = [dist.get(t, 0) for t in order_t]
    for t, p in zip(order_t, pcts):
        n = int((real["membership_tier"] == t).sum())
        _p("INFO", f"  {t:<10}", f"{n:>8,}  ({p:6.2%})")
    check("phân bố hạng là hình chóp giảm dần đơn điệu",
          all(a >= b for a, b in zip(pcts, pcts[1:])))
    check("có mặt đủ 5 hạng (Diamond không trống)", all(p > 0 for p in pcts))

    # [FIX v3.1] Bản cũ đọc `frequencyBought` — cột mà fix #1 vừa chuyển thành
    # XUYÊN KÊNH — rồi đem so với dải 60-90 vốn suy ra trên cơ sở OFFLINE.
    # Nguồn của dải này: JM_Generation_Rules_v2 mục 5.3, câu cuối ghi rõ
    # "hiệu chỉnh trên cơ sở doanh thu offline riêng". Đây là CHỐT CHẶN HỒI QUY
    # kế thừa từ v2.1, KHÔNG phải sự thật nghiệp vụ — Business Domain v2 không
    # có dòng nào về tần suất mua, và chuỗi "GR-CUST" không tồn tại trong
    # Generation Rules v2. Vì vậy bỏ mã quy tắc khỏi tên test.
    # Kéo xuyên kênh về 60-90 sẽ đẩy offline ra ~120 ngày — hai mục tiêu triệt
    # tiêu nhau. Gate theo offline, xuyên kênh chỉ để quan sát.
    span = (pd.to_datetime(bills["bill_date"]).max()
            - pd.to_datetime(bills["bill_date"]).min()).days + 1
    yrs = span / 365.25

    n_off = int((~bills["customer_id"].isin(PH)
                 & (bills["bill_type"] == "2")).sum())
    gap_off = 365.25 / (n_off / len(real) / yrs)
    warn("khoảng cách 2 lần mua OFFLINE 60-90 ngày "
         "(chốt chặn hồi quy v2.1 — không phải quy tắc nghiệp vụ)",
         60 <= gap_off <= 90, f"~{gap_off:.0f} ngày")

    gap_all = 365.25 / (real["frequencyBought"].sum() / len(real) / yrs)
    info("  khoảng cách 2 lần mua XUYÊN KÊNH (quan sát, không gate)",
         f"~{gap_all:.0f} ngày")

    b2 = bills[bills["bill_type"] == "2"]
    redeem = b2[b2["payment_used_points_value"] > 0]
    bad_r = sum(1 for it in redeem["products"] if isinstance(it, list)
                for i in it if i["discount"] > 0)
    check("GR-CUST.8: hóa đơn tiêu điểm không chứa dòng SP có discount",
          bad_r == 0, f"{bad_r} dòng vi phạm / {len(redeem):,} hóa đơn tiêu điểm")

    # ------------------------------------------------------------------
    section("5. TÍNH TOÁN TIỀN — bất biến bắt buộc")
    def line_total(it):
        return sum(i["amount"] for i in it) if isinstance(it, list) else 0
    b2 = b2.copy()
    b2["calc"] = b2["products"].apply(line_total)
    mism = (b2["payment_amount"] != b2["calc"]).sum()
    check("payment_amount == tổng amount dòng SP", mism == 0, f"{mism:,} dòng lệch")

    pay_sum = (b2["payment_cash_amount"] + b2["payment_transfer_amount"]
               + b2["payment_credit_amount"])
    check("GR-OFF.4: tổng 3 phương thức == payment_customer_amount",
          (pay_sum == b2["payment_customer_amount"]).all(),
          f"{(pay_sum != b2['payment_customer_amount']).sum():,} dòng lệch")

    bad_conv = sum(1 for it in b2["products"] if isinstance(it, list)
                   for i in it
                   if i["discount"] != i["totalDiscount"]
                   or i["amount"] != i["price"] * i["quantity"] - i["discount"])
    check("quy ước dòng SP: discount == totalDiscount == giảm CẢ DÒNG",
          bad_conv == 0, f"{bad_conv:,} dòng lệch")
    check("không có payment_amount âm", (bills["payment_amount"] >= 0).all())

    # ------------------------------------------------------------------
    section("6. TỒN KHO — RECONCILIATION (GR-INV.9)")
    check("không âm: quantity >= 0 ở mọi snapshot",
          (snap["quantity"] >= 0).all(), f"{(snap['quantity'] < 0).sum()} dòng âm")

    per_date = snap.groupby("snapshot_date")["product_id"].apply(set)
    check("panel CỐ ĐỊNH: cùng tập SKU ở mọi kỳ",
          all(s == per_date.iloc[0] for s in per_date),
          f"{len(per_date)} kỳ, {len(per_date.iloc[0])} SKU/kỳ")
    n_ser = snap.groupby(["warehouse_code", "product_id"]).size()
    check("mọi chuỗi (kho, SKU) đủ số kỳ", n_ser.nunique() == 1,
          f"số kỳ/chuỗi = {sorted(int(x) for x in n_ser.unique())}")

    piv = snap.pivot_table(index=["warehouse_code", "product_id"],
                           columns="snapshot_date", values="quantity")
    cols = list(piv.columns)
    mid = len(cols) // 2
    corr = piv[cols[mid]].corr(piv[cols[mid + 1]])
    check("tồn có quán tính giữa 2 kỳ (không phải random như bản cũ)",
          corr > 0.5, f"tương quan = {corr:.3f}  (bản cũ ~0)")

    tr = xnk[xnk["mode"] == 3]
    imp = xnk[xnk["mode"] == 5]
    check("phiếu chuyển kho CÓ dòng sản phẩm (bản cũ products=None)",
          len(tr) > 0 and tr["products"].notna().all(), f"{len(tr):,} phiếu")
    check("phiếu nhập NCC có dòng sản phẩm",
          len(imp) > 0 and imp["products"].notna().all(), f"{len(imp):,} phiếu")
    q_in = sum(i["quantity"] for ps in tr[tr["type"] == 1]["products"] for i in ps)
    q_out = sum(i["quantity"] for ps in tr[tr["type"] == 2]["products"] for i in ps)
    check("chuyển kho cân đối: SL xuất kho tổng == SL nhập cửa hàng",
          q_in == q_out, f"xuất {q_out:,} / nhập {q_in:,} đv")

    wh_ids = set(depots[depots["store_format"] == "Kho"]["id"])
    check("phiếu XUẤT chuyển kho luôn xuất phát từ kho",
          set(tr[tr["type"] == 2]["depotId"]) <= wh_ids)
    loi_id = depots[depots["code"] == "WH_LOI"]["id"]
    check("kho hàng lỗi WH_LOI tồn tại trong depots", len(loi_id) == 1)
    loi = snap[snap["warehouse_code"] == "WH_LOI"]
    if len(loi):
        ser = loi.groupby("snapshot_date")["quantity"].sum().sort_index()
        check("kho lỗi CHỈ TĂNG (hàng hỏng không bán ra)",
              all(b >= a for a, b in zip(ser.values, ser.values[1:])),
              f"{ser.iloc[0]:,} -> {ser.iloc[-1]:,} đv")

    # ------------------------------------------------------------------
    section("7. PHÍ SÀN THEO TIMELINE")
    o = orders[orders["order_type"] != "Khách trả lại hàng"].copy()
    o["y"] = o["created_at"].str[:4]
    self_ch = o[o["sale_channel"].isin(["Facebook", "Instagram", "Website", "Admin"])]
    check("kênh tự vận hành có ecom_fee = 0",
          (self_ch["ecom_fee"] == 0).all(), f"{len(self_ch):,} đơn")
    mkt = o[o["sale_channel"].isin(["Shopee", "Lazada", "TikTok Shop"])]
    check("sàn TMĐT luôn có ecom_fee > 0",
          (mkt["ecom_fee"] > 0).all(), f"{len(mkt):,} đơn")

    ok = o[o["status"] == "Thành công"]
    r = ok.groupby("sale_channel").apply(
        lambda x: (x["ecom_fee"].sum() / max(1, x["cod_amount"].sum())),
        include_groups=False)
    for ch, v in r.items():
        info(f"  tỉ lệ phí/doanh thu — {ch:<12}", f"{v:.2%}")

    sp = mkt[mkt["sale_channel"] == "Shopee"].copy()
    sp["d"] = pd.to_datetime(sp["created_at"]).dt.date
    before = sp[sp["d"] < date(2026, 5, 1)]
    after = sp[sp["d"] >= date(2026, 5, 1)]
    if len(before) and len(after):
        rb = (before["ecom_fee"] / before["products"].apply(line_total).clip(lower=1)).median()
        ra = (after["ecom_fee"] / after["products"].apply(line_total).clip(lower=1)).median()
        check("Shopee: mức phí TĂNG sau mốc 01/05/2026", ra > rb,
              f"trước {rb:.2%} -> sau {ra:.2%}")

    failed = o[o["status"] != "Thành công"]
    check("đơn hoàn/hủy VẪN chịu phí không hoàn (doanh thu 0, chi phí > 0)",
          len(failed) == 0 or failed[failed["sale_channel"].isin(
              ["Shopee", "Lazada", "TikTok Shop"])]["ecom_fee"].sum() > 0)

    # [FIX v3.1] Bản cũ gộp "status != Thành công" thành MỘT chỉ số rồi gọi là
    # "tỉ lệ hoàn/hủy" -> ra 22-38%, không so được với số đã khóa (TikTok 24,3%
    # / Shopee 11,6%) vốn chỉ nói về HOÀN. Hủy trước giao và hoàn sau giao là
    # hai cơ chế khác nhau về bản chất chi phí lẫn nghiệp vụ — không bao giờ
    # được cộng chung. Tách làm 2.
    RET_ST = {"Đang chuyển hoàn", "Đã chuyển hoàn", "Xác nhận hoàn"}
    CAN_ST = {"Khách hủy", "Hệ thống hủy", "Hết hàng", "Thất bại"}

    ret = o.groupby("sale_channel").apply(
        lambda x: x["status"].isin(RET_ST).mean(), include_groups=False)
    can = o.groupby("sale_channel").apply(
        lambda x: x["status"].isin(CAN_ST).mean(), include_groups=False)

    for ch in ret.sort_values(ascending=False).index:
        info(f"  hoàn / hủy — {ch:<12}",
             f"hoàn {ret[ch]:.1%}  |  hủy {can[ch]:.1%}")

    tt = ret.get("TikTok Shop", 0)
    check("TikTok Shop có tỉ lệ HOÀN cao nhất (số QA đã khóa ~24,3%)",
          tt == ret.max(), f"TikTok {tt:.1%} | " +
          " | ".join(f"{k} {v:.1%}" for k, v in ret.sort_values(ascending=False).items()))
    sp_r = ret.get("Shopee", 0)
    warn("Shopee tỉ lệ HOÀN bám số đã khóa ~11,6% (±3đ)",
         abs(sp_r - 0.116) <= 0.03, f"{sp_r:.1%}")

    # ------------------------------------------------------------------
    section("8. BLACK FRIDAY — luật mua >= 4 giảm 15%")
    def in_bf(x):
        d = date.fromisoformat(x)
        return (d.month == 10 and d.day >= 30) or (d.month == 11 and d.day <= 13)
    bb = b2.copy()
    bb["bf"] = bb["bill_date"].apply(in_bf)
    bb["n"] = bb["products"].apply(
        lambda it: sum(i["quantity"] for i in it) if isinstance(it, list) else 0)
    big = bb[bb["bf"] & (bb["n"] >= 4) & (bb["payment_used_points_value"] == 0)]
    viol = sum(1 for it in big["products"] for i in it
               if i["price"] * i["quantity"] > 0
               and i["discount"] / (i["price"] * i["quantity"]) < 0.15 - 1e-9)
    check("BF: hóa đơn >= 4 món được giảm tối thiểu 15% mọi dòng",
          viol == 0 and len(big) > 0, f"{len(big):,} hóa đơn đạt ngưỡng, {viol} dòng vi phạm")
    check("BF kéo UPT lên so với ngày thường",
          bb[bb["bf"]]["n"].mean() > bb[~bb["bf"]]["n"].mean(),
          f"BF {bb[bb['bf']]['n'].mean():.2f} vs thường {bb[~bb['bf']]['n'].mean():.2f}")

    # ------------------------------------------------------------------
    section("9. QUY MÔ & MỤC TIÊU NĂM")
    bb["y"] = bb["bill_date"].str[:4]
    off = bb["y"].value_counts().sort_index()
    onl = o["y"].value_counts().sort_index()
    TARGET = {"2024": 400_000, "2025": 325_000, "2026": 180_000}
    for y in sorted(set(off.index) | set(onl.index)):
        tot = int(off.get(y, 0)) + int(onl.get(y, 0))
        t = TARGET.get(y)
        d = f"{tot:,} (offline {int(off.get(y,0)):,} + online {int(onl.get(y,0)):,})"
        if t and tot >= 0.5 * t:
            warn(f"tổng giao dịch năm {y} sát mục tiêu {t:,} (±12%)",
                 abs(tot - t) / t <= 0.12, d + f"  lệch {100*(tot-t)/t:+.1f}%")
        elif t:
            info(f"tổng giao dịch năm {y}",
                 d + "  (chạy thu nhỏ — bỏ qua so mục tiêu full-scale)")
        else:
            info(f"tổng giao dịch năm {y}", d)

    share = onl.sum() / (onl.sum() + off.sum())
    warn("tỉ trọng online 35-55%", 0.35 <= share <= 0.55, f"{share:.1%}")

    # ------------------------------------------------------------------
    section("10. HIỆU CHỈNH TỒN KHO — ĐỌC KỸ PHẦN NÀY")
    print("  lot_size và replen_days CHƯA được calibrate ở quy mô thật.")
    print("  Dùng các số dưới đây để quyết định có cần chỉnh không.\n")

    last = snap[snap["snapshot_date"] == snap["snapshot_date"].max()]
    zero = (last["quantity"] == 0).mean()
    info("  % (kho, SKU) hết hàng cuối kỳ", f"{zero:.1%}")
    info("  tồn trung bình mỗi (kho, SKU)", f"{snap['quantity'].mean():.1f} đv")
    info("  tồn trung vị", f"{snap['quantity'].median():.0f} đv")

    # [FIX v3.1] Bản cũ đo sai 3 chỗ, nên con số ra không dùng để quyết định
    # tham số được:
    #   1. LỆCH TẬP KHO — tử số cộng doanh số SKU panel trên TOÀN BỘ cửa hàng,
    #      mẫu số chỉ là tồn của các cặp (kho, SKU) TRONG panel. Mỗi cửa hàng
    #      chỉ giữ 35% của 400 SKU, nên một SKU nằm trong panel của ~10 cửa
    #      hàng nhưng bán ở 29 -> tử số thổi phồng ~2,9x.
    #   2. BỎ SÓT ONLINE — tử số chỉ đọc bills_raw, trong khi sổ cái tồn kho
    #      của generator trừ cả orders_raw (~42,5% nhu cầu).
    #   3. KHÔNG QUY NĂM — 140 kỳ ≈ 2,7 năm, nhưng ngưỡng 1,5-12 là chuẩn vòng
    #      quay NĂM của ngành thời trang.
    # sell-through cũ còn vô nghĩa hơn: tử số 400 SKU panel, mẫu số q_in là
    # tổng nhập của cả 7.213 SKU.
    depot_wh = dict(zip(depots["id"].astype(str), depots["code"]))
    pairs = set(zip(snap["warehouse_code"], snap["product_id"]))

    NEVER_LEFT = {"Khách hủy", "Hệ thống hủy", "Hết hàng"}
    tot_sold = 0
    for dep, bt, it in zip(bills["depot_id"], bills["bill_type"], bills["products"]):
        if bt != "2" or not isinstance(it, list):
            continue
        wh = depot_wh.get(str(dep))
        for i in it:
            if (wh, i["code"]) in pairs:
                tot_sold += i["quantity"]
    for dep, ot, st_, it in zip(orders["depot_id"], orders["order_type"],
                                orders["status"], orders["products"]):
        if ot == "Khách trả lại hàng" or st_ in NEVER_LEFT or not isinstance(it, list):
            continue
        wh = depot_wh.get(str(dep))
        for i in it:
            if (wh, i["code"]) in pairs:
                tot_sold += i["quantity"]

    sd = pd.to_datetime(snap["snapshot_date"])
    years = max(0.01, (sd.max() - sd.min()).days / 365.25)
    avg_stock = snap.groupby("snapshot_date")["quantity"].sum().mean()
    turns = tot_sold / max(1, avg_stock) / years
    info("  nhu cầu xuất trong panel (cả 2 kênh)", f"{tot_sold:,} đv")
    info("  vòng quay tồn kho QUY NĂM", f"{turns:.2f} vòng/năm  ({years:.2f} năm dữ liệu)")

    # bằng chứng tích lũy: tồn tổng panel đầu kỳ vs cuối kỳ
    by_d = snap.groupby("snapshot_date")["quantity"].sum().sort_index()
    n_pair = snap.groupby("snapshot_date").size().iloc[0]
    close_per_pair = by_d.iloc[-1] / max(1, n_pair)
    info("  tổng tồn panel đầu kỳ -> cuối kỳ",
         f"{int(by_d.iloc[0]):,} -> {int(by_d.iloc[-1]):,} đv "
         f"({by_d.iloc[-1] / max(1, by_d.iloc[0]):.1f}x)")
    info("  tồn CUỐI KỲ mỗi cặp (kho, SKU)", f"{close_per_pair:.2f} đv")

    print()
    # [FIX v3.1] Ngưỡng cũ dùng TỈ LỆ đầu/cuối kỳ (1,5x) — bắt nhầm ở hai chỗ:
    #   (a) kỳ snapshot đầu tiên chưa vào trạng thái ổn định, mẫu số quá nhỏ
    #       nên tỉ lệ nào cũng vọt;
    #   (b) giao dịch giảm dần theo năm (400k -> 180k) nên càng về sau càng
    #       nhiều cặp ngừng bán hẳn và giữ phần dư làm tròn lô vĩnh viễn — đây
    #       là hàng cuối vòng đời, ĐÚNG nghiệp vụ.
    # Mô phỏng nhu cầu ròng trong jm_inv_diagnostic.py tái tạo đúng hiện tượng
    # này dù không hề có logic nhu cầu gộp -> xác nhận không phải lỗi tích lũy.
    # Nay gate theo MỨC TUYỆT ĐỐI: tồn cuối kỳ vượt 3 đv/cặp mới đáng ngờ.
    if close_per_pair > 3.0:
        _p("WARN", "tồn cuối kỳ dày bất thường",
           f"{close_per_pair:.1f} đv/cặp — kiểm tra logic nhu cầu ròng "
           "trong gen_inventory()")
        WARN.append("tồn kho tích lũy")
    else:
        _p("PASS", "tồn cuối kỳ ở mức mỏng, không tích lũy bất thường",
           f"{close_per_pair:.2f} đv/cặp")
        PASS.append("tồn cuối kỳ không tích lũy")

    if turns < 1.5:
        _p("WARN", "vòng quay THẤP — tồn quá dày",
           "chạy jm_inv_diagnostic.py để lấy bảng lưới lot_size/replen_days "
           "trước khi chỉnh — KHÔNG chỉnh mò")
        WARN.append("vòng quay tồn kho thấp")
    elif turns > 12:
        _p("WARN", "vòng quay QUÁ CAO — tồn quá mỏng",
           "TĂNG lot_size hoặc TĂNG replen_days")
        WARN.append("vòng quay tồn kho quá cao")
    else:
        _p("PASS", "vòng quay tồn kho trong dải hợp lý cho thời trang (1,5-12)",
           f"{turns:.2f} vòng")
        PASS.append("vòng quay tồn kho hợp lý")

    # ------------------------------------------------------------------
    section("TỔNG KẾT")
    print(f"  PASS : {len(PASS)}")
    print(f"  WARN : {len(WARN)}")
    print(f"  FAIL : {len(FAIL)}")
    if FAIL:
        print("\n  Các test FAIL — phải sửa GENERATOR, không vá bằng SQL:")
        for f in FAIL:
            print("    ✗ " + f)
    if WARN:
        print("\n  Các test WARN — xem xét, không chặn:")
        for w in WARN:
            print("    ! " + w)
    if not FAIL:
        print("\n  ✓ Không có FAIL. Bộ dữ liệu sẵn sàng upload BigQuery.")
        print("    LƯU Ý: M6 đã gán nhãn chữ ngay từ generator -> KHÔNG cần")
        print("    chạy lại SQL mapping STRING sau mỗi lần reload nữa.")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()

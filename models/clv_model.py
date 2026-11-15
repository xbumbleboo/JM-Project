"""
CLV: BG/NBD (số lần mua) + Gamma-Gamma (giá trị mỗi lần mua), mốc 31/08/2026.

Viết bằng scipy theo công thức đóng của Fader, Hardie & Lee (2005), vì thư viện
`lifetimes` 0.11.3 không hội tụ với numpy 2.x. Hàm mục tiêu, cách tính dự báo và
CLV làm theo đúng `lifetimes` (penalizer 0,001 trên tham số, CLV 12 tháng chiết
khấu 1%/tháng), để kết quả so được với bảng `customer_clv` của bộ tham chiếu
(bảng đó được tạo bằng `lifetimes` ngày 13/09/2026).

Đầu vào: view `pbi_ngay_mua` (một dòng mỗi khách định danh mỗi ngày có doanh thu,
đã bỏ phiếu trả) — 706.121 dòng, 38.446 khách với bộ dữ liệu tham chiếu.

Chạy (Colab hoặc máy đã đăng nhập gcloud):
    export JM_PROJECT=your-project JM_DATASET=your_dataset   # mặc định: bộ gốc
    python models/clv_model.py                 # ghi clv_output.csv
    python models/clv_model.py --compare REF   # so thêm với REF = project.dataset.customer_clv
Sau đó: python models/upload_clv.py (nạp clv_output.csv thành bảng customer_clv).

Cách đọc kết quả (xem phụ lục phương pháp, mục 6): chỉ dùng để xếp hạng khách.
Không dùng giá trị tuyệt đối hay xác suất "còn hoạt động" để kết luận về rời bỏ.
"""
import os
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import betaln, gammaln, hyp2f1

PROJECT = os.environ.get("JM_PROJECT", "jm-synthetic-data")
DATASET = os.environ.get("JM_DATASET", "JM_Synthetic_Data")
SNAPSHOT = pd.Timestamp("2026-08-31")
PENALIZER = 0.001
CLV_MONTHS = 12
DISCOUNT_MONTHLY = 0.01        # giả định; chỉ ảnh hưởng mức tuyệt đối, không ảnh hưởng thứ hạng
OUTPUT_CSV = "clv_output.csv"

# Bộ tối ưu thử cả những điểm làm hàm hợp lý không xác định (log của số âm…); các điểm đó bị
# loại tự động, nên cảnh báo số học trong lúc tìm kiếm không ảnh hưởng kết quả.
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Số kiểm của bộ dữ liệu tham chiếu
EXPECTED_ROWS, EXPECTED_CUSTOMERS, EXPECTED_FREQ_ZERO = 706_121, 38_446, 6_328


# ---------------------------------------------------------------- BG/NBD
def bg_loglik(params, x, tx, T):
    r, alpha, a, b = params
    a1 = gammaln(r + x) - gammaln(r) + r * np.log(alpha)
    a2 = betaln(a, b + x) - betaln(a, b)
    a3 = -(r + x) * np.log(alpha + T)
    with np.errstate(divide="ignore", invalid="ignore"):
        a4 = np.where(x > 0,
                      betaln(a + 1, b + np.maximum(x, 1) - 1) - betaln(a, b)
                      - (r + x) * np.log(alpha + tx),
                      -np.inf)
    return a1 + np.logaddexp(a2 + a3, a4)


def bg_fit(x, tx, T, penalizer=PENALIZER):
    def obj(logp):
        p = np.exp(logp)
        return -bg_loglik(p, x, tx, T).mean() + penalizer * np.sum(p ** 2)

    best = None
    for start in ([0.5, 30, 0.5, 2], [0.2, 5, 0.8, 2.4], [1, 100, 0.01, 0.2]):
        res = minimize(obj, np.log(start), method="Nelder-Mead",
                       options={"maxiter": 20000, "maxfev": 20000, "xatol": 1e-9, "fatol": 1e-12})
        res = minimize(obj, res.x, method="L-BFGS-B")
        if best is None or res.fun < best.fun:
            best = res
    return dict(zip(["r", "alpha", "a", "b"], np.exp(best.x))), best


def bg_expected(p, t, x, tx, T):
    """Số lần mua kỳ vọng trong t ngày tới."""
    r, alpha, a, b = p["r"], p["alpha"], p["a"], p["b"]
    z = t / (alpha + T + t)
    num = (a + b + x - 1) / (a - 1) * (1 - ((alpha + T) / (alpha + T + t)) ** (r + x)
                                       * hyp2f1(r + x, b + x, a + b + x - 1, z))
    den = 1 + (x > 0) * a / (b + np.maximum(x, 1) - 1) * ((alpha + T) / (alpha + tx)) ** (r + x)
    return num / den


def bg_p_alive(p, x, tx, T):
    r, alpha, a, b = p["r"], p["alpha"], p["a"], p["b"]
    return 1 / (1 + (x > 0) * a / (b + np.maximum(x, 1) - 1) * ((alpha + T) / (alpha + tx)) ** (r + x))


# ----------------------------------------------------------- Gamma-Gamma
def gg_loglik(params, x, m):
    p, q, v = params
    return (gammaln(p * x + q) - gammaln(p * x) - gammaln(q) + q * np.log(v)
            + (p * x - 1) * np.log(m) + p * x * np.log(x) - (p * x + q) * np.log(x * m + v))


def gg_fit(x, m, penalizer=PENALIZER):
    def obj(logp):
        p = np.exp(logp)
        return -gg_loglik(p, x, m).mean() + penalizer * np.sum(p ** 2)

    best = None
    for start in ([1, 1, 1], [5, 5, float(np.median(m))], [1, 3, float(np.mean(m))]):
        res = minimize(obj, np.log(start), method="Nelder-Mead",
                       options={"maxiter": 20000, "maxfev": 20000, "xatol": 1e-9, "fatol": 1e-12})
        res = minimize(obj, res.x, method="L-BFGS-B")
        if best is None or res.fun < best.fun:
            best = res
    return dict(zip(["p", "q", "v"], np.exp(best.x))), best


def gg_expected_value(g, x, m):
    """Giá trị kỳ vọng mỗi lần mua, có điều kiện theo lịch sử của khách."""
    p, q, v = g["p"], g["q"], g["v"]
    return p * (v + x * m) / (p * x + q - 1)


def clv(p_bg, value, x, tx, T, months=CLV_MONTHS, discount=DISCOUNT_MONTHLY, days_per_month=30):
    """Như lifetimes._customer_lifetime_value với freq='D': cộng từng tháng, chiết khấu theo tháng."""
    total = np.zeros_like(x, dtype=float)
    for i in range(1, months + 1):
        t1, t0 = i * days_per_month, (i - 1) * days_per_month
        n = bg_expected(p_bg, t1, x, tx, T) - bg_expected(p_bg, t0, x, tx, T)
        total += value * n / (1 + discount) ** i
    return total


# ------------------------------------------------------------------ dữ liệu
def load_purchase_days():
    from google.cloud import bigquery
    sql = f"select customer_id, ngay, doanh_thu from `{PROJECT}.{DATASET}.pbi_ngay_mua` where ngay <= '{SNAPSHOT.date()}'"
    tx = bigquery.Client(project=PROJECT).query(sql).to_dataframe()
    tx["ngay"] = pd.to_datetime(tx["ngay"])
    tx["doanh_thu"] = tx["doanh_thu"].astype(float)
    return tx


def summarise(tx):
    """frequency = số ngày mua lặp lại; recency = lần cuối − lần đầu; T = mốc − lần đầu (ngày);
    monetary_value = bình quân giá trị các ngày mua lặp lại (bỏ ngày đầu), 0 nếu frequency = 0."""
    tx = tx.sort_values(["customer_id", "ngay"])
    g = tx.groupby("customer_id")
    first, last = g["ngay"].min(), g["ngay"].max()
    s = pd.DataFrame({
        "frequency": g.size() - 1,
        "recency": (last - first).dt.days,
        "T": (SNAPSHOT - first).dt.days,
    })
    repeat = tx[tx.groupby("customer_id").cumcount() > 0]
    s["monetary_value"] = repeat.groupby("customer_id")["doanh_thu"].mean().reindex(s.index).fillna(0.0)
    return s


def main(compare_with=None):
    tx = load_purchase_days()
    n_cust = tx["customer_id"].nunique()
    print(f"Ngày mua: {len(tx):,} dòng · {n_cust:,} khách")
    if (len(tx), n_cust) != (EXPECTED_ROWS, EXPECTED_CUSTOMERS):
        print("  Lưu ý: khác số kiểm của bộ tham chiếu "
              f"({EXPECTED_ROWS:,} / {EXPECTED_CUSTOMERS:,}) — kiểm lại dữ liệu đầu vào.")

    s = summarise(tx)
    x, tx_, T = (s[c].to_numpy(dtype=float) for c in ("frequency", "recency", "T"))
    print(f"Khách mua đúng 1 ngày (frequency = 0): {(x == 0).sum():,} (tham chiếu {EXPECTED_FREQ_ZERO:,})")

    p_bg, res = bg_fit(x, tx_, T)
    print("BG/NBD:", {k: round(float(v), 4) for k, v in p_bg.items()}, "· hội tụ", res.success)

    rep = x > 0
    m = s["monetary_value"].to_numpy(dtype=float)
    print(f"Tương quan frequency × giá trị mỗi lần (khách mua lặp lại): "
          f"{np.corrcoef(x[rep], m[rep])[0, 1]:+.4f}  (giả định Gamma-Gamma cần gần 0)")
    p_gg, gres = gg_fit(x[rep], m[rep])
    print("Gamma-Gamma:", {k: round(float(v), 4) for k, v in p_gg.items()}, "· hội tụ", gres.success)

    s["predicted_purchases"] = bg_expected(p_bg, CLV_MONTHS * 30.44, x, tx_, T)
    s["prob_alive"] = bg_p_alive(p_bg, x, tx_, T)
    s["expected_avg_value"] = np.where(rep, gg_expected_value(p_gg, x, m), np.nan)
    s["clv"] = np.where(rep, clv(p_bg, s["expected_avg_value"].to_numpy(), x, tx_, T), np.nan)
    assert s.loc[rep, ["predicted_purchases", "clv"]].notna().all().all(), "Có giá trị rỗng trong dự báo"

    ranked = s["clv"].dropna().sort_values(ascending=False)
    top = int(len(ranked) * 0.10)
    print(f"Top 10% khách ({top:,}) nắm {ranked.iloc[:top].sum() / ranked.sum():.1%} tổng CLV dự báo")

    out = s.reset_index()[["customer_id", "frequency", "recency", "T", "monetary_value",
                           "predicted_purchases", "prob_alive", "expected_avg_value", "clv"]]
    out.to_csv(OUTPUT_CSV, index=False)
    print(f"Đã ghi {len(out):,} dòng → {OUTPUT_CSV}")

    if compare_with:
        compare(out, compare_with)


def compare(out, ref_table):
    """So với bảng customer_clv tham chiếu: tương quan thứ hạng, trùng decile, tỉ trọng top 10%."""
    from google.cloud import bigquery
    from scipy.stats import spearmanr
    ref = bigquery.Client(project=PROJECT).query(
        f"select customer_id, clv, clv_decile from `{ref_table}`").to_dataframe()
    d = out.merge(ref, on="customer_id", suffixes=("", "_ref"))
    d = d[d["clv"].notna() & d["clv_ref"].notna()].copy()
    n = len(d)
    rank = d["clv"].rank(method="first", ascending=False).astype(int)
    d["decile"] = ((rank - 1) * 10) // n + 1
    same = (d["decile"] == d["clv_decile"]).mean()
    within1 = ((d["decile"] - d["clv_decile"]).abs() <= 1).mean()
    rho = spearmanr(d["clv"], d["clv_ref"])[0]
    print("\n--- So với bảng tham chiếu", ref_table, "---")
    print(f"  Khách so được          : {n:,}")
    print(f"  Spearman CLV           : {rho:.4f}")
    print(f"  Cùng decile            : {same:.2%}  · lệch tối đa 1 decile: {within1:.2%}")
    print(f"  Tổng CLV mới / tham chiếu: {d['clv'].sum() / d['clv_ref'].sum():.4f}")


if __name__ == "__main__":
    args = sys.argv[1:]
    main(compare_with=args[1] if len(args) == 2 and args[0] == "--compare" else None)

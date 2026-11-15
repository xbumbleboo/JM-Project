"""
JM SYNTHETIC DATA GENERATOR — v3.1
Sinh bộ dữ liệu bán lẻ thời trang mô phỏng theo cấu trúc hệ thống bán hàng Nhanh.vn,
dựa trên quy mô, chính sách, giá và chương trình khuyến mãi công khai của JM.
Toàn bộ dữ liệu là mô phỏng: không có số liệu kinh doanh hay thông tin khách hàng thật.

CÁCH CHẠY
    pip install -r requirements.txt
    python data-generator/generate_data.py      # ghi ra ./jm_synthetic_data_v2/
    python data-generator/qa_checks.py          # 57 phép kiểm, phải 0 FAIL
Cần nhiều RAM ở quy mô đầy đủ (máy 4 GB không chạy được; Google Colab chạy được).

TÁI LẬP
    Seed cố định (CONFIG["seed"] = 42) và ngày gốc cố định cho mọi phép tính "tính từ hôm nay"
    (CONFIG["generation_date"] = 07/09/2026). Với các phiên bản thư viện trong requirements.txt,
    chạy lại vào ngày nào cũng ra đúng bộ dữ liệu đã dùng trong báo cáo (đã kiểm 13/11/2026,
    xem docs/vi/reference-dataset.md). Các cột ghi giờ máy (synced_at, _loaded_at, updated_at,
    updatedAt) khác nhau giữa các lần chạy theo thiết kế.

OUTPUT (18 bảng). Bảng có cột lồng (ARRAY<STRUCT>) ghi NDJSON, bảng phẳng ghi CSV.
    shop_data/       depots.csv, depot_id_mapping.csv, store_mapping.csv
    product_data/    nhanh_categories.csv, nhanh_internal_categories.csv, nhanh_products_full.ndjson
    customer_data/   nhanh_customers_full.csv, t_customer_tier_final.csv
    retail_data/     bills_raw.ndjson, employees.csv, work_schedule.csv
    order_data/      orders_raw.ndjson
    bill_data/       nhanh_bills_full.ndjson
    inventory_data/  daily_snapshot.csv, health_check_log.csv, v_daily_summary.csv
    palexy_data/     daily_visits_v2.csv, hourly_traffic.csv

Quy tắc sinh dữ liệu, căn cứ của từng tham số và những điểm khác với thực tế:
docs/vi/synthetic-data-design.md. Các chú thích trong code giữ lại lý do của từng quyết định.
"""

import bisect
import gc
import json
import os
import random
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker

# ==============================================================================
# CONFIG — chỉnh ở đây để đổi quy mô / phạm vi
# ==============================================================================
CONFIG = {
    "seed": 42,
    # Ngày dùng cho mọi phép tính "tính từ hôm nay" (hiện chỉ có ngày sinh
    # khách). Cố định để chạy lại vào ngày nào cũng ra cùng bộ dữ liệu.
    # 07/09/2026 là ngày sinh ra bộ dữ liệu tham chiếu dùng trong báo cáo.
    "generation_date": date(2026, 9, 7),
    "start_date": date(2024, 1, 1),
    "end_date": date(2026, 8, 31),   # dữ liệu đến hết T8/2026 (YTD)

    # Mục tiêu số hóa đơn/đơn hàng TỔNG (offline + online) mỗi năm — mục tiêu
    # CHÍNH theo Chương 22.1 FINAL doc. Với 2026, con số này áp cho đúng
    # khoảng ngày còn lại trong "end_date" (YTD), không phải cả năm.
    "yearly_total_target": {2024: 400_000, 2025: 325_000, 2026: 180_000},

    # Chỉ là HƯỚNG DẪN phân bổ (Chương 22.3): online chiếm khoảng 35-55% tổng.
    # online = phần dư sau khi trừ offline, để tổng năm luôn khớp target ở trên.
    "online_share": 0.45,

    "n_products_parent": 600,

    # Số KH thật ĐƯỢC SINH RA ban đầu. Khách không phát sinh giao dịch nào sẽ
    # bị loại ở bước cuối (GR-CUST.16), nên số khách trong file output sẽ thấp
    # hơn con số này một chút.
    # LƯU Ý HIỆU CHỈNH (v2.1): con số cũ 260.000 khiến mỗi khách chỉ mua ~1,8
    # lần trong 32 tháng -> chi tiêu 12 tháng ~0,87tr, dưới xa ngưỡng Silver
    # (5tr) -> 97,7% khách kẹt ở Member, KHÔNG có Platinum/Diamond nào, và
    # khoảng cách giữa 2 lần mua ~297 ngày (GR-CUST.12 yêu cầu 60-90 ngày).
    # 75.000 sinh ra -> ~58.000 khách còn lại sau khi lọc khách không giao dịch,
    # nằm trong dải 50.000-200.000 của Chương 22.2 và cho ~4,9 giao dịch/khách/
    # năm -> khoảng cách giữa 2 lần mua ~75 ngày, đúng GR-CUST.12 (60-90 ngày).
    # [v3] HIỆU CHỈNH SAU M5 (hạng thẻ chỉ tính offline).
    # Bỏ doanh thu online khỏi tính hạng làm chi tiêu/khách tụt mạnh -> phân bố
    # hạng sập (Diamond = 0%). Sửa bằng 2 cần điều khiển, KHÔNG bằng cách gộp
    # lại doanh thu online (sẽ sai chính sách thật):
    #   - n_customers giảm  -> mỗi khách chi nhiều hơn (doanh thu tổng đã khoá)
    #   - k (shape) giảm    -> đuôi dày hơn, sinh ra khách VIP
    # KẾT LUẬN SAU KHI ĐO: n_customers KHÔNG dùng được làm cần điều khiển vì bị
    # khoá cứng bởi GR-CUST.12. Tổng giao dịch/năm đã chốt (~400k năm 2024), nên
    #     khoảng cách mua = 365 / (400.000 / n_customers)
    # => để rơi vào 60-90 ngày thì n_customers phải trong khoảng 66.000-98.500.
    # Hạ xuống 60.000 làm khoảng cách còn ~56 ngày -> VI PHẠM. Giữ 75.000
    # (≈68 ngày, giữa dải an toàn) và chỉ hiệu chỉnh bằng k.
    "n_customers": 75_000,

    # Tham số hình dạng (shape k) của trọng số mua hàng theo từng khách, phân
    # phối Gamma chuẩn hoá về trung bình 1. Kết hợp với việc rút khách ngẫu
    # nhiên, đây chính là mô hình Negative Binomial (NBD) — mô hình kinh điển
    # cho số lần mua lặp trong bán lẻ.
    #   k nhỏ  -> phân hoá mạnh, nhiều khách VIP chi tiêu rất lớn
    #   k lớn  -> mọi khách gần giống nhau (k -> vô cùng là bản cũ: đồng đều,
    #             đuôi Poisson cực mỏng, KHÔNG sinh ra khách VIP nào)
    # Giá trị 0,45 đã hiệu chỉnh để: hạng thẻ giảm dần đơn điệu Member→Diamond
    # (GR-CUST.11), khoảng cách mua ~75 ngày (GR-CUST.12), và ~20% khách hàng
    # đầu tạo ~60% tổng chi tiêu — đúng mức tập trung của bán lẻ thời trang.
    # [v3] Hạ từ 0,45 -> 0,18 để bù cho M5 (hạng thẻ chỉ tính offline). k nhỏ
    # hơn = phân hoá mạnh hơn = đuôi dày hơn = có khách VIP đạt Platinum/Diamond,
    # trong khi KHÔNG đụng tới tần suất mua trung bình (nên không phá GR-CUST.12).
    # Đây là cần điều khiển DUY NHẤT còn tự do sau khi n_customers bị khoá.
    "customer_weight_shape": 0.18,
    "multi_item_weights": [0.62, 0.26, 0.09, 0.03],
    "sizes": ["S", "M", "L", "XL"],
    "colors": ["Đen", "Trắng", "Kem", "Xanh Than", "Be", "Nâu", "Đỏ Đô", "Xanh Rêu"],
    # [v3 — SỬA LỖI] Mã màu 2 ký tự cho SKU code. Bản cũ dùng color[:2].upper()
    # -> "Xanh Than" và "Xanh Rêu" CÙNG ra "XA", làm mã SKU con BỊ TRÙNG (~3,7%
    # số SKU). Mã SKU là khóa join sang bills_raw/orders_raw nên trùng mã sẽ gây
    # fan-out khi join và làm sai mọi số liệu theo sản phẩm. Nay dùng bảng tra
    # cố định, không dấu, đảm bảo duy nhất.
    "color_codes": {
        "Đen": "DE", "Trắng": "TR", "Kem": "KE", "Xanh Than": "XT",
        "Be": "BE", "Nâu": "NA", "Đỏ Đô": "DD", "Xanh Rêu": "XR",
    },

    "orphan_return_rate": 0.035,       # % phiếu trả không link được hóa đơn gốc
    "placeholder_customer_rate": 0.08,
    "return_rate": 0.045,              # % hóa đơn bán offline phát sinh đổi/trả
    "points_redeem_prob": 0.20,        # xác suất 1 hóa đơn hợp lệ có tiêu điểm

    # Mốc "đổi hệ thống" làm reset field tổng hợp CỦA KHÁCH PLACEHOLDER —
    # KHÁC với mốc reset hạng thẻ/điểm 01/01/2026 (GR-CUST.10, hard-coded
    # riêng vì gắn với cửa sổ 01/07/2024-31/12/2025 cụ thể).
    "migration_date": date(2025, 4, 24),

    # Số ngày kể từ end_date mà một sản phẩm còn được coi là Active.
    # [FIX v2.2 #21] Bản trước gán status Active/Inactive NGẪU NHIÊN 82/18 cho
    # toàn bộ 7.226 SKU -> ~5.900 SKU cùng Active một lúc, gấp ~3 lần mục tiêu
    # "dưới 2.000 SKU active cùng lúc" của Chương 22.2. Thực tế thời trang: tổng
    # số SKU qua 3 năm thì lớn, nhưng tại MỘT thời điểm chỉ một phần đang bày
    # bán — hàng bộ sưu tập cũ chuyển Inactive. Nay mô phỏng đúng vòng đời đó.
    "active_sku_window_days": 220,

    "inventory_snapshot_freq_days": 7,
    "output_dir": "jm_synthetic_data_v2",
}

fake = Faker("vi_VN")


def init_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    Faker.seed(seed)


def daterange(start, end):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


class IdGen:
    """Bộ đếm ID dùng chung giữa các hàm sinh bill để không trùng."""
    def __init__(self, start):
        self.n = start

    def next(self):
        self.n += 1
        return self.n


class CustomerPicker:
    """Chọn khách hàng theo trọng số lệch phải (heterogeneity) thay vì đồng đều.

    LÝ DO TỒN TẠI [FIX v2.1 #13]: bản cũ dùng random.choice() đồng đều, nghĩa
    là mọi khách có xác suất mua như nhau -> số lần mua theo phân phối Poisson
    quanh giá trị trung bình, đuôi cực mỏng, KHÔNG có khách "cá voi". Hệ quả:
    không khách nào đạt Platinum/Diamond, RFM tier chỉ đang cắt nhiễu thống kê
    chứ không phản ánh hành vi, và CLV/loyalty analysis vô nghĩa.

    Ở đây trọng số rút từ phân phối GAMMA (chuẩn hoá trung bình = 1). Rút khách
    theo trọng số Gamma rồi đếm số lần mua chính là mô hình Negative Binomial
    (NBD) — mô hình kinh điển và được kiểm chứng thực nghiệm cho hành vi mua
    lặp trong bán lẻ (Ehrenberg). Ưu điểm so với lognormal: đuôi suy giảm theo
    hàm mũ nên hạng thẻ cao nhất (Diamond, không có trần) không bị phình to
    hơn hạng ngay dưới nó (Platinum, dải hẹp 25-40tr) — giữ đúng hình chóp
    giảm dần mà GR-CUST.11 yêu cầu.
    """

    def __init__(self, ids, shape):
        self.ids = list(ids)
        if shape is None or shape <= 0:
            weights = np.ones(len(self.ids))
        else:
            # scale = 1/shape để trung bình = shape × scale = 1
            weights = np.random.gamma(shape=shape, scale=1.0 / shape, size=len(self.ids))
            weights = np.maximum(weights, 1e-9)
        self.cum = np.cumsum(weights).tolist()
        self._buf = []
        self._buf_i = 0

    def pick(self):
        """Lấy 1 khách. Sinh sẵn theo lô để tránh gọi random.choices 800k lần."""
        if self._buf_i >= len(self._buf):
            self._buf = random.choices(self.ids, cum_weights=self.cum, k=20_000)
            self._buf_i = 0
        v = self._buf[self._buf_i]
        self._buf_i += 1
        return v


# ==============================================================================
# 1. SHOP_DATA — cửa hàng / kho  [FIX #1, #2]
# ==============================================================================
# Đủ 29 điểm bán theo bảng 4.1 + 2 kho tổng. tier: 1=Hà Nội, 2=TP.HCM/Hải
# Phòng/Đà Nẵng, 3 = các tỉnh còn lại (đúng 4.2 "Tier thị trường").
STORE_BLUEPRINT = [
    # (mã vùng, tỉnh/TP, số CH, tier, đơn/ngày min, đơn/ngày max, số CH TTTM)
    ("HN",  "Hà Nội",           11, 1, 70, 110, 3),   # Times City, AEON Hà Đông, Ocean Park
    ("HCM", "TP. Hồ Chí Minh",   3, 2, 45,  75, 0),
    ("HP",  "Hải Phòng",         2, 2, 35,  60, 1),   # AEON Lê Chân
    ("DN",  "Đà Nẵng",           1, 2, 35,  60, 0),
    ("BN",  "Bắc Ninh",          1, 3, 12,  30, 0),
    ("HD",  "Hải Dương",         1, 3, 12,  30, 0),
    ("TB",  "Thái Bình",         1, 3, 12,  30, 0),
    ("NB",  "Ninh Bình",         1, 3, 12,  30, 0),
    ("TH",  "Thanh Hóa",         1, 3, 12,  30, 0),
    ("NA",  "Nghệ An",           1, 3, 12,  30, 0),
    ("HUE", "Thừa Thiên Huế",    1, 3, 12,  30, 1),   # AEON Huế
    ("DNA", "Đồng Nai",          2, 3, 12,  30, 0),
    ("BD",  "Bình Dương",        1, 3, 12,  30, 0),
    ("BRVT","Bà Rịa - Vũng Tàu", 1, 3, 12,  30, 0),
    ("CT",  "Cần Thơ",           1, 3, 12,  30, 0),
]
assert sum(n for _, _, n, *_ in STORE_BLUEPRINT) == 29
assert sum(nm for *_, nm in STORE_BLUEPRINT) == 5   # GR-ST.3

REGION_OF = {
    "HN": "Miền Bắc", "HP": "Miền Bắc", "BN": "Miền Bắc", "HD": "Miền Bắc",
    "TB": "Miền Bắc", "NB": "Miền Bắc",
    "TH": "Miền Trung", "NA": "Miền Trung", "HUE": "Miền Trung", "DN": "Miền Trung",
    "HCM": "Miền Nam", "DNA": "Miền Nam", "BD": "Miền Nam", "BRVT": "Miền Nam",
    "CT": "Miền Nam",
}


# Mã tỉnh cố định, lấy đúng giá trị của bộ dữ liệu tham chiếu. Bản cũ dùng
# hash() nên mã đổi sau mỗi lần khởi động Python.
CITY_ID = {
    "Hà Nội": 27, "TP. Hồ Chí Minh": 36, "Hải Phòng": 11, "Đà Nẵng": 20,
    "Bắc Ninh": 14, "Hải Dương": 67, "Thái Bình": 49, "Ninh Bình": 86,
    "Thanh Hóa": 45, "Nghệ An": 43, "Thừa Thiên Huế": 85, "Đồng Nai": 22,
    "Bình Dương": 69, "Bà Rịa - Vũng Tàu": 17, "Cần Thơ": 47,
}


def gen_depots():
    stores = []
    depot_id = 1000
    for code, province, n, tier, lo, hi, n_mall in STORE_BLUEPRINT:
        for i in range(1, n + 1):
            depot_id += 1
            is_mall = i <= n_mall
            is_center = is_mall or (random.random() < (0.7 if tier == 1 else
                                                       0.5 if tier == 2 else 0.35))
            perf = np.random.uniform(0.62, 1.45)
            if is_mall:   perf *= 1.28
            if is_center: perf *= 1.18
            aov_f = {1: 1.12, 2: 1.00, 3: 0.90}[tier]
            if is_mall:   aov_f *= 1.06
            if is_center: aov_f *= 1.03
            if code == "HP":
                aov_f *= 0.80          # GR-ST.5: Hải Phòng thấp hơn mặt bằng chung ~20%
            aov_f *= np.random.uniform(0.96, 1.04)
            stores.append({
                "id": depot_id,
                "code": f"STORE_{code}_{i:02d}",
                "name": f"JM {code} {i:02d}",
                "province": province,
                "region": REGION_OF[code],
                "tier": tier,
                "store_format": "TTTM" if is_mall else "Mặt phố",
                "location_type": "Trung tâm" if is_center else "Ven đô",
                "perf_factor": round(perf, 3),
                "aov_factor": round(aov_f, 3),
                "base_orders_lo": lo,
                "base_orders_hi": hi,
                "is_warehouse": False,
            })
    # [v3] WH_LOI — kho hàng lỗi. Nơi chứa hàng hoàn ở tình trạng Damaged (10%
    # số phiếu hoàn): hàng VỀ kho thật nhưng KHÔNG bán lại được.
    # Ban đầu định dùng một mã kho tự chế chỉ xuất hiện trong daily_snapshot,
    # nhưng như vậy sẽ tạo mã kho không join được về depots — một quả mìn cho
    # bất kỳ phân tích nào join snapshot với dimension cửa hàng. Khai báo thành
    # depot thật (is_warehouse=True, giống WH_HN/WH_HCM đã có) giữ được toàn
    # vẹn tham chiếu 100% mà vẫn không đụng schema.
    for wcode, prov in [("WH_HN", "Hà Nội"), ("WH_HCM", "TP. Hồ Chí Minh"),
                        ("WH_LOI", "Hà Nội")]:
        depot_id += 1
        stores.append({
            "id": depot_id, "code": wcode,
            "name": "Kho hàng lỗi" if wcode == "WH_LOI" else f"Kho tổng {wcode}",
            "province": prov, "region": REGION_OF["HCM" if "HCM" in wcode else "HN"],
            "tier": 0, "store_format": "Kho", "location_type": "Kho",
            "perf_factor": 0, "aov_factor": 1.0,
            "base_orders_lo": 0, "base_orders_hi": 0, "is_warehouse": True,
        })

    df = pd.DataFrame([{
        "id": s["id"], "code": s["code"], "name": s["name"],
        "mobile": fake.phone_number(),
        "city_id": CITY_ID[s["province"]],
        "city_name": s["province"],
        "district_id": random.randint(1, 700),
        "district_name": f"Quận/Huyện {random.randint(1, 12)}",
        "ward_id": random.randint(1, 11000),
        "ward_name": f"Phường {random.randint(1, 30)}",
        "address": f"Số {random.randint(1, 400)}, {s['province']}",
        "store_format": s["store_format"], "location_type": s["location_type"],
        "synced_at": datetime.now().isoformat(timespec="seconds"),
    } for s in stores])
    return df, stores


def gen_depot_id_mapping(stores):
    return pd.DataFrame([{
        "code": s["code"], "name": s["name"],
        "old_depot_id": s["id"] - 500, "new_depot_id": s["id"],
    } for s in stores])


# ==============================================================================
# 2. PRODUCT_DATA — danh mục + sản phẩm  [FIX #3]
# ==============================================================================
CATEGORIES = ["Áo", "Đầm", "Quần", "Chân váy", "Set bộ", "Áo khoác", "Phụ kiện"]

# Đúng 20 BST thật ở Chương 6.2. "kind" chỉ dùng nội bộ để mô hình hoá phân bố
# ngày bán (GR-PRD.7): occasion = bán tập trung quanh dịp; basic = đều quanh
# năm; other = không có pattern đặc biệt được xác nhận, để phân bố tự nhiên.
COLLECTIONS = [
    ("BST 14/2", "occasion"), ("BST 8/3", "occasion"), ("BST TẾT", "occasion"),
    ("BST BASIC", "basic"),
    ("BST BLAZER", "other"), ("BST LEN THUN", "other"), ("BST OFFICE", "other"),
    ("BST ONLINE", "other"), ("BST PARTY", "other"), ("BST PATTERN", "other"),
    ("BST POPLIN", "other"), ("BST RESORT", "other"), ("BST STREET", "other"),
    ("BST T-SHIRT", "other"), ("BST TRENCH COAT", "other"), ("BST TWEED", "other"),
    ("BST ÁO DÀI", "other"), ("FOB THU ĐÔNG", "other"),
    ("SP DẪN XUÂN HÈ 26", "other"), ("ÁO SƠ MI", "other"),
]
assert len(COLLECTIONS) == 20   # GR-PRD.2

# Cửa sổ "dịp lễ" cho BST occasion — (tháng, ngày bắt đầu, ngày kết thúc).
OCCASION_WINDOW = {
    "BST 14/2": (2, 1, 14),
    "BST 8/3": (3, 1, 10),
    "BST TẾT": (1, 1, 25),
}

STYLE_WORDS = ["Thanh Lịch", "Xếp Ly", "Sát Nách", "Tay Bồng", "Cổ Đức", "Dáng Suông",
               "Ôm Body", "Cách Điệu", "Phối Ren", "Trơn Basic"]


def gen_categories():
    df_cat = pd.DataFrame([{
        "id": 100 + i, "code": f"CAT{i:02d}", "name": name, "parent_id": None,
        "_loaded_at": datetime.now().isoformat(timespec="seconds"),
    } for i, name in enumerate(CATEGORIES, 1)])

    df_int = pd.DataFrame([{
        "id": 200 + i, "code": f"BST{i:02d}", "name": name, "parent_id": None,
        "_loaded_at": datetime.now().isoformat(timespec="seconds"),
    } for i, (name, _kind) in enumerate(COLLECTIONS, 1)])
    return df_cat, df_int


def _occasion_created_date(name, start, end):
    """Ngày tạo SP của BST occasion rải quanh (trước) cửa sổ dịp lễ, đúng năm nào đó trong kỳ."""
    m, d1, _d2 = OCCASION_WINDOW[name]
    years = list(range(start.year, end.year + 1))
    y = random.choice(years)
    try:
        peak = date(y, m, d1)
    except ValueError:
        peak = date(y, m, 1)
    created = peak - timedelta(days=random.randint(10, 55))
    return max(start, min(end, created))


def gen_products(df_cat, df_int, n_parent):
    price_range = {
        "Áo": (250_000, 650_000), "Đầm": (450_000, 1_200_000),
        "Quần": (350_000, 750_000), "Chân váy": (300_000, 700_000),
        "Set bộ": (600_000, 1_500_000), "Áo khoác": (700_000, 1_800_000),
        # [v3] Tách Phụ kiện thành 2 nhóm theo dải giá thật trên jm.com.vn:
        #   - Đi kèm trang phục (mấn áo dài, phụ kiện đồng bộ BST): 150-350k
        #   - Lifestyle/merchandise (bình giữ nhiệt, hộp quà thiết kế): 250-500k
        # v2 gộp chung 99-350k nên không phủ hết dải lifestyle tới 500k.
        "Phụ kiện": (150_000, 350_000),
        "Phụ kiện Lifestyle": (250_000, 500_000),
    }
    col_kind = dict(COLLECTIONS)
    start, end = CONFIG["start_date"], CONFIG["end_date"]
    parents, children = [], []
    pid = 500_000
    used_parent_codes = set()
    for _p in range(n_parent):
        cat = df_cat.sample(1).iloc[0]
        col = df_int.sample(1).iloc[0]
        lo, hi = price_range[cat["name"]]
        retail = int(round(np.random.uniform(lo, hi) / 1000) * 1000)
        avg_cost = int(retail * np.random.uniform(0.35, 0.45))
        pid += 1
        parent_id = pid
        # [v3 — SỬA LỖI] Ép mã SP cha DUY NHẤT. Bản cũ rút ngẫu nhiên không kiểm
        # tra trùng, ở 600 SP vẫn có va chạm -> kéo theo mã SKU con trùng.
        while True:
            parent_code = (f"{random.choice('1234567')}{random.choice('RSTA')}"
                           f"{random.randint(1,99):02d}.{random.randint(2402,2608)}")
            if parent_code not in used_parent_codes:
                used_parent_codes.add(parent_code)
                break
        parent_name = f"{cat['name']} {random.choice(STYLE_WORDS)} {random.choice(STYLE_WORDS)}"
        kind = col_kind.get(col["name"], "other")
        if kind == "occasion":
            created = _occasion_created_date(col["name"], start, end)
        else:
            created = start + timedelta(days=random.randint(0, (end - start).days))
        parents.append({
            "id": parent_id, "parent_id": None, "code": parent_code,
            "name": parent_name, "category_id": cat["id"],
            "internal_category_id": col["id"], "retail": retail,
            "avg_cost": avg_cost, "created": created,
        })
        for size in CONFIG["sizes"]:
            for color in random.sample(CONFIG["colors"], k=random.randint(2, 4)):
                pid += 1
                children.append({
                    "id": pid, "parent_id": parent_id,
                    "code": f"{parent_code}-{CONFIG['color_codes'][color]}-{size}",
                    "name": f"{parent_name} - {color} - {size}",
                    "category_id": cat["id"], "internal_category_id": col["id"],
                    "retail": retail, "avg_cost": avg_cost,
                    "size": size, "color": color, "created": created,
                    "cat_name": cat["name"], "col_name": col["name"],
                })
    return parents, children


def build_products_df(parents, children, stores):
    """nhanh_products_full — nested cols (prices/inventory/images/...) giữ dạng
    native list/dict, xuất NDJSON ở bước ghi file (FIX #11)."""
    rows = []
    store_ids = [s["id"] for s in stores]
    col_kind = dict(COLLECTIONS)
    # Vòng đời sản phẩm (GR-PRD.7 + Chương 22.2): BST BASIC bán đều quanh năm nên
    # luôn Active; các BST khác chỉ Active nếu ra mắt trong cửa sổ gần đây, hàng
    # bộ sưu tập cũ chuyển Inactive. Nhờ vậy tổng SKU qua 3 năm vẫn lớn nhưng số
    # SKU Active CÙNG LÚC nằm dưới 2.000.
    active_cutoff = CONFIG["end_date"] - timedelta(days=CONFIG["active_sku_window_days"])
    for c in children:
        remain = max(0, int(np.random.gamma(2.0, 12)))
        available = max(0, remain - random.randint(0, 3))
        depots = []
        for did in random.sample(store_ids, k=min(len(store_ids), random.randint(3, 10))):
            q = max(0, int(np.random.poisson(2.5)))
            depots.append({"depot_id": did, "remain": q, "available": q,
                           "shipping": 0, "holding": 0, "damage": 0,
                           "warranty": 0, "warranty_holding": 0,
                           "holding_new": 0, "shipping_export": 0})
        rows.append({
            "id": c["id"], "parent_id": c["parent_id"], "code": c["code"],
            "barcode": f"893{random.randint(10**9, 10**10-1)}",
            "name": c["name"], "other_name": None,
            "status": ("Active" if (col_kind.get(c["col_name"]) == "basic"
                                    or c["created"] >= active_cutoff)
                       else "Inactive"),
            "category_id": c["category_id"],
            "internal_category_id": c["internal_category_id"],
            "prices": {
                "retail": c["retail"], "import": int(c["avg_cost"] * 1.05),
                "old": 0, "wholesale": 0, "avg_cost": c["avg_cost"],
            },
            "vat": 0,
            "inventory": {
                "remain": remain, "available": available, "shipping": 0,
                "holding": 0, "damaged": max(0, int(np.random.poisson(0.15))),
                "warranty_remain": 0, "warranty_holding": 0,
                "holding_new": 0, "shipping_export": 0, "depots": depots,
            },
            "images": [f"https://cdn.example/{c['id']}_{i}.jpg" for i in range(1, 4)],
            "warranty": {"month": 0, "phone": None, "address": None},
            "brand": {"id": 1, "name": "JM"},
            "type": {"id": 1, "name": "Sản phẩm"},
            "shipping": {"length": 30, "width": 25, "height": 5,
                         "weight": random.choice([200, 300, 400, 500])},
            "country_name": "Việt Nam",
            "units": None, "combos": None, "attributes": None, "suppliers": None,
            "videos": None, "branch_prices": None,
            "created_at": datetime.combine(c["created"], datetime.min.time()).isoformat(timespec="seconds"),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "description": None, "content": None, "child_ids": None,
        })
    return pd.DataFrame(rows)


# ==============================================================================
# 3. RETAIL_DATA — nhân viên + lịch làm việc  [FIX #4]
# ==============================================================================
ROLES = ["Quản lý cửa hàng", "Nhân viên bán hàng", "Thu ngân"]

# Bảng 5.2 — đúng 2 ca theo vị trí (Thu ngân dùng chung khung giờ NV bán hàng,
# vì bảng 5.2 gốc không tách riêng Thu ngân).
# [v3] planned_hours chuyển sang định mức CÁ NHÂN thống nhất: 26 công x 7 giờ
# = 182 giờ/người/tháng. v2 dùng baseline 7,5h (NV/Thu ngân) và 8,0h (Quản lý)
# — không khớp định mức đã chốt và làm năng suất/giờ công lệch giữa 2 nhóm.
HOURS_PER_SHIFT = 7.0
WORK_DAYS_PER_MONTH = 26
MONTHLY_HOURS_PER_EMPLOYEE = WORK_DAYS_PER_MONTH * HOURS_PER_SHIFT  # = 182 giờ

SHIFT_WINDOWS = {
    "Quản lý cửa hàng": [("10:00-18:30", HOURS_PER_SHIFT), ("14:00-22:30", HOURS_PER_SHIFT)],
    "Nhân viên bán hàng": [("08:30-15:30", HOURS_PER_SHIFT), ("15:30-22:30", HOURS_PER_SHIFT)],
    "Thu ngân": [("08:30-15:30", HOURS_PER_SHIFT), ("15:30-22:30", HOURS_PER_SHIFT)],
}


def gen_employees(stores):
    emps = []
    eid = 9000
    for s in stores:
        if s["is_warehouse"]:
            continue
        n_staff = 5 if s["tier"] == 1 else (4 if s["tier"] == 2 else 3)
        for j in range(n_staff + 1):
            eid += 1
            emps.append({
                "emp_id": f"EMP{eid}", "emp_name": fake.name(),
                "phone": fake.phone_number(), "store_id": s["code"],
                "role": ROLES[0] if j == 0 else random.choice(ROLES[1:]),
                "is_active": random.random() > 0.12,
                "created_at": datetime.combine(
                    CONFIG["start_date"] + timedelta(days=random.randint(0, 700)),
                    datetime.min.time()).isoformat(timespec="seconds"),
            })
    return pd.DataFrame(emps)


def gen_work_schedule(df_emp, start, end, sample_days=None):
    """GR-HR.3: ca làm chỉ nhận 2 giá trị/vị trí đúng khung giờ bảng 5.2.

    [v3] MỞ TOÀN KỲ: v2 chỉ sinh 180 ngày gần nhất, khiến phân tích năng suất
    lao động (roadmap Mục 16) bị giới hạn cứng và không so sánh được theo năm.
    Nay phủ trọn start..end. Truyền sample_days để giới hạn lại nếu cần test.

    [v3] Tỉ lệ nghỉ hiệu chỉnh để số công/tháng ≈ 26 (định mức cá nhân), tức
    nghỉ ~4,4/30,4 ngày, thay cho mức 4/30 của v2.
    planned_hours = 7,0 giờ đồng nhất mọi vị trí (xem HOURS_PER_SHIFT).
    """
    rows = []
    if sample_days is None:
        days = list(daterange(start, end))          # TOÀN KỲ
    else:
        days = [end - timedelta(days=i) for i in range(sample_days)]
    for _, e in df_emp[df_emp["is_active"]].iterrows():
        windows = SHIFT_WINDOWS[e["role"]]
        for d in days:
            # nghỉ sao cho số công/tháng ≈ WORK_DAYS_PER_MONTH (26/30,4 ngày)
            if random.random() > (WORK_DAYS_PER_MONTH / 30.4):
                continue
            shift_label, hours = random.choice(windows)
            rows.append({
                "emp_id": e["emp_id"], "store_id": e["store_id"],
                "work_date": d.isoformat(), "shift_name": shift_label,
                "planned_hours": hours,
                "actual_hours": round(hours + np.random.normal(0, 0.4), 2),
            })
    return pd.DataFrame(rows)


# ==============================================================================
# 4. CUSTOMER_DATA — khách hàng
# ==============================================================================
PLACEHOLDER_CUSTOMERS = [
    {"id": 1, "name": "PHÒNG NHÂN SỰ",    "mobile": "0862050982"},
    {"id": 2, "name": "KHÁCH LẺ",          "mobile": "0000000000"},
    {"id": 3, "name": "KHÁCH NƯỚC NGOÀI",  "mobile": "0000000001"},
]


def _shift_year(d, years):
    """Giống change_year của Faker: 29/02 rơi vào năm thường thì về 28/02."""
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d.replace(year=d.year + years, day=28)


def _date_of_birth(minimum_age, maximum_age):
    """Cùng logic và cùng chuỗi số ngẫu nhiên với fake.date_of_birth(),
    nhưng tính từ CONFIG["generation_date"] thay vì datetime.now().

    Dùng date_time_ad của Faker để giữ nguyên chuỗi số ngẫu nhiên.
    KHÔNG nâng phiên bản Faker (đã pin trong requirements.txt) mà không
    kiểm lại việc tái lập bộ dữ liệu tham chiếu.
    """
    anchor = CONFIG["generation_date"]
    start = _shift_year(anchor, -(maximum_age + 1))
    end = _shift_year(anchor, -minimum_age)
    dob = fake.date_time_ad(start_datetime=start, end_datetime=end).date()
    return dob if dob != start else dob + timedelta(days=1)


def _gen_mobile():
    while True:
        m = f"0{random.choice([3,5,7,8,9])}{random.randint(10**7, 10**8-1)}"
        if not m.endswith("982"):
            return m


def gen_customers(n_real):
    rows = []
    for p in PLACEHOLDER_CUSTOMERS:
        rows.append({
            "id": p["id"], "type": "1", "name": p["name"], "mobile": p["mobile"],
            "gender": None, "birthday": None,
            "startedDate": CONFIG["start_date"].isoformat(),
            "is_placeholder": True,
        })
    cid = 100_000
    for _ in range(n_real):
        cid += 1
        rows.append({
            "id": cid, "type": "1", "name": fake.name(),
            "mobile": _gen_mobile(),
            "gender": random.choices(["female", "male"], weights=[0.88, 0.12])[0],
            "birthday": _date_of_birth(18, 55).isoformat(),
            # startedDate để trống ở đây — sẽ gán bằng NGÀY GIAO DỊCH ĐẦU TIÊN
            # thật sự ở finalize_customers (GR-CUST.16). Bản cũ gán ngẫu nhiên
            # nên có khách "đăng ký" năm 2026 nhưng lại có hóa đơn từ 2024.
            "startedDate": None,
            "is_placeholder": False,
        })
    return pd.DataFrame(rows)


# ==============================================================================
# 5. LỊCH KHUYẾN MÃI & SEASONALITY  [FIX #9]
# ==============================================================================
# Đúng 7 chương trình bảng 7.1 (GR-PROMO.1) + mốc 30/4-1/5 riêng (GR-OFF.6).
# (tên, tháng bắt đầu, ngày bắt đầu, tháng kết thúc, ngày kết thúc,
#  hệ số lưu lượng, độ sâu giảm giá thêm)
PROMOTIONS = [
    ("Xả kho cuối năm & Chào Xuân", 1, 1, 1, 25, 1.30, 0.15),
    ("Hot Sale 8/3",                3, 1, 3, 8,  1.45, 0.20),
    ("30/4 - 1/5",                  4, 27, 5, 3, 1.25, 0.10),
    ("Sale sinh nhật JM",           6, 20, 7, 15, 1.25, 0.15),
    ("Sale giữa tháng 15/7",        7, 13, 7, 17, 1.20, 0.10),
    ("End of Season Sale",         7, 20, 8, 20, 1.15, 0.15),
    ("Black Friday",               10, 30, 11, 13, 1.45, 0.30),   # SỬA: 30/10-13/11, không phải cuối T11
    ("Ra mắt BST mới",             10, 1, 12, 31, 1.10, 0.05),
]


def _in_window(d, m1, d1, m2, d2):
    """True nếu ngày d nằm trong [m1/d1, m2/d2] (hỗ trợ khoảng vắt qua 2 tháng)."""
    if m1 == m2:
        return d.month == m1 and d1 <= d.day <= d2
    if d.month == m1:
        return d.day >= d1
    if d.month == m2:
        return d.day <= d2
    return m1 < d.month < m2 if m1 < m2 else (d.month > m1 or d.month < m2)


def event_effect(d: date):
    """Trả về (hệ số lưu lượng, độ sâu giảm giá thêm) — lấy chương trình có
    hệ số lưu lượng cao nhất nếu nhiều chương trình trùng ngày."""
    best = (1.0, 0.0)
    for _name, m1, d1, m2, d2, traf, disc in PROMOTIONS:
        if _in_window(d, m1, d1, m2, d2) and traf > best[0]:
            best = (traf, disc)
    return best


# [v3] Black Friday có luật SỐ LƯỢNG TỐI THIỂU: "mua 4 giảm 15%" — khác hẳn
# giảm giá theo % thông thường, vì nó thưởng cho việc gom nhiều món vào một
# hóa đơn. Bản cũ mô hình hóa bằng extra_disc chung nên hóa đơn 1 món cũng
# được giảm như hóa đơn 4 món, làm mất hoàn toàn hiệu ứng lên UPT/giỏ hàng.
BF_MIN_ITEMS = 4
BF_BUNDLE_RATE = 0.15


def is_black_friday(d: date) -> bool:
    return _in_window(d, 10, 30, 11, 13)


def price_inflation(d: date) -> float:
    years = (d - date(2024, 1, 1)).days / 365.25
    return 1.09 ** years


def seasonality_factor(d: date) -> float:
    m = d.month
    base = {1: 1.35, 2: 0.70, 3: 0.85, 4: 1.00, 5: 1.05, 6: 0.95,
            7: 0.80, 8: 0.85, 9: 1.00, 10: 1.05, 11: 1.20, 12: 1.40}[m]
    base *= event_effect(d)[0]
    if d.weekday() >= 5:
        base *= 1.35
    return base


# ==============================================================================
# 6. QUY MÔ — hiệu chỉnh hệ số theo năm để khớp target thay vì dò tay [FIX #10]
# ==============================================================================
def calibrate_offline_scale(stores, start, end, target_offline_by_year):
    """Tính hệ số nhân theo năm sao cho tổng offline KỲ VỌNG (trước khi random
    Poisson) khớp target_offline_by_year. Dùng kỳ vọng (mean base) thay vì mô
    phỏng thật để rẻ và tất định."""
    raw_by_year = {}
    for s in stores:
        if s["is_warehouse"]:
            continue
        mean_base = (s["base_orders_lo"] + s["base_orders_hi"]) / 2
        for d in daterange(start, end):
            raw_by_year[d.year] = raw_by_year.get(d.year, 0.0) + \
                mean_base * s["perf_factor"] * seasonality_factor(d)
    mult = {}
    for y, raw in raw_by_year.items():
        tgt = target_offline_by_year.get(y)
        mult[y] = (tgt / raw) if (tgt and raw > 0) else 1.0
    return mult


# ==============================================================================
# 7. RETAIL_DATA.bills_raw — HÓA ĐƠN BÁN LẺ (chỉ hóa đơn BÁN, chưa gồm đổi/trả)
# ==============================================================================
def pick_products_for_bill(children_active, n_items, d=None, aov_factor=1.0,
                            child_by_collection=None):
    """Chọn dòng sản phẩm cho một hóa đơn.

    GR-PRD.7: nếu ngày d rơi vào cửa sổ 1 BST occasion (14/2, 8/3, TẾT), tăng
    trọng số chọn SP thuộc BST đó (bán tập trung quanh dịp).
    """
    pool_source = children_active
    if d is not None and child_by_collection:
        boosted = []
        for name, (m, d1, d2) in OCCASION_WINDOW.items():
            if d.month == m and d1 <= d.day <= d2:
                boosted.extend(child_by_collection.get(name, []))
        if boosted:
            pool_source = boosted * 3 + children_active

    pool = random.sample(pool_source, k=min(n_items * 5, len(pool_source)))
    pool.sort(key=lambda x: x["retail"])
    n = len(pool)
    bias = max(-0.35, min(0.35, (aov_factor - 1.0) * 1.6))
    picked = []
    for _ in range(min(n_items, n)):
        u = random.random()
        u = min(0.999, max(0.0, u + bias * (1 - abs(2 * u - 1))))
        cand = pool[int(u * n)]
        if cand not in picked:
            picked.append(cand)
    if not picked:
        picked = [random.choice(pool)]

    infl = price_inflation(d) if d else 1.0
    _, extra_disc = event_effect(d) if d else (1.0, 0.0)

    # [v3] Black Friday: luật "mua >= 4 món giảm 15%". Trong cửa sổ BF, khách
    # có xu hướng gom thêm món để đạt ngưỡng -> mô hình hóa bằng cách tăng xác
    # suất mua 2 cái/dòng, rồi chỉ áp mức giảm bundle khi hóa đơn ĐẠT ngưỡng.
    bf = is_black_friday(d) if d else False

    items = []
    for p in picked:
        qty = 1 if random.random() < (0.85 - 0.08 * (aov_factor - 1)) else 2
        if bf and random.random() < 0.35:
            qty = max(qty, 2)
        price = int(round(p["retail"] * infl / 1000) * 1000)
        r = random.random()
        if r < 0.55:      disc_pct = 0.0
        elif r < 0.85:    disc_pct = random.choice([0.1, 0.15, 0.2])
        else:             disc_pct = random.choice([0.3, 0.4, 0.5])
        disc_pct = min(0.7, disc_pct + extra_disc)
        discount = int(price * qty * disc_pct)
        amount = price * qty - discount
        items.append({
            "imexId": random.randint(10**6, 10**7),
            "id": p["id"], "code": p["code"], "barcode": None,
            "name": p["name"], "quantity": qty, "price": price,
            "discount": discount, "totalDiscount": discount, "amount": amount,
            "_avg_cost": p["avg_cost"],
        })

    # Luật số lượng tối thiểu: chỉ khi TỔNG SỐ MÓN >= 4 mới được mức bundle 15%,
    # và chỉ nâng cho những dòng đang được giảm ÍT HƠN 15% (không hạ mức của
    # hàng vốn đã sale sâu hơn).
    if bf and sum(i["quantity"] for i in items) >= BF_MIN_ITEMS:
        for i in items:
            gross = i["price"] * i["quantity"]
            floor = int(gross * BF_BUNDLE_RATE)
            if i["discount"] < floor:
                i["discount"] = floor
                i["totalDiscount"] = floor
                i["amount"] = gross - floor
    return items


def _clean_items(items):
    return [{k: v for k, v in i.items() if not k.startswith("_")} for i in items]


def _split_payment(amount):
    """Phân bổ TOÀN BỘ `amount` vào đúng một phương thức thanh toán, theo cơ
    cấu tiền mặt 42% / chuyển khoản 38% / thẻ 20%. Đảm bảo GR-OFF.4: tổng các
    phương thức luôn bằng payment_amount (không bao giờ để cả ba = 0)."""
    r = random.random()
    cash = transfer = credit = 0
    if r < 0.42:
        cash = amount
    elif r < 0.80:
        transfer = amount
    else:
        credit = amount
    return {"payment_cash_amount": cash,
            "payment_transfer_amount": transfer,
            "payment_credit_amount": credit}


def gen_sales_bills(stores, children, df_cust, df_emp, start, end, bill_ctr,
                     scale_mult, child_by_collection, picker):
    """Chỉ sinh hóa đơn BÁN (bill_type=2). Đổi/trả được sinh riêng ở gen_returns
    sau khi đã biết hạng thẻ của khách (tier_lookup gộp cả 2 kênh)."""
    cust_ph = df_cust[df_cust["is_placeholder"]]["id"].tolist()
    emp_by_store = df_emp.groupby("store_id")["emp_id"].apply(list).to_dict()
    emp_name = dict(zip(df_emp["emp_id"], df_emp["emp_name"]))

    bills = []
    bills_per_day = {}
    sold_history = []

    for s in stores:
        if s["is_warehouse"]:
            continue
        emps = emp_by_store.get(s["code"], [])
        if not emps:
            continue
        for d in daterange(start, end):
            base = np.random.uniform(s["base_orders_lo"], s["base_orders_hi"])
            # QUAN TRỌNG: KHÔNG int() giá trị kỳ vọng trước khi đưa vào Poisson —
            # làm vậy sẽ làm tròn về 0 một cách hệ thống mỗi khi kỳ vọng < 1
            # (ví dụ khi calibrate ra scale_mult nhỏ ở quy mô test), gây lệch âm
            # tích lũy. Giữ nguyên số thực, chỉ Poisson-sample.
            lam = base * s["perf_factor"] * seasonality_factor(d) * scale_mult.get(d.year, 1.0)
            n = max(0, int(np.random.poisson(max(lam, 0.05))))
            bills_per_day[(s["code"], d)] = n
            for _ in range(n):
                bill_id = bill_ctr.next()
                emp = random.choice(emps)
                if random.random() < CONFIG["placeholder_customer_rate"]:
                    cust = random.choice(cust_ph)
                else:
                    cust = picker.pick()   # trọng số lệch phải, không đồng đều
                items = pick_products_for_bill(
                    children, n_items=random.choices([1, 2, 3, 4], weights=CONFIG["multi_item_weights"])[0],
                    d=d, aov_factor=s["aov_factor"], child_by_collection=child_by_collection)
                total = sum(i["amount"] for i in items)
                total_disc = sum(i["discount"] for i in items)
                r = random.random()
                cash = transfer = credit = 0
                if r < 0.42:   cash = total
                elif r < 0.80: transfer = total
                else:          credit = total
                ts = datetime.combine(d, datetime.min.time()) + timedelta(
                    hours=random.randint(9, 21), minutes=random.randint(0, 59))
                bills.append({
                    "bill_id": str(bill_id), "bill_date": d.isoformat(),
                    "bill_datetime": ts.isoformat(timespec="seconds"),
                    "depot_id": s["id"], "bill_type": "2", "bill_mode": "2",
                    "order_id": None, "customer_id": cust,
                    "created_user_id": None, "created_user_name": emp_name.get(emp),
                    "created_at": ts.isoformat(timespec="seconds"),
                    "sale_user_id": emp, "sale_user_name": emp_name.get(emp),
                    "products": _clean_items(items),
                    "payment_amount": total, "payment_customer_amount": total,
                    "payment_discount": total_disc,
                    "payment_points": 0, "payment_used_points_value": 0,
                    "payment_used_points_amount": 0,
                    "payment_transfer_amount": transfer, "payment_cash_amount": cash,
                    "payment_credit_amount": credit,
                    "payment_coupon_value": 0, "payment_coupon_amount": 0,
                    "payment_return_fee": 0, "payment_return_amount": 0,
                    "related_type": None, "related_parent_id": None,
                    "related_bill_id": None,
                    "description": None, "tags": None,
                    "synced_at": datetime.now().isoformat(timespec="seconds"),
                    "sync_batch": f"batch_{d.isoformat()}",
                })
                sold_history.append({
                    "bill_id": bill_id, "date": d, "depot_id": s["id"],
                    "store_code": s["code"], "customer_id": cust,
                    "total": total, "emp": emp, "items": items,
                })

    df = pd.DataFrame(bills).sort_values("bill_datetime").reset_index(drop=True)
    return df, bills_per_day, sold_history


# ==============================================================================
# 7b. TIER LOOKUP — hạng thẻ tạm thời tại 1 thời điểm bất kỳ (dùng để chọn cửa
#     sổ đổi/trả trước khi engine điểm/hạng chính thức chạy) — hỗ trợ FIX #7
# ==============================================================================
TIER_THRESHOLDS = [
    (0, 5_000_000, "Member", 1),
    (5_000_000, 15_000_000, "Silver", 2),
    (15_000_000, 25_000_000, "Gold", 3),
    (25_000_000, 40_000_000, "Platinum", 5),
    (40_000_000, float("inf"), "Diamond", 8),
]


# [v3] Ưu đãi SINH NHẬT theo hạng (jm.com.vn): 1 hóa đơn/năm, tối đa 5 SP,
# trong đúng tháng sinh nhật, cần xác thực CCCD tại quầy.
BIRTHDAY_DISCOUNT_BY_TIER = {
    "Member": 0.15, "Silver": 0.18, "Gold": 0.20,
    "Platinum": 0.25, "Diamond": 0.30,
}
BIRTHDAY_MAX_ITEMS = 5

# [v3] Ưu đãi NÂNG HẠNG: khi khách vượt ngưỡng lên hạng mới, hóa đơn kế tiếp
# được giảm thêm một lần. Cơ chế nâng hạng: đạt đủ chi tiêu 12 tháng -> lên
# hạng ngay, không chờ kỳ xét định kỳ (Business Domain v2, mục 2.4).
TIER_UPGRADE_BONUS = {
    "Silver": 0.05, "Gold": 0.08, "Platinum": 0.10, "Diamond": 0.12,
}


def tier_for_spend(spend):
    for lo, hi, name, rate in TIER_THRESHOLDS:
        if lo <= spend < hi:
            return name, rate
    return "Diamond", 8


def orders_as_spend_events(df_orders, placeholder_ids):
    """[M5 — v3] KHÔNG còn đưa chi tiêu ONLINE vào tính hạng thẻ/điểm.

    Luôn trả về danh sách rỗng. Hàm được giữ lại (thay vì xoá) để chữ ký các
    hàm gọi nó không đổi và để lưu vết quyết định này ngay tại chỗ.

    LÝ DO (Business Domain v2, Chương 2 — [QUYẾT ĐỊNH] 05/09/2026):
      Toàn bộ chương trình thành viên (tích điểm, tiêu điểm, ưu đãi hạng, cửa
      sổ đổi trả theo hạng) CHỈ áp dụng cho khách mua tại 29 cửa hàng offline.
      Khách mua online là khách của SÀN — không tích điểm, không hưởng bất kỳ
      đãi ngộ hạng thành viên nào. Hai hệ chính sách hoàn toàn độc lập.

    LỊCH SỬ — vì sao đảo ngược so với v2.1:
      v2.1 (#16) từng chuyển sang tính hạng XUYÊN KÊNH để sửa lỗi "97,7% khách
      kẹt hạng Member, không có Platinum/Diamond". Cách sửa đó đúng về kỹ thuật
      nhưng SAI về nghiệp vụ. v3 quay lại chỉ-offline cho đúng chính sách thật.

    ⚠️ CẢNH BÁO TÁC ĐỘNG DÂY CHUYỀN (Generation Rules v2, mục 5.3):
      Việc quay lại chỉ-offline có nguy cơ làm TÁI PHÁT lỗi phân bố hạng thẻ.
      Bù lại bằng cách hiệu chỉnh quy mô khách offline (CONFIG["n_customers"])
      chứ KHÔNG bằng cách gộp lại doanh thu online. Xem qa_tier_distribution().
    """
    return []


def build_tier_lookup(*event_lists):
    """cust_id -> (sorted_dates_ordinal[], prefix_sum[]).

    Nhận nhiều nguồn sự kiện chi tiêu (offline sold_history + online orders) và
    gộp lại, để hạng thẻ phản ánh đúng chi tiêu XUYÊN KÊNH.
    """
    by_cust = {}
    for events in event_lists:
        for r in events:
            by_cust.setdefault(r["customer_id"], []).append((r["date"].toordinal(), r["total"]))
    lookup = {}
    for cid, lst in by_cust.items():
        lst.sort(key=lambda x: x[0])
        ords = [x[0] for x in lst]
        prefix = [0]
        for _o, amt in lst:
            prefix.append(prefix[-1] + amt)
        lookup[cid] = (ords, prefix)
    return lookup


def tier_as_of(lookup, cust_id, as_of_date):
    """Hạng thẻ theo tổng chi tiêu trailing 365 ngày TÍNH ĐẾN TRƯỚC as_of_date."""
    entry = lookup.get(cust_id)
    if not entry:
        return "Member", 1
    ords, prefix = entry
    hi_ord = as_of_date.toordinal()
    lo_ord = hi_ord - 365
    i_hi = bisect.bisect_left(ords, hi_ord)
    i_lo = bisect.bisect_left(ords, lo_ord)
    spend = prefix[i_hi] - prefix[i_lo]
    return tier_for_spend(spend)


# ==============================================================================
# 8. ĐỔI / TRẢ HÀNG OFFLINE  [FIX #6, #7]
# ==============================================================================
def gen_returns(stores, children, sold_history, tier_lookup, end, bill_ctr,
                 child_by_collection, df_emp):
    """GR-EXC.1: offline luôn là ĐỔI HÀNG (2 phiếu: 1 phiếu trả + 1 hóa đơn mua
    mới), KHÔNG có refund đơn lẻ. GR-EXC.6: cửa sổ 30 ngày (Platinum/Diamond)
    hoặc 7 ngày (Member/Silver/Gold), theo hạng thẻ tại thời điểm mua gốc."""
    # [FIX v2.1 #14] Bản trước để dict này RỖNG -> toàn bộ phiếu trả và hóa đơn
    # đổi có sale_user_id hợp lệ nhưng sale_user_name/created_user_name = NULL
    # (~43.000 dòng). QA cũ chỉ kiểm tra ID nên không phát hiện.
    emp_name_map = dict(zip(df_emp["emp_id"], df_emp["emp_name"]))
    n_returns = int(len(sold_history) * CONFIG["return_rate"])
    return_rows = []
    for src in random.sample(sold_history, k=n_returns):
        tier_name, _rate = tier_as_of(tier_lookup, src["customer_id"], src["date"])
        window = 30 if tier_name in ("Platinum", "Diamond") else 7
        gap = random.randint(1, window)
        rdate = src["date"] + timedelta(days=gap)
        if rdate > end:
            continue

        return_bill_id = bill_ctr.next()
        returned_value = src["total"]

        is_orphan = random.random() < CONFIG["orphan_return_rate"]
        rel_type = "0" if is_orphan else "6"
        rel_bill = None if is_orphan else str(src["bill_id"])

        ts = datetime.combine(rdate, datetime.min.time()) + timedelta(
            hours=random.randint(9, 21), minutes=random.randint(0, 59))

        # JM chỉ cho đổi sang SP giá >= SP cũ; số ít đổi xuống giá thì phần
        # chênh không hoàn khách mà tính vào payment_return_fee (GR-EXC.4).
        #
        # [FIX v2.1 #19] Bản trước bịa new_value bằng công thức rồi gắn thẳng vào
        # hóa đơn mới, trong khi cột products lại chứa một sản phẩm chọn ngẫu
        # nhiên có giá hoàn toàn khác -> payment_amount KHÔNG khớp tổng dòng sản
        # phẩm. Sai lệch này lan sang engine tiêu điểm (vốn tính lại
        # payment_amount từ products) và gây vi phạm cả GR-CUST.7 lẫn GR-OFF.4.
        # Nay làm ngược lại: CHỌN SẢN PHẨM có giá phù hợp với giá trị mục tiêu,
        # rồi suy new_value TỪ CHÍNH dòng sản phẩm đó.
        #
        # [FIX v2.2 #20] Lần vá trước ép quantity = target/giá, khiến hóa đơn đổi
        # có số lượng phi thực tế (trung bình 3, p95 = 9, cá biệt 58 sản phẩm/dòng)
        # trong khi hóa đơn bán thường tối đa chỉ 2. Nay giữ số lượng trong khoảng
        # 1-3 như hóa đơn thường và thay vào đó CHỌN sản phẩm có đơn giá gần mục
        # tiêu nhất — vừa đúng giá trị, vừa giống một giao dịch đổi hàng thật.
        if random.random() < 0.80:
            want_upgrade = True
            target_value = returned_value * np.random.uniform(1.0, 1.6)
        else:
            want_upgrade = False
            target_value = returned_value * np.random.uniform(0.6, 0.95)

        infl = price_inflation(rdate)
        cands = random.sample(children, k=min(60, len(children)))
        best, best_score = None, None
        for c in cands:
            price = int(round(c["retail"] * infl / 1000) * 1000)
            for qty in (1, 2, 3):
                value = price * qty
                # Khi đổi lên giá, ưu tiên phương án >= giá trị đơn cũ (GR-EXC.4)
                penalty = 0 if (not want_upgrade or value >= returned_value) else returned_value
                score = abs(value - target_value) + penalty
                if best_score is None or score < best_score:
                    best_score, best = score, (c, price, qty, value)

        c, price, qty, new_value = best
        new_items = [{
            "imexId": random.randint(10**6, 10**7),
            "id": c["id"], "code": c["code"], "barcode": None,
            "name": c["name"], "quantity": qty, "price": price,
            "discount": 0, "totalDiscount": 0, "amount": new_value,
        }]

        return_fee = max(0, returned_value - new_value)   # GR-EXC.3: MAX(0, cũ - mới)

        return_rows.append({
            "bill_id": str(return_bill_id), "bill_date": rdate.isoformat(),
            "bill_datetime": ts.isoformat(timespec="seconds"),
            "depot_id": src["depot_id"], "bill_type": "1", "bill_mode": "2",
            "order_id": None, "customer_id": src["customer_id"],
            "created_user_id": None, "created_user_name": emp_name_map.get(src["emp"]),
            "created_at": ts.isoformat(timespec="seconds"),
            "sale_user_id": src["emp"], "sale_user_name": emp_name_map.get(src["emp"]),
            "products": _clean_items(src["items"]),
            "payment_amount": returned_value, "payment_customer_amount": 0,
            "payment_discount": 0, "payment_points": 0,
            "payment_used_points_value": 0, "payment_used_points_amount": 0,
            "payment_transfer_amount": 0, "payment_cash_amount": 0,
            "payment_credit_amount": 0,
            "payment_coupon_value": 0, "payment_coupon_amount": 0,
            "payment_return_fee": return_fee, "payment_return_amount": 0,   # GR-EXC.1: offline không có return_amount đơn lẻ
            "related_type": rel_type, "related_parent_id": None,
            "related_bill_id": rel_bill,
            "description": None, "tags": None,
            "synced_at": datetime.now().isoformat(timespec="seconds"),
            "sync_batch": f"batch_{rdate.isoformat()}",
        })

        # Hóa đơn mua mới đi kèm — GR-EXC.1 bắt buộc luôn có, không điều kiện.
        # new_items/new_value đã được dựng ở trên và LUÔN khớp nhau.
        new_bill_id = bill_ctr.next()
        return_rows.append({
            "bill_id": str(new_bill_id), "bill_date": rdate.isoformat(),
            "bill_datetime": ts.isoformat(timespec="seconds"),
            "depot_id": src["depot_id"], "bill_type": "2", "bill_mode": "2",
            "order_id": None, "customer_id": src["customer_id"],
            "created_user_id": None, "created_user_name": emp_name_map.get(src["emp"]),
            "created_at": ts.isoformat(timespec="seconds"),
            "sale_user_id": src["emp"], "sale_user_name": emp_name_map.get(src["emp"]),
            "products": _clean_items(new_items),
            "payment_amount": new_value, "payment_customer_amount": new_value,
            "payment_discount": 0, "payment_points": 0,
            "payment_used_points_value": 0, "payment_used_points_amount": 0,
            # [FIX v2.1 #15] Bản trước: transfer = new_value chỉ 50% số lần, còn
            # cash/credit luôn = 0 -> một nửa số hóa đơn đổi có tổng phương thức
            # thanh toán = 0 trong khi payment_amount > 0, vi phạm GR-OFF.4
            # ("tổng các phương thức = payment_amount"). Nay phân bổ đủ 100%
            # giá trị vào đúng một phương thức, theo cùng cơ cấu hóa đơn thường.
            **_split_payment(new_value),
            "payment_coupon_value": 0, "payment_coupon_amount": 0,
            "payment_return_fee": 0, "payment_return_amount": 0,
            "related_type": None, "related_parent_id": str(return_bill_id),
            "related_bill_id": None,
            "description": None, "tags": None,
            "synced_at": datetime.now().isoformat(timespec="seconds"),
            "sync_batch": f"batch_{rdate.isoformat()}",
        })
    return pd.DataFrame(return_rows)


# ==============================================================================
# 9. ORDER_DATA.orders_raw — ĐƠN HÀNG ONLINE  [FIX #8]
# ==============================================================================
CARRIERS = [(2,"Viettel Post"),(5,"Giaohangnhanh"),(8,"Giao hàng tiết kiệm"),
            (24,"JT Express"),(29,"SPX Express"),(27,"Ninja Van"),(12,"Tự Vận Chuyển")]
CHANNELS = [(1,"admin"),(2,"Website"),(20,"Facebook"),(21,"JM - INSTAGRAM"),
            (41,"Laz"),(42,"Shopee"),(48,"Tiktok")]
CHANNEL_W = [0.10, 0.08, 0.22, 0.07, 0.08, 0.20, 0.25]
TRAFFIC_SRC = ["Facebook","JM (livestream)","JM - INSTAGRAM","KH điểm bán","KOL, KOC",
               "Khác","Laz","Nguồn CSKH","Shopee","Tiktok","Website","Đối tác, người quen"]

# ------------------------------------------------------------------------------
# [M6 — v3] TẬP NHÃN CHỮ CHUẨN — gán NGAY từ generator, KHÔNG remap downstream.
#
# v2 xuất 4 cột này dạng INT rồi phải chạy CREATE OR REPLACE TABLE trên BigQuery
# để map sang chữ. Mỗi lần reload orders_raw với autodetect=True, BigQuery lại
# revert về INT64 -> phải nhớ chạy lại SQL mapping, rất dễ quên và làm gãy các
# view phụ thuộc. v3 sinh thẳng nhãn chữ nên lỗi này không thể tái phát.
#
# LƯU Ý CÓ CHỦ ĐÍCH: hệ thống Nhanh.vn thật lưu các trường này dạng INT
# (apidocs.nhanh.vn v3). Đây là quyết định ưu tiên tính khả dụng phân tích hơn
# tính trung thực tuyệt đối với API — đã ghi rõ ở Generation Rules v2, Rule M6.
# ------------------------------------------------------------------------------
STATUS_LABELS = {
    40: "Đã đóng gói",        42: "Đang đóng gói",     43: "Chờ thu gom",
    54: "Đơn mới",            55: "Đang xác nhận",     56: "Đã xác nhận",
    57: "Chờ khách xác nhận", 58: "NVC hủy đơn",       59: "Đang chuyển",
    60: "Thành công",         61: "Thất bại",          63: "Khách hủy",
    64: "Hệ thống hủy",       68: "Hết hàng",          71: "Đang chuyển hoàn",
    72: "Đã chuyển hoàn",     74: "Xác nhận hoàn",
}
ORDER_TYPE_LABELS = {
    1:  "Giao hàng tận nhà",   # orders_raw (online)
    2:  "Mua tại quầy",        # CHỈ bills_raw (offline)
    12: "Đổi sản phẩm",        # CHỈ bills_raw (offline) — không có đổi hàng online
    14: "Khách trả lại hàng",  # cả 2 luồng
}
SALE_CHANNEL_LABELS = {
    1: "Admin", 2: "Website", 20: "Facebook", 21: "Instagram",
    41: "Lazada", 42: "Shopee", 48: "TikTok Shop",
}

STATUS_POOL      = [60, 63, 64, 72, 74, 71, 68, 61]
STATUS_W_DEFAULT = [0.78, 0.06, 0.02, 0.06, 0.04, 0.02, 0.01, 0.01]
# [SỬA v3] GR-ONL.3 của v2 ghi SHOPEE có tỉ lệ hoàn/hủy cao nhất — MÂU THUẪN với
# số đã khoá ở QA checklist (TikTok ~24,3% cao nhất hệ thống, Shopee ~11,6%).
# Vòng audit 05/09/2026 đã chốt giữ số QA-locked (có corroboration gián tiếp từ
# ngành: thời trang trên TikTok Shop/livestream tỉ lệ hoàn 20-30%).
# => Đảo lại: TikTok mang bộ trọng số hoàn/hủy cao, Shopee về mức trung bình.
STATUS_W_TIKTOK  = [0.62, 0.08, 0.02, 0.13, 0.08, 0.04, 0.02, 0.01]
CANCEL_REASONS   = [1,2,3,4,5,6,9,11,12,14,16,18,19,23,24,26]
# [v3] Bộ mã LÝ DO TRẢ HÀNG — dùng chính cột `reason` có sẵn trong schema
# (không thêm cột mới). Trọng số theo đặc trưng ngành thời trang:
# sai size 65% / không như mô tả 15% / lỗi SP 10% / giao nhầm 5% / thất lạc 5%.
RETURN_REASONS   = [31, 32, 33, 34, 35]
RETURN_REASON_W  = [0.65, 0.15, 0.10, 0.05, 0.05]
RETURN_REASON_LABELS = {
    31: "Sai size", 32: "Không như mô tả", 33: "Lỗi sản phẩm",
    34: "Giao nhầm", 35: "Thất lạc vận chuyển",
}
# Tình trạng hàng hoàn KHÔNG lưu ở orders_raw — đó là sự kiện KHO, thuộc về
# nhanh_bills_full (phiếu nhập trả hàng), ghi ở cột `description` có sẵn.
RETURN_CONDITIONS = ["Restockable", "Damaged", "Lost"]
RETURN_COND_W     = [0.85, 0.10, 0.05]


# ==============================================================================
# [v3] BIỂU PHÍ SÀN THEO TIMELINE THẬT
# ==============================================================================
# Bản cũ gộp tất cả vào MỘT dòng: ecom_fee = total * uniform(5%, 12%) — không
# phân biệt sàn, không phân biệt loại phí, không có mốc thời gian, và không xử
# lý chuyện phí nào được hoàn khi khách trả hàng. Hệ quả: mọi phân tích biên
# lợi nhuận theo sàn/theo thời gian đều chỉ đọc ra nhiễu ngẫu nhiên.
#
# Cấu trúc: (effective_from, effective_to, rate_hoặc_số_tiền, refundable)
#   - rate < 1  -> tính theo % giá trị đơn
#   - rate >= 1 -> số tiền cố định trên đơn (VNĐ)
#   - refundable = phí có được hoàn lại khi đơn bị trả hay không
# Nguồn: seller center từng sàn, đối chiếu vòng audit 05-06/09/2026.
FAR = date(2099, 12, 31)
PLATFORM_FEES = {
    "Shopee": [
        # Transaction Fee ~4,91% (từ 01/07/2025) -> 6% (từ 01/05/2026)  [XÁC NHẬN]
        ("transaction", date(2024, 1, 1), date(2025, 6, 30), 0.0400, False),
        ("transaction", date(2025, 7, 1), date(2026, 4, 30), 0.0491, False),
        ("transaction", date(2026, 5, 1), FAR,               0.0600, False),
        # Phí hoa hồng nền tảng cho shop thường  [SUY LUẬN]
        ("commission",  date(2024, 1, 1), FAR,               0.0300, True),
    ],
    "TikTok Shop": [
        # Transaction Fee 5% -> 6% (từ 09/05/2026)  [XÁC NHẬN]
        ("transaction", date(2024, 1, 1), date(2026, 5, 8),  0.0500, False),
        ("transaction", date(2026, 5, 9), FAR,               0.0600, False),
        # Commission: 12,5% Marketplace từ 09/05/2026  [XÁC NHẬN]
        ("commission",  date(2024, 1, 1), date(2026, 5, 8),  0.0800, True),
        ("commission",  date(2026, 5, 9), FAR,               0.1250, True),
        # Phí xử lý đơn 3.000đ/đơn từ 27/10/2025, KHÔNG hoàn  [XÁC NHẬN]
        ("handling",    date(2025, 10, 27), FAR,             3_000,  False),
    ],
    "Lazada": [
        # Phí thanh toán ~3,99-4,02%, không hoàn  [XÁC NHẬN]
        ("payment",     date(2024, 1, 1), FAR,               0.0400, False),
        # Phí cố định ~3,993% non-Mall, ĐƯỢC hoàn khi trả hàng  [XÁC NHẬN]
        ("commission",  date(2024, 1, 1), FAR,               0.0399, True),
        # Phí hạ tầng 1.000-3.000đ/đơn, không hoàn  [XÁC NHẬN]
        ("handling",    date(2024, 1, 1), FAR,               2_000,  False),
    ],
    # Facebook/Instagram/Website/Admin: JM tự vận hành, không có phí sàn.
}


def platform_fee(channel, d, order_value, returned=False):
    """Tổng phí sàn của một đơn tại ngày `d`.

    `returned=True` -> chỉ giữ lại các khoản KHÔNG được hoàn. Đây là điểm mấu
    chốt về biên lợi nhuận: đơn bị trả vẫn phải chịu transaction fee/phí xử lý
    đơn, nên doanh thu = 0 nhưng chi phí > 0.
    """
    total = 0
    for _kind, f, t, rate, refundable in PLATFORM_FEES.get(channel, []):
        if not (f <= d <= t):
            continue
        if returned and refundable:
            continue
        total += int(order_value * rate) if rate < 1 else int(rate)
    return total


def gen_orders(stores, children, df_cust, start, end, target_by_year, order_ctr,
               child_by_collection, picker):
    """target_by_year: dict năm -> số đơn online cần sinh trong đúng năm đó
    (đã tính bằng target tổng năm trừ offline ước tính — FIX #10)."""
    rows = []
    # [M3 — v3] Không lấy danh sách placeholder ở đây nữa: đơn ONLINE không bao
    # giờ được gán khách placeholder (xem chú thích tại customer_id bên dưới).
    shops = [s for s in stores if not s["is_warehouse"]]

    days_by_year = {}
    for d in daterange(start, end):
        days_by_year.setdefault(d.year, []).append(d)

    per_day_plan = {}
    for y, days_y in days_by_year.items():
        n_target = int(target_by_year.get(y, 0))
        if n_target <= 0 or not days_y:
            continue
        weights = np.array([seasonality_factor(d) for d in days_y])
        weights = weights / weights.sum()
        per_day = np.random.multinomial(n_target, weights)
        for d, n in zip(days_y, per_day):
            per_day_plan[d] = int(n)

    for d, n in per_day_plan.items():
        for _ in range(n):
            order_id = order_ctr.next()
            ch_id, ch_name = random.choices(CHANNELS, weights=CHANNEL_W)[0]
            is_tiktok = (ch_id == 48)
            status = random.choices(STATUS_POOL,
                                    weights=STATUS_W_TIKTOK if is_tiktok else STATUS_W_DEFAULT)[0]
            items = pick_products_for_bill(
                children, n_items=random.choices([1,2,3], weights=[.68,.24,.08])[0], d=d,
                child_by_collection=child_by_collection)
            total = sum(i["amount"] for i in items)
            cid, cname = random.choice(CARRIERS)
            ship_fee = random.choice([0, 20_000, 25_000, 30_000, 35_000])
            created = datetime.combine(d, datetime.min.time()) + timedelta(
                hours=random.randint(8, 23), minutes=random.randint(0, 59))
            confirmed = created + timedelta(hours=random.randint(1, 20))
            packed = confirmed + timedelta(hours=random.randint(1, 24))
            sent = packed + timedelta(hours=random.randint(1, 12))
            delivered = sent + timedelta(days=random.randint(1, 5))

            # [M1 — v3] BỎ HOÀN TOÀN luồng bán buôn. JM không có chính sách/chương
            # trình B2B nào. Ở v2, 2% đơn bị gán is_wholesale (20-200 SP/đơn,
            # giá -30%) do hiểu nhầm định nghĩa field order_mode của Nhanh.vn
            # API — đây là ARTIFACT sinh dữ liệu, không phải nghiệp vụ thật.
            # Cột order_mode cũng bị bỏ khỏi schema (xem rows.append bên dưới).

            rows.append({
                # [M6] Nhãn chữ ngay từ generator (không remap ở BigQuery nữa)
                "order_id": str(order_id),
                "order_type": ORDER_TYPE_LABELS[1],
                "depot_id": random.choice(shops)["id"],
                "status": STATUS_LABELS[status],
                "reason": random.choice(CANCEL_REASONS) if status in (63, 64) else 0,
                "order_index": random.randint(1, 500),
                "created_at": created.isoformat(timespec="seconds"),
                "updated_at": (delivered + timedelta(days=1)).isoformat(timespec="seconds"),
                "confirmed_at": confirmed.isoformat(timespec="seconds"),
                "packed_at": packed.isoformat(timespec="seconds"),
                "sale_channel": SALE_CHANNEL_LABELS[ch_id],
                "traffic_source": random.choice(TRAFFIC_SRC),
                "app_order_id": f"{ch_name[:3].upper()}{random.randint(10**9,10**10)}" if ch_id in (41,42,48) else None,
                "shop_name": ch_name if ch_id in (41,42,48) else None,
                "fb_ads_id": random.randint(10**14,10**15) if ch_id in (20,21) else None,
                "fb_psid": random.randint(10**14,10**15) if ch_id in (20,21) else None,
                # Cùng picker với offline -> một khách trung thành sẽ mua nhiều
                # ở CẢ hai kênh, đúng bản chất omnichannel (GR-CUST.1).
                # [M3 — v3] KHÔNG BAO GIỜ gán placeholder cho đơn ONLINE.
                # v2 gán 3% đơn online cho khách placeholder (id 1/2/3) — đây là
                # lỗi tái dụng cơ chế của offline sang online mà không xét bản
                # chất nguồn dữ liệu. Dữ liệu online được KÉO VỀ từ API sàn, mà
                # sàn LUÔN trả buyer ID cho mọi đơn, nên không thể tồn tại đơn
                # online "không xác định được khách". Placeholder chỉ có ở quầy
                # offline (khách không đọc SĐT). Business Domain v2, Chương 6.3.
                "customer_id": picker.pick(),
                "city_id": random.randint(1, 63),
                "carrier_id": cid, "carrier_name": cname,
                "carrier_code": f"{cname[:2].upper()}{random.randint(10**9,10**10)}",
                "carrier_service_type": random.choice([0,5,10,15,16]),
                "check_goods": random.choice([0,1,2,3,4]),
                "is_part_delivery": 0, "is_declared_fee": random.choice([0,1]),
                "send_carrier_at": sent.isoformat(timespec="seconds") if status not in (63,) else None,
                "delivery_at": delivered.isoformat(timespec="seconds") if status == 60 else None,
                "ship_fee": ship_fee,
                "cod_fee": int(total * 0.01) if status == 60 else 0,
                # [v3] Phí sàn tra theo biểu phí có hiệu lực tại ngày đặt đơn.
                # Đơn bị hoàn/hủy vẫn chịu các khoản không hoàn (xem platform_fee).
                "ecom_fee": platform_fee(SALE_CHANNEL_LABELS[ch_id], d, total,
                                         returned=(status != 60)),
                "return_fee": random.choice([0, 15_000, 20_000]) if status in (71,72,74) else 0,
                "customer_ship_fee": ship_fee,
                "carrier_payment_status": 0 if status == 60 else 2,
                "vat_amount": 0,
                "discount_amount": sum(i["discount"] for i in items),
                "cod_amount": total + ship_fee if status == 60 else 0,
                "business_payment": int(total * 0.92) if status == 60 else 0,
                "business_payment_status": 99 if status == 60 else 0,
                "products": _clean_items(items),
                "synced_at": datetime.now().isoformat(timespec="seconds"),
                "sync_batch": f"batch_{d.isoformat()}",
            })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # ==========================================================================
    # [M4 — v3] ĐƠN TRẢ ONLINE (order_type=14) — VIẾT LẠI HOÀN TOÀN
    # ==========================================================================
    # BUG CỦA v2 (đã xác nhận qua BigQuery, gây overstate doanh thu online ~5%):
    #   Bản cũ tạo bản ghi trả hàng với order_id MỚI, cod_amount=0, KHÔNG liên
    #   kết ngược về đơn gốc và KHÔNG trừ tiền khỏi đơn gốc. Kết quả: bản ghi
    #   trả hàng trở thành "marker mồ côi" — SUM(cod_amount) toàn hệ thống không
    #   hề giảm khi có return, nên mọi phân tích doanh thu online đều bị thổi lên.
    #
    # LOGIC ĐÚNG (Generation Rules v2, Chương 7):
    #   1. Chọn đơn status="Thành công" theo tỉ lệ return của từng kênh
    #   2. Bản ghi trả mang CÙNG order_id đơn gốc + original_order_id trỏ về gốc
    #   3. ~95% full refund / ~5% partial refund (xem công thức bên dưới)
    #   4. Full refund: ZERO HOÁ cod_amount/business_payment của ĐƠN GỐC
    #   5. Partial refund: TRỪ đúng giá trị SP bị hoàn khỏi đơn gốc
    #   6. Ngày trả = ngày giao thành công + 3..10 ngày (độ trễ vật lý)
    #   7. Gán return_condition_status: 85% Restockable/10% Damaged/5% Lost
    #
    # Vì sao ~95% full refund là ĐÚNG chứ không phải con số tuỳ tiện:
    #   68% đơn chỉ có 1 sản phẩm  -> buộc phải full refund
    #   32% đơn nhiều SP           -> 85% trong số đó khách trả hết
    #   => 0.68*1.0 + 0.32*0.85 = 0.952
    # ==========================================================================
    RETURN_RATE_BY_CHANNEL = {
        "TikTok Shop": 0.243,   # cao nhất hệ thống (số QA-locked)
        "Shopee":      0.116,
        "Lazada":      0.100,   # [SUY LUẬN] chưa có số riêng, dùng mức trung bình
        "Website":     0.080,
        "Facebook":    0.080,
        "Instagram":   0.080,
        "Admin":       0.010,   # đơn lên tay tại quầy — hành vi giống offline
    }
    MULTI_ITEM_FULL_REFUND_PROB = 0.85

    success_idx = df.index[df["status"] == STATUS_LABELS[60]].tolist()

    ret_rows = []
    return_events = []      # chuyển sang gen_nhanh_bills_full để sinh phiếu nhập kho
    for idx in success_idx:
        o = df.loc[idx]
        if random.random() >= RETURN_RATE_BY_CHANNEL.get(o["sale_channel"], 0.08):
            continue

        rdate = (datetime.fromisoformat(o["created_at"])
                 + timedelta(days=random.randint(3, 10)))
        if rdate.date() > end:
            continue

        items = o["products"] if isinstance(o["products"], list) else []
        if not items:
            continue

        # --- Full vs partial refund ------------------------------------------
        # 68% đơn chỉ có 1 SP -> buộc full refund; đơn nhiều SP thì 85% trả hết.
        # => tỉ lệ full refund kỳ vọng = 0.68*1.0 + 0.32*0.85 ≈ 0.952
        is_full = True if len(items) == 1 else (random.random() < MULTI_ITEM_FULL_REFUND_PROB)
        returned_items = [dict(i) for i in items] if is_full else [dict(random.choice(items))]
        refund_amount = sum(i["amount"] for i in returned_items)

        # --- TRỪ THỰC SỰ khỏi ĐƠN GỐC (điểm đã sai ở v2) ---------------------
        if is_full:
            df.at[idx, "cod_amount"] = 0
            df.at[idx, "business_payment"] = 0
        else:
            df.at[idx, "cod_amount"] = max(0, int((o["cod_amount"] or 0) - refund_amount))
            df.at[idx, "business_payment"] = max(0, int((o["business_payment"] or 0) - refund_amount))

        reason_code = random.choices(RETURN_REASONS, weights=RETURN_REASON_W)[0]
        condition = random.choices(RETURN_CONDITIONS, weights=RETURN_COND_W)[0]

        # --- Dòng trả hàng: CHỈ dùng cột có sẵn trong schema ------------------
        r = o.to_dict()
        r.update({
            # Liên kết về đơn gốc bằng chính order_id (dùng chung id) — không
            # cần cột original_order_id. Phân biệt 2 dòng bằng order_type.
            "order_id":     o["order_id"],
            "order_type":   ORDER_TYPE_LABELS[14],
            "status":       STATUS_LABELS[60],   # đơn gốc vẫn "Thành công" (KB3/KB4)
            "reason":       reason_code,          # dùng cột `reason` có sẵn
            "created_at":   rdate.isoformat(timespec="seconds"),
            "updated_at":   rdate.isoformat(timespec="seconds"),
            "confirmed_at": rdate.isoformat(timespec="seconds"),
            "delivery_at":  rdate.isoformat(timespec="seconds"),
            # Giá trị ÂM để SUM toàn bảng tự đối trừ. is_full/refund_amount suy
            # ra được từ đây nên không cần cột riêng.
            "cod_amount":       -int(refund_amount),
            "business_payment": -int(refund_amount),
            "business_payment_status": 0,
            "products":     _clean_items(returned_items),
            "sync_batch":   f"batch_{rdate.date().isoformat()}",
        })
        ret_rows.append(r)

        # Tình trạng hàng hoàn -> sự kiện KHO, sinh phiếu nhập ở nhanh_bills_full.
        # Hàng "Lost" KHÔNG sinh phiếu nhập (không có gì về kho để nhập).
        return_events.append({
            "order_id":  o["order_id"],
            "depot_id":  o["depot_id"],
            "date":      rdate.date(),
            "condition": condition,
            "products":  _clean_items(returned_items),
            "amount":    int(refund_amount),
        })

    if ret_rows:
        df = pd.concat([df, pd.DataFrame(ret_rows)], ignore_index=True)

    df = df.sort_values("created_at").reset_index(drop=True)
    df.attrs["return_events"] = return_events   # đọc lại ở gen_nhanh_bills_full
    return df



# ==============================================================================
# 10. BILL_DATA.nhanh_bills_full — PHIẾU XUẤT/NHẬP KHO
# ==============================================================================
def gen_nhanh_bills_full(df_bills, stores, start, end, n_transfer=None,
                         return_events=None, receipt_docs=None):
    rows = []
    xnk_id = 8_000_000
    for _, b in df_bills.iterrows():
        xnk_id += 1
        rows.append({
            "id": xnk_id, "orderId": 0, "depotId": b["depot_id"], "date": b["bill_date"],
            "type": 2 if b["bill_type"] == "2" else 1, "mode": 2, "description": None,
            "customerId": b["customer_id"], "customerName": None, "customerMobile": None,
            "createdById": None, "createdByName": b["created_user_name"],
            "createdAt": b["created_at"],
            "saleId": b["sale_user_id"], "saleName": b["sale_user_name"],
            "supplierId": None, "supplierName": None,
            "paymentAmount": b["payment_amount"], "paymentDiscount": b["payment_discount"],
            "paymentTransferAmount": b["payment_transfer_amount"],
            "paymentCashAmount": b["payment_cash_amount"],
            "paymentCouponCode": None, "paymentCouponAmount": 0,
            "products": b["products"],
            "_loaded_at": datetime.now().isoformat(timespec="seconds"),
            "_batch_id": b["sync_batch"],
        })
    # ==========================================================================
    # [v3] PHIẾU NHẬP TRẢ HÀNG ONLINE — hàng hoàn từ sàn về kho
    # ==========================================================================
    # Tình trạng hàng hoàn (Restockable/Damaged/Lost) là SỰ KIỆN KHO nên thuộc
    # về bảng này, không phải orders_raw. Ghi vào cột `description` có sẵn,
    # link về đơn gốc qua cột `orderId` có sẵn — KHÔNG thêm cột mới.
    #
    #   Restockable (85%) -> nhập kho, tăng tồn khả dụng
    #   Damaged     (10%) -> nhập kho lỗi, tăng tồn thực tế nhưng KHÔNG khả dụng
    #   Lost         (5%) -> KHÔNG sinh phiếu nhập (hàng thất lạc, không về kho)
    for ev in (return_events or []):
        if ev["condition"] == "Lost":
            continue      # không có hàng về kho -> không có phiếu nhập
        xnk_id += 1
        rows.append({
            "id": xnk_id, "orderId": ev["order_id"], "depotId": ev["depot_id"],
            "date": ev["date"].isoformat(),
            "type": 1,          # 1 = phiếu NHẬP (hàng về kho)
            "mode": 2,
            "description": f"Nhập trả hàng online - {ev['condition']}",
            "customerId": None, "customerName": None, "customerMobile": None,
            "createdById": None, "createdByName": None,
            "createdAt": f"{ev['date'].isoformat()}T10:00:00",
            "saleId": None, "saleName": None,
            "supplierId": None, "supplierName": None,
            "paymentAmount": -ev["amount"],   # giá trị âm: giảm trừ doanh thu
            "paymentDiscount": 0,
            "paymentTransferAmount": 0, "paymentCashAmount": 0,
            "paymentCouponCode": None, "paymentCouponAmount": 0,
            "products": ev["products"],
            "_loaded_at": datetime.now().isoformat(timespec="seconds"),
            "_batch_id": f"batch_{ev['date'].isoformat()}",
        })

    shops = [s for s in stores if not s["is_warehouse"]]
    whs = [s for s in stores if s["is_warehouse"]]
    # ==================================================================
    # [v3] PHIẾU CHUYỂN KHO + NHẬP KHO — nay lấy từ SỔ CÁI TỒN KHO THẬT
    # ==================================================================
    # Bản cũ rải ngẫu nhiên ~18% x số hóa đơn phiếu chuyển kho với
    # `products = None` — tức chứng từ RỖNG, không nói gì về hàng hóa, và
    # không liên quan gì tới tồn kho. Nay mỗi đợt nhập bổ sung mà engine tồn
    # kho tính ra sẽ sinh đúng 1 cặp chứng từ chuyển kho (xuất ở kho tổng /
    # nhập ở cửa hàng) kèm ĐẦY ĐỦ dòng sản phẩm, nên daily_snapshot và
    # nhanh_bills_full khớp nhau.
    if receipt_docs:
        wh_src = [w for w in whs if w["code"] != "WH_LOI"] or whs
        supplier_lines = {}
        for doc in receipt_docs:
            d = doc["date"]
            src = random.choice(wh_src)
            val = sum(pr["amount"] for pr in doc["products"])
            for t, dep in ((2, src["id"]), (1, doc["depot_id"])):
                xnk_id += 1
                rows.append({
                    "id": xnk_id, "orderId": 0, "depotId": dep,
                    "date": d.isoformat(), "type": t, "mode": 3,
                    "description": None,
                    "customerId": None, "customerName": None, "customerMobile": None,
                    "createdById": None, "createdByName": None,
                    "createdAt": f"{d.isoformat()}T09:00:00",
                    "saleId": None, "saleName": None,
                    "supplierId": None, "supplierName": None,
                    "paymentAmount": int(val), "paymentDiscount": 0,
                    "paymentTransferAmount": 0, "paymentCashAmount": 0,
                    "paymentCouponCode": None, "paymentCouponAmount": 0,
                    "products": doc["products"],
                    "_loaded_at": datetime.now().isoformat(timespec="seconds"),
                    "_batch_id": f"batch_{d.isoformat()}",
                })
            # hàng phải vào kho tổng trước khi chuyển đi -> gom phiếu nhập NCC
            key = (src["id"], d)
            supplier_lines.setdefault(key, []).extend(doc["products"])

        # phiếu nhập từ nhà cung cấp: gom theo (kho tổng, ngày), cắt 100 dòng/phiếu
        for (dep, d), lines in sorted(supplier_lines.items()):
            for i in range(0, len(lines), 100):
                chunk = lines[i:i + 100]
                sup = random.randint(1, 20)
                xnk_id += 1
                rows.append({
                    "id": xnk_id, "orderId": 0, "depotId": dep,
                    "date": d.isoformat(), "type": 1, "mode": 5,
                    "description": None,
                    "customerId": None, "customerName": None, "customerMobile": None,
                    "createdById": None, "createdByName": None,
                    "createdAt": f"{d.isoformat()}T08:00:00",
                    "saleId": None, "saleName": None,
                    "supplierId": sup, "supplierName": f"NCC {sup}",
                    "paymentAmount": int(sum(pr["amount"] for pr in chunk)),
                    "paymentDiscount": 0, "paymentTransferAmount": 0,
                    "paymentCashAmount": 0, "paymentCouponCode": None,
                    "paymentCouponAmount": 0, "products": chunk,
                    "_loaded_at": datetime.now().isoformat(timespec="seconds"),
                    "_batch_id": f"batch_{d.isoformat()}",
                })
    return pd.DataFrame(rows)


# ==============================================================================
# 11. PALEXY_DATA — traffic camera AI (không đổi so với bản cũ — đã đúng)
# ==============================================================================
def gen_palexy(stores, start, end, bills_per_day_map):
    daily_rows, hourly_rows = [], []
    open_hours = list(range(9, 22))
    hour_weight = np.array([0.4,0.5,0.7,0.9,1.0,0.8,0.7,0.9,1.2,1.4,1.5,1.2,0.6])
    hour_weight = hour_weight / hour_weight.sum()

    for s in stores:
        if s["is_warehouse"]:
            continue
        for d in daterange(start, end):
            n_bills = bills_per_day_map.get((s["code"], d), 0)
            if n_bills == 0:
                continue
            cr = np.random.uniform(0.08, 0.18)
            unique_visits = int(n_bills / cr)
            daily_rows.append({
                "snapshot_date": d.isoformat(),
                "snapshot_timestamp": f"{d.isoformat()}T23:50:00",
                "store_id": str(s["id"]), "store_code": s["code"],
                "store_name": s["name"], "unique_visits": unique_visits,
                "loaded_at": f"{d.isoformat()}T23:55:00",
            })
            inflate = np.random.uniform(1.15, 1.38)
            total_hourly = int(unique_visits * inflate)
            alloc = np.random.multinomial(total_hourly, hour_weight)
            for h, v in zip(open_hours, alloc):
                hourly_rows.append({
                    "snapshot_date": d.isoformat(), "snapshot_hour": h,
                    "snapshot_timestamp": f"{d.isoformat()}T{h:02d}:59:00",
                    "store_id": str(s["id"]), "store_code": s["code"],
                    "store_name": s["name"], "visits": int(v),
                    "loaded_at": f"{d.isoformat()}T23:55:00",
                })
    df_map = pd.DataFrame([{
        "palexy_store_name": f"{s['name']} (Palexy)",
        "correct_store_code": s["code"], "correct_store_name": s["name"],
    } for s in stores if not s["is_warehouse"]])
    return pd.DataFrame(daily_rows), pd.DataFrame(hourly_rows), df_map


# ==============================================================================
# 12. INVENTORY_DATA — snapshot tồn kho (không đổi so với bản cũ)
# ==============================================================================
def _movement_ledger(df_bills, df_orders, return_events, wh_loi_id=None):
    """Dựng sổ cái chuyển động tồn kho từ dữ liệu bán ĐÃ SINH.

    Trả về dict (depot_id, sku_code) -> {date_ordinal: delta}, phủ TOÀN BỘ cặp
    (kho, SKU) có phát sinh — không giới hạn ở panel snapshot, vì sổ cái này
    còn là nguồn sinh phiếu nhập kho/chuyển kho trong nhanh_bills_full.

    Quy ước dấu:
      - bills_raw type=2 (bán tại quầy)       : XUẤT (-)
      - bills_raw type=1 (phiếu trả offline)  : NHẬP (+)
      - orders_raw đã đóng gói trở đi         : XUẤT (-)
      - đơn hoàn về trước khi giao (KB1/KB2)  : NHẬP (+) nguyên lô
      - return_events (KB3/KB4, sau khi giao) : NHẬP (+) đúng SL thực trả;
        Damaged đẩy sang kho lỗi, Lost không nhập đâu cả
    """
    mv = {}

    def add(dep, code, d_ord, delta):
        k = (dep, code)
        d = mv.get(k)
        if d is None:
            d = mv[k] = {}
        d[d_ord] = d.get(d_ord, 0) + delta

    # ---- offline ----
    for dep, btype, bdate, items in zip(df_bills["depot_id"], df_bills["bill_type"],
                                        df_bills["bill_date"], df_bills["products"]):
        if not isinstance(items, list):
            continue
        sign = -1 if btype == "2" else 1
        o = date.fromisoformat(bdate).toordinal()
        for it in items:
            add(dep, it["code"], o, sign * it["quantity"])

    # ---- online ----
    # Đơn chưa từng rời kho thì không đụng tồn.
    NEVER_LEFT = {STATUS_LABELS[63], STATUS_LABELS[64], STATUS_LABELS[68]}
    # Hoàn về kho TRƯỚC khi khách nhận (KB1/KB2) -> nguyên lô quay lại.
    CAME_BACK = {STATUS_LABELS[71], STATUS_LABELS[72], STATUS_LABELS[74],
                 STATUS_LABELS[61], STATUS_LABELS[58]}
    if df_orders is not None and not df_orders.empty:
        for dep, otype, status, cat, items in zip(
                df_orders["depot_id"], df_orders["order_type"], df_orders["status"],
                df_orders["created_at"], df_orders["products"]):
            if otype == ORDER_TYPE_LABELS[14] or not isinstance(items, list):
                continue          # dòng hoàn xử lý riêng qua return_events
            if status in NEVER_LEFT:
                continue
            o = date.fromisoformat(cat[:10]).toordinal()
            for it in items:
                add(dep, it["code"], o, -it["quantity"])
            if status in CAME_BACK:
                for it in items:      # về kho sau ~5 ngày vận chuyển ngược
                    add(dep, it["code"], o + 5, it["quantity"])

    # ---- hoàn sau khi giao (KB3/KB4) ----
    for ev in (return_events or []):
        cond = ev.get("condition")
        if cond == "Lost":
            continue              # mất hàng: không có gì về kho
        o = ev["date"].toordinal() if hasattr(ev["date"], "toordinal") \
            else date.fromisoformat(str(ev["date"])[:10]).toordinal()
        # Damaged: về kho LỖI, không về cửa hàng (tăng tồn thực, không khả dụng)
        dep = ev["depot_id"] if cond == "Restockable" else (wh_loi_id or ev["depot_id"])
        for it in ev["products"]:
            add(dep, it["code"], o, it["quantity"])
    return mv


def gen_inventory(children, stores, start, end, freq_days, df_bills=None,
                  df_orders=None, return_events=None, sku_sample=400,
                  replen_days=30, lot_size=2):
    """[v3 — VIẾT LẠI] Engine tồn kho reconcile được (GR-INV.9).

    HIỆU CHỈNH lot_size (v3.1) — đo bằng jm_inv_diagnostic.py trên bộ dữ liệu
    thật, mô phỏng đã kiểm chứng tái tạo đúng số thật (lệch 0%):
        lot=6 -> 0,82 vòng/năm | lot=4 -> 1,27 | lot=3 -> 1,68
        lot=2 -> 2,49          | lot=1 -> 4,45 (loại: 50,2% hết hàng cuối kỳ)
    Chốt lot_size=2: 2,49 vòng/năm ≈ hàng nằm kho ~5 tháng, nằm giữa dải điển
    hình của bán lẻ may mặc (~2-4 vòng/năm) [SUY LUẬN — chuẩn ngành chung,
    không phải số riêng của JM]. Đánh đổi: hết hàng cuối kỳ 28,7% (lot=3 là
    21,1%), chấp nhận được vì đây là cấp SKU tức từng size-màu-cửa hàng.
    GIỚI HẠN ĐÃ BIẾT: sell-through 93% là cao so với thực tế vì generator
    không có cơ chế hàng ế/markdown; chọn lot nào cũng không sửa được điểm này.

    Bản cũ sinh `quantity` bằng np.random.gamma(1.8, 4) độc lập ở MỖI kỳ
    snapshot — con số không liên quan gì tới hàng đã bán, nên mọi chỉ số vòng
    quay/sell-through tính ra đều vô nghĩa. Đây là lỗi NỘI DUNG chứ không phải
    lỗi kỹ thuật: bảng vẫn đúng schema, vẫn upload được, không có gì báo lỗi.

    Cách làm mới — suy NGƯỢC từ hàng đã bán, không mô phỏng xuôi:
      1. Sổ cái chuyển động dựng từ bills_raw + orders_raw + return_events,
         phủ TOÀN BỘ cặp (kho, SKU).
      2. Nhập bổ sung theo chu kỳ `replen_days`: đầu mỗi chu kỳ nhập phần
         nhu cầu RÒNG — nhu cầu chu kỳ đó TRỪ tồn còn lại từ chu kỳ trước —
         rồi làm tròn LÊN bội số `lot_size`. Nhờ
         đặt theo LÔ, SKU bán chậm luôn dư hàng còn SKU bán nhanh về gần 0
         cuối chu kỳ -> chênh lệch vòng quay giữa các size/màu trong cùng một
         SP (gãy size, GR-INV.5) xuất hiện tự nhiên, không cần cơ chế riêng.
      3. daily_snapshot chỉ materialize một PANEL CỐ ĐỊNH (depot x SKU) để giữ
         số dòng tương đương bản cũ. Bản cũ random lại tập SKU ở mỗi kỳ nên
         chuỗi thời gian của một SKU bị đứt đoạn -> không thể reconcile.
      4. Phiếu nhập bổ sung được trả ra qua attrs["receipts"] để
         gen_nhanh_bills_full sinh phiếu chuyển kho/nhập kho CÓ products thật.

    GIỚI HẠN ĐÃ BIẾT (cố ý): không sinh được tình trạng HẾT HÀNG THẬT (tồn = 0
    trong khi vẫn còn nhu cầu), vì dữ liệu bán đã sinh TRƯỚC — ép tồn về 0 sẽ
    mâu thuẫn với chính hóa đơn đã có. Tồn chỉ chạm 0 sau giao dịch cuối chu kỳ.
    """
    shops = [s for s in stores if not s["is_warehouse"]]
    wh_loi = next((s for s in stores if s["code"] == "WH_LOI"), None)
    wh_loi_id = wh_loi["id"] if wh_loi else None
    code_of_depot = {s["id"]: s["code"] for s in stores}
    by_code = {c["code"]: c for c in children}

    # ---- PANEL CỐ ĐỊNH cho daily_snapshot ----
    skus = random.sample(children, k=min(sku_sample, len(children)))
    panel = {}
    for s in shops:
        panel[s["id"]] = [c["code"] for c in random.sample(skus, k=max(1, int(len(skus) * 0.35)))]
    if wh_loi is not None:
        panel[wh_loi["id"]] = [c["code"] for c in skus]

    # ---- SỔ CÁI ----
    mv = _movement_ledger(df_bills, df_orders, return_events, wh_loi_id) \
        if df_bills is not None else {}

    start_ord, end_ord = start.toordinal(), end.toordinal()
    snap_ords = list(range(start_ord, end_ord + 1, freq_days))

    # ---- NHẬP BỔ SUNG THEO CHU KỲ ----
    # Kho lỗi không bao giờ nhập bổ sung (chỉ nhận hàng hỏng, không bán ra).
    receipts = {}                      # (dep, code) -> {cycle_start_ord: qty}
    # [FIX v3.1] Trước đây mỗi chu kỳ nhập đủ nhu cầu GỘP, làm tròn lên bội
    # lot_size, KHÔNG trừ tồn đang có. Dư của chu kỳ trước không bao giờ được
    # dùng -> mỗi chu kỳ có bán lại bồi thêm ceil(d/lot)*lot − d đơn vị, tích
    # lũy đơn điệu suốt kỳ. Đó là nguyên nhân thật của vòng quay thấp; hạ
    # lot_size chỉ làm chậm tích lũy chứ không chặn được.
    #   net_need(c) = max(0, demand(c) − tồn dự kiến đầu chu kỳ c)
    # Phép chiếu tồn CỐ Ý chỉ theo dõi đơn nhập và nhu cầu gộp, không cộng hàng
    # hoàn về (mv > 0): hàng hoàn về giữa chu kỳ không chắc kịp bán, coi như
    # đệm an toàn. Cách này khớp đúng với mô phỏng ở jm_inv_diagnostic.py.
    for (dep, code), deltas in mv.items():
        if dep == wh_loi_id:
            continue
        need = {}
        for o, v in deltas.items():
            if v < 0:
                c0 = start_ord + ((o - start_ord) // replen_days) * replen_days
                need[c0] = need.get(c0, 0) - v
        if need:
            rec = {}
            stock_proj = 0
            for c0 in sorted(need):
                nd = need[c0]
                net = nd - stock_proj
                if net > 0:
                    q = -(-net // lot_size) * lot_size
                    rec[c0] = q
                    stock_proj += q
                stock_proj -= nd
                if stock_proj < 0:
                    stock_proj = 0
            receipts[(dep, code)] = rec
    # Cặp thuộc panel nhưng KHÔNG bán được gì -> vẫn bày 1 lô hàng.
    # [FIX v3.1] `setdefault` trên key start_ord chỉ kiểm tra "đã có phiếu nhập
    # đúng NGÀY ĐẦU KỲ chưa", nên cặp CÓ nhu cầu (phiếu nhập rơi vào chu kỳ
    # khác) vẫn bị cộng thêm một lô. Hệ quả: gần như cả 4.460 cặp panel ôm sẵn
    # 1 lô tồn chết từ ngày đầu, nằm NGOÀI vòng tính nhu cầu ròng nên không bao
    # giờ bị trừ đi. Đo được: tồn kỳ đầu 5,45 đv/cặp so với 2,9 của mô phỏng.
    # Sửa: chỉ cấp lô trưng bày cho cặp chưa có BẤT KỲ phiếu nhập nào.
    for dep, codes in panel.items():
        if dep == wh_loi_id:
            continue
        for code in codes:
            if (dep, code) not in receipts:
                receipts[(dep, code)] = {start_ord: lot_size}

    # ---- CHỐT TỒN TẠI NGÀY SNAPSHOT (chỉ panel) ----
    rows, audit = [], []
    for dep, codes in panel.items():
        wcode = code_of_depot[dep]
        for code in codes:
            c = by_code[code]
            evs = {}
            for o, v in mv.get((dep, code), {}).items():
                evs[o] = evs.get(o, 0) + v
            for o, q in receipts.get((dep, code), {}).items():
                evs[o] = evs.get(o, 0) + q
            keys = sorted(evs)
            stock = 0
            cum_in = cum_out = 0
            ki = 0
            for so in snap_ords:
                while ki < len(keys) and keys[ki] <= so:
                    d = evs[keys[ki]]
                    stock += d
                    if d > 0: cum_in += d
                    else:     cum_out += -d
                    ki += 1
                sd = date.fromordinal(so)
                rows.append({
                    "snapshot_date": sd.isoformat(),
                    "snapshot_time": f"{sd.isoformat()}T02:00:00",
                    "product_id": code,
                    "parent_product_code": code.split("-")[0],
                    "parent_product_name": c["name"].split(" - ")[0],
                    "product_name": c["name"], "warehouse_code": wcode,
                    "quantity": int(stock), "unit_price": c["retail"],
                    "cost_price": c["avg_cost"],
                    "import_price": int(c["avg_cost"] * 1.05),
                })
            while ki < len(keys):
                d = evs[keys[ki]]
                stock += d
                if d > 0: cum_in += d
                else:     cum_out += -d
                ki += 1
            audit.append({"depot_id": dep, "product_id": code, "total_in": cum_in,
                          "total_out": cum_out, "closing": stock})

    df_snap = pd.DataFrame(rows)
    g = df_snap.groupby("snapshot_date")
    summary = g.agg(
        total_products=("product_id", "nunique"),
        total_warehouses=("warehouse_code", "nunique"),
        total_quantity=("quantity", "sum"),
    ).reset_index()
    summary["products_in_stock"] = g.apply(
        lambda x: int((x["quantity"] > 0).sum()), include_groups=False).values
    summary["products_out_of_stock"] = g.apply(
        lambda x: int((x["quantity"] == 0).sum()), include_groups=False).values
    summary["total_inventory_value"] = g.apply(
        lambda x: int((x["quantity"] * x["cost_price"]).sum()), include_groups=False).values

    hc = summary[["snapshot_date", "total_products", "total_warehouses", "total_quantity"]].copy()
    hc = hc.rename(columns={"snapshot_date": "check_date"})
    hc["total_quantity_yesterday"] = hc["total_quantity"].shift(1).fillna(hc["total_quantity"])
    hc["change"] = hc["total_quantity"] - hc["total_quantity_yesterday"]
    hc["change_percent"] = (hc["change"] / hc["total_quantity_yesterday"] * 100).round(2)
    hc["quantity_status"] = np.where(hc["change_percent"].abs() > 15, "ABNORMAL", "OK")
    hc["warehouse_status"] = "OK"
    hc["change_status"] = np.where(hc["change"] >= 0, "INCREASE", "DECREASE")

    # ---- gom phiếu nhập theo (kho, chu kỳ) để sinh chứng từ xuất/nhập ----
    by_doc = {}
    for (dep, code), rec in receipts.items():
        for c0, q in rec.items():
            if q > 0:
                by_doc.setdefault((dep, c0), []).append((code, q))
    receipt_docs = []
    for (dep, c0), lines in sorted(by_doc.items()):
        for i in range(0, len(lines), 100):      # tối đa 100 dòng SP mỗi chứng từ
            chunk = lines[i:i + 100]
            receipt_docs.append({
                "depot_id": dep, "date": date.fromordinal(c0),
                "products": [{
                    "imexId": random.randint(10**6, 10**7),
                    "id": by_code[cd]["id"], "code": cd, "barcode": None,
                    "name": by_code[cd]["name"], "quantity": int(q),
                    "price": by_code[cd]["avg_cost"], "discount": 0,
                    "totalDiscount": 0, "amount": int(by_code[cd]["avg_cost"] * q),
                } for cd, q in chunk],
            })

    df_snap.attrs["audit"] = pd.DataFrame(audit)
    df_snap.attrs["receipts"] = receipt_docs
    return df_snap, hc, summary


# ==============================================================================
# 13. MEMBERSHIP ENGINE — hạng thẻ + điểm (tích/tiêu/hết hạn)  [FIX #5]
# ==============================================================================
def apply_membership_and_points(df_bills, online_events, placeholder_ids, cust_birthday):
    """Engine hạng thẻ + điểm — [M5 v3] CHỈ chạy trên hóa đơn OFFLINE.

    online_events luôn rỗng ở v3 (xem orders_as_spend_events): chương trình
    thành viên là chính sách của CỬA HÀNG, khách mua trên sàn không tích điểm
    và không hưởng ưu đãi hạng. v2.1 từng gộp xuyên kênh để cứu phân bố hạng
    — đúng kỹ thuật nhưng sai nghiệp vụ; v3 bù bằng customer_weight_shape.

    [v3] Bổ sung 2 nghiệp vụ v2 chưa có:
      - Ưu đãi SINH NHẬT: 15-30% theo hạng, 1 lần/năm, tối đa 5 SP
      - Ưu đãi NÂNG HẠNG: giảm giá cho hóa đơn đầu tiên ngay sau khi lên hạng

    Chỉ hóa đơn OFFLINE được ghi ngược dữ liệu (payment_points, tiêu điểm,
    products...) vì orders_raw không có trường điểm trong schema Nhanh.vn.

    cust_birthday: dict customer_id -> date sinh nhật (date object), lấy từ
    df_cust["birthday"] tại nơi gọi hàm. Khách placeholder có birthday=None
    nên sẽ không có mặt trong dict (hoặc map tới None) — không ảnh hưởng vì
    sale_mask đã loại placeholder khỏi df_sale từ đầu.

    Trả về (df_bills đã cập nhật, dict customer_id -> (tier, số dư điểm)).
    """
    sale_mask = (df_bills["bill_type"] == "2") & (~df_bills["customer_id"].isin(placeholder_ids))
    df_sale = df_bills[sale_mask]

    # ---- dựng dòng sự kiện gộp: (customer_id, sort_key, kind, payload) ----
    events = []
    for i, cid, bdt, amt in zip(df_sale.index, df_sale["customer_id"],
                                 df_sale["bill_datetime"], df_sale["payment_amount"]):
        events.append((cid, str(bdt), "B", i, amt))
    for e in online_events:
        # đơn online xếp cuối ngày để hóa đơn offline cùng ngày được xử lý trước
        events.append((e["customer_id"], e["date"].isoformat() + "T23:59:59", "O", -1, e["total"]))
    events.sort(key=lambda x: (x[0], x[1]))

    ACT_WIN_START = date(2024, 7, 1).toordinal()
    ACT_WIN_END = date(2025, 12, 31).toordinal()
    RESET_ORD = date(2026, 1, 1).toordinal()
    END_ORD = CONFIG["end_date"].toordinal()
    redeem_prob = CONFIG["points_redeem_prob"]

    # ghi ngược theo lô (nhanh hơn .at từng dòng rất nhiều ở quy mô 500k+)
    upd_points = {}
    upd_redeem = {}   # idx -> (used_value, used_amount, payment_amount, customer_amount, products, cash, transfer, credit)
    upd_benefit = {}  # [v3] idx -> (products, payment_amount, pay) — ưu đãi sinh nhật/nâng hạng

    cur_cust = None
    history = []      # [(ordinal, amount)]
    ledger = []       # [[earn_ordinal, points_left]] FIFO
    reset_done = False
    last_tier_info = {}

    def flush(cid):
        if cid is None:
            return
        bal = sum(p for _o, p in ledger)
        lo = END_ORD - 365
        spend = sum(amt for o, amt in history if lo <= o <= END_ORD)
        tier_name, _rate = tier_for_spend(spend)
        last_tier_info[cid] = (tier_name, int(bal))

    last_seen_tier = {}                       # [v3] theo dõi hạng để phát hiện nâng hạng
    birthday_used = {}                        # [v3] (cid, năm) -> đã dùng ưu đãi sinh nhật chưa
    TIER_ORDER = ["Member", "Silver", "Gold", "Platinum", "Diamond"]

    for cid, sort_key, kind, idx, amount in events:
        b_ord = date.fromisoformat(sort_key[:10]).toordinal()

        if cid != cur_cust:
            flush(cur_cust)
            cur_cust = cid
            history, ledger, reset_done = [], [], False

        # GR-CUST.10: không phát sinh giao dịch nào trong 01/07/2024-31/12/2025
        # -> điểm về 0 và hạng về Member kể từ 01/01/2026.
        if not reset_done and b_ord >= RESET_ORD:
            if not any(ACT_WIN_START <= o <= ACT_WIN_END for o, _a in history):
                history, ledger = [], []
            reset_done = True

        is_true_first = (len(history) == 0)
        ledger = [[o, p] for o, p in ledger if o >= b_ord - 365 and p > 0]

        lo_ord = b_ord - 365
        spend_before = sum(amt for o, amt in history if lo_ord <= o < b_ord)
        tier_name, rate = ("Member", 1) if is_true_first else tier_for_spend(spend_before)

        # [v3] Phát hiện NÂNG HẠNG: so hạng hiện tại với hạng ở giao dịch trước.
        # Cơ chế: vượt ngưỡng chi tiêu 12 tháng -> lên hạng ngay lập tức.
        prev_tier = last_seen_tier.get(cid)
        just_upgraded = (prev_tier is not None and prev_tier != tier_name
                         and TIER_ORDER.index(tier_name) > TIER_ORDER.index(prev_tier))
        last_seen_tier[cid] = tier_name

        payment_amount = amount

        if kind == "O":
            # Đơn online: chỉ cộng chi tiêu + tích điểm, không ghi ngược dữ liệu.
            pts = 0 if is_true_first else int(payment_amount // 100_000) * rate
            if pts > 0:
                ledger.append([b_ord, pts])
            history.append((b_ord, payment_amount))
            continue

        # ---- hóa đơn offline ----
        used_points_value = 0
        if (not is_true_first) and random.random() < redeem_prob:
            available = sum(p for _o, p in ledger)
            redeem = min(available, int(0.5 * payment_amount / 1000))
            if redeem > 0:
                used_points_value = redeem
                remaining = redeem
                for entry in ledger:
                    if remaining <= 0:
                        break
                    take = min(entry[1], remaining)
                    entry[1] -= take
                    remaining -= take
                ledger = [e for e in ledger if e[1] > 0]

        if used_points_value > 0:
            # GR-CUST.8: hóa đơn có tiêu điểm không được chứa dòng SP discount > 0
            new_items, new_total = [], 0
            for it in df_bills.at[idx, "products"]:
                it2 = dict(it)
                it2["discount"] = 0
                it2["totalDiscount"] = 0
                it2["amount"] = it["price"] * it["quantity"]
                new_items.append(it2)
                new_total += it2["amount"]
            payment_amount = new_total
            used_amt = used_points_value * 1000
            customer_amount = max(0, payment_amount - used_amt)
            pay = _split_payment(customer_amount)
            upd_redeem[idx] = (used_points_value, used_amt, payment_amount,
                                customer_amount, new_items, pay)

        # ==================================================================
        # [v3] ƯU ĐÃI SINH NHẬT + ƯU ĐÃI NÂNG HẠNG
        # ==================================================================
        # Quy tắc loại trừ 3 tầng (Business Domain 2.3): 2 ưu đãi này thuộc
        # Tầng 2 (ưu đãi hạng thẻ) nên KHÔNG áp cùng hóa đơn có tiêu điểm
        # (Tầng 3 — GR-CUST.8 cấm hóa đơn tiêu điểm chứa dòng SP discount > 0)
        # và không áp lên SP đang sale (Tầng 1 đã chiếm chỗ).
        #
        # [v3 — Rachel chốt] SINH NHẬT và NÂNG HẠNG là 2 ưu đãi ĐỘC LẬP, khác
        # nguồn gốc (voucher gửi theo tháng sinh vs sự kiện vượt ngưỡng chi
        # tiêu). Business Domain 2.3 chỉ quy định Tầng 1 khóa Tầng 2, không hề
        # bắt 2 ưu đãi trong cùng Tầng 2 loại trừ nhau. Khi cả hai cùng đủ điều
        # kiện trên một hóa đơn: LẤY MỨC CAO NHẤT, không cộng dồn và không nhân
        # tuần tự.  [QUYẾT ĐỊNH]
        #
        # Lưu ý cấu trúc: hai điều kiện phải xét ĐỘC LẬP (2 khối `if` riêng),
        # KHÔNG dùng if/elif — bản trước dùng elif nên khách lên hạng đúng vào
        # tháng sinh nhật mà đã tiêu voucher sinh nhật rồi thì mất luôn ưu đãi
        # nâng hạng.
        bday_rate = 0.0
        upg_rate = 0.0
        if used_points_value == 0 and not is_true_first:
            bday = cust_birthday.get(cid)
            b_date = date.fromisoformat(sort_key[:10])
            if bday and bday.month == b_date.month and (cid, b_date.year) not in birthday_used:
                # 1 hóa đơn/năm, đúng tháng sinh nhật. Trần 5 SP được xử lý ở
                # khối áp giảm giá bên dưới (theo đơn vị hàng, không loại cả HĐ).
                bday_rate = BIRTHDAY_DISCOUNT_BY_TIER.get(tier_name, 0.15)
            if just_upgraded:
                upg_rate = TIER_UPGRADE_BONUS.get(tier_name, 0.0)

        extra_disc_rate = max(bday_rate, upg_rate)
        # Chỉ đánh dấu đã dùng voucher sinh nhật khi nó THỰC SỰ được áp. Nếu
        # ưu đãi nâng hạng cao hơn và chiếm chỗ, voucher sinh nhật coi như
        # chưa tiêu -> khách vẫn dùng được ở hóa đơn sau trong cùng tháng.
        if bday_rate > 0 and extra_disc_rate == bday_rate:
            birthday_used[(cid, date.fromisoformat(sort_key[:10]).year)] = True

        if extra_disc_rate > 0:
            items_now = df_bills.at[idx, "products"]
            if isinstance(items_now, list) and items_now:
                # [v3] Trần "tối đa 5 SẢN PHẨM/hóa đơn" của ưu đãi sinh nhật
                # (Business Domain 2.6) đếm theo ĐƠN VỊ hàng, không phải số
                # DÒNG sản phẩm — một dòng quantity=2 tiêu 2 suất. Ưu đãi nâng
                # hạng KHÔNG có trần này. Bản trước hiểu sai thành "hóa đơn có
                # >5 dòng thì mất trắng ưu đãi".
                # Ưu tiên áp cho hàng đắt nhất trước (nhân viên quầy luôn áp
                # theo hướng có lợi nhất cho khách).  [SUY LUẬN]
                cap = BIRTHDAY_MAX_ITEMS if extra_disc_rate == bday_rate else None
                order = sorted(
                    range(len(items_now)),
                    key=lambda j: -items_now[j]["price"]) if cap is not None \
                    else range(len(items_now))

                new_items = [dict(it) for it in items_now]
                remaining = cap
                for j in order:
                    it = items_now[j]
                    # chỉ áp lên hàng NGUYÊN GIÁ (Tầng 1 chưa chiếm chỗ)
                    if it.get("discount", 0) != 0:
                        continue
                    qty = it["quantity"]
                    if remaining is not None:
                        if remaining <= 0:
                            break
                        n_units = min(qty, remaining)
                        remaining -= n_units
                    else:
                        n_units = qty
                    d = int(it["price"] * n_units * extra_disc_rate)
                    # GIỮ ĐÚNG QUY ƯỚC gen_sales_bills: `discount` và
                    # `totalDiscount` đều là số tiền giảm CỦA CẢ DÒNG (không
                    # phải giảm/đơn vị). payment_discount = tổng cột `discount`
                    # nên chia cho quantity ở đây sẽ làm lệch payment_discount.
                    new_items[j]["discount"] = d
                    new_items[j]["totalDiscount"] = d
                    new_items[j]["amount"] = it["price"] * qty - d

                new_total = sum(i["amount"] for i in new_items)
                pay = _split_payment(new_total)
                upd_benefit[idx] = (new_items, new_total, pay)
                payment_amount = new_total

        points_earned = 0 if is_true_first else int(payment_amount // 100_000) * rate
        upd_points[idx] = points_earned
        if points_earned > 0:
            ledger.append([b_ord, points_earned])
        history.append((b_ord, payment_amount))

    flush(cur_cust)

    # ---- ghi ngược theo lô ----
    if upd_points:
        s = pd.Series(upd_points)
        df_bills.loc[s.index, "payment_points"] = s.values
    for idx, (uv, ua, pa, ca, items, pay) in upd_redeem.items():
        df_bills.at[idx, "products"] = items
        df_bills.at[idx, "payment_discount"] = 0
        df_bills.at[idx, "payment_amount"] = pa
        df_bills.at[idx, "payment_customer_amount"] = ca
        df_bills.at[idx, "payment_used_points_value"] = uv
        df_bills.at[idx, "payment_used_points_amount"] = ua
        df_bills.at[idx, "payment_cash_amount"] = pay["payment_cash_amount"]
        df_bills.at[idx, "payment_transfer_amount"] = pay["payment_transfer_amount"]
        df_bills.at[idx, "payment_credit_amount"] = pay["payment_credit_amount"]

    # [v3] ghi ngược ưu đãi sinh nhật / nâng hạng — loại trừ với upd_redeem
    # theo thiết kế (used_points_value == 0 là điều kiện bật extra_disc_rate ở
    # trên), nên không có idx trùng giữa 2 dict này.
    for idx, (items, pa, pay) in upd_benefit.items():
        total_disc = sum(it["discount"] for it in items)
        df_bills.at[idx, "products"] = items
        df_bills.at[idx, "payment_discount"] = total_disc
        df_bills.at[idx, "payment_amount"] = pa
        df_bills.at[idx, "payment_customer_amount"] = pa
        df_bills.at[idx, "payment_cash_amount"] = pay["payment_cash_amount"]
        df_bills.at[idx, "payment_transfer_amount"] = pay["payment_transfer_amount"]
        df_bills.at[idx, "payment_credit_amount"] = pay["payment_credit_amount"]

    return df_bills, last_tier_info


# ==============================================================================
# 14. CUSTOMER AGGREGATES — noise cố ý #3 (đứt gãy lịch sử placeholder) +
#     gắn membership_tier/points thật vào customer master
# ==============================================================================
def finalize_customers(df_cust, df_bills, df_orders, migration_date, end, tier_info):
    """[FIX v2.1 #17] Aggregate khách hàng nay tính trên CẢ HAI KÊNH.

    Bản trước chỉ cộng hóa đơn offline, nên totalAmount/frequencyBought/
    daysNotBought — vốn là đầu vào trực tiếp của bảng phân hạng RFM
    t_customer_tier_final — chỉ phản ánh ~55% hành vi thật của khách.

    Nhiễu cố ý (đứt gãy lịch sử của nhóm placeholder tại migration_date) vẫn
    giữ nguyên, chỉ mở rộng sang cả giao dịch online.
    """
    b = df_bills[df_bills["bill_type"] == "2"][["customer_id", "bill_date", "payment_amount"]].copy()
    b = b.rename(columns={"bill_date": "txn_date", "payment_amount": "value"})
    b["txn_date"] = pd.to_datetime(b["txn_date"]).dt.date

    if df_orders is not None and not df_orders.empty:
        # [M1 — v3] Bỏ bộ lọc order_mode != 1: cột order_mode không còn tồn tại
        # vì JM không có bán buôn (mọi đơn online đều là bán lẻ).
        # LƯU Ý: khối này tính chỉ số HÀNH VI khách (recency/frequency/monetary
        # cho RFM/CLV) — khác với hạng thẻ thành viên. RFM vẫn tính XUYÊN KÊNH
        # (đúng bản chất: đo hành vi mua thực tế), chỉ có hạng thẻ mới bị giới
        # hạn ở offline (M5). Đây là 2 khái niệm tách biệt, không mâu thuẫn.
        # [FIX v3.1] M6 gán NHÃN CHỮ ngay tại lúc tạo dòng (dòng 1409/1416), nên
        # so sánh với số nguyên 60/14 KHÔNG BAO GIỜ khớp -> `o` rỗng -> toàn bộ
        # doanh thu online bị loại khỏi totalAmount/frequencyBought/daysNotBought,
        # đúng cái lỗi mà docstring phía trên tuyên bố đã sửa. Lỗi im lặng: không
        # exception, không FAIL trong QA, chỉ lộ ra khi viết SQL RFM.
        o = df_orders[(df_orders["status"] == STATUS_LABELS[60])
                      & (df_orders["order_type"] != ORDER_TYPE_LABELS[14])].copy()
        o["txn_date"] = pd.to_datetime(o["created_at"]).dt.date
        o["value"] = o["products"].apply(
            lambda ps: sum(i["amount"] for i in ps) if isinstance(ps, list) else 0)
        o = o[["customer_id", "txn_date", "value"]]
        txn = pd.concat([b, o], ignore_index=True)
    else:
        txn = b

    def _agg(frame):
        return frame.groupby("customer_id").agg(
            totalAmount=("value", "sum"),
            frequencyBought=("value", "count"),
            last_buy=("txn_date", "max"),
        ).reset_index()

    agg_all = _agg(txn)
    agg_after = _agg(txn[txn["txn_date"] >= migration_date])

    ph_ids = set(df_cust[df_cust["is_placeholder"]]["id"])
    agg = pd.concat([
        agg_all[~agg_all["customer_id"].isin(ph_ids)],
        agg_after[agg_after["customer_id"].isin(ph_ids)],
    ], ignore_index=True)

    # GR-CUST.16: customer_id gắn với giao dịch đầu tiên — startedDate là NGÀY
    # KHÁCH XUẤT HIỆN LẦN ĐẦU thật sự, không phải ngày ngẫu nhiên như bản trước.
    # Tính trên MỌI lần xuất hiện (kể cả đơn bị hủy / đơn bán buôn), vì tài
    # khoản khách được tạo ngay ở lần tương tác đầu tiên bất kể kết quả đơn.
    _seen = [pd.DataFrame({
        "customer_id": df_bills["customer_id"],
        "d": pd.to_datetime(df_bills["bill_date"]).dt.date,
    })]
    if df_orders is not None and not df_orders.empty:
        _seen.append(pd.DataFrame({
            "customer_id": df_orders["customer_id"],
            "d": pd.to_datetime(df_orders["created_at"]).dt.date,
        }))
    first_txn = pd.concat(_seen, ignore_index=True).groupby("customer_id")["d"].min()

    out = df_cust.merge(agg, left_on="id", right_on="customer_id", how="left")
    out["totalAmount"] = out["totalAmount"].fillna(0).astype(int)
    out["frequencyBought"] = out["frequencyBought"].fillna(0).astype(int)
    out["daysNotBought"] = out["last_buy"].apply(
        lambda x: (end - x).days if pd.notna(x) else None)
    out["startedDate"] = out.apply(
        lambda r: (CONFIG["start_date"].isoformat() if r["is_placeholder"]
                   else (first_txn[r["id"]].isoformat() if r["id"] in first_txn.index else None)),
        axis=1)

    # GR-CUST.16: không tồn tại customer_id nào không có giao dịch nào.
    # LƯU Ý: điều kiện giữ lại phải là "xuất hiện ở BẤT KỲ đâu trong bills_raw
    # hoặc orders_raw", KHÔNG phải "có giao dịch bán lẻ thành công". Khách chỉ
    # có đơn online bị hủy, hoặc chỉ có đơn bán buôn, vẫn phải tồn tại trong
    # customer master — nếu không sẽ vỡ toàn vẹn tham chiếu orders → customers.
    referenced = set(df_bills["customer_id"].unique())
    if df_orders is not None and not df_orders.empty:
        referenced |= set(df_orders["customer_id"].unique())
    n_before = len(out)
    out = out[out["is_placeholder"] | out["id"].isin(referenced)].copy()
    n_dropped = n_before - len(out)
    if n_dropped:
        print(f"   → loại {n_dropped:,} khách không phát sinh giao dịch nào (GR-CUST.16)")

    tier_map = tier_info  # customer_id -> (tier_name, points_balance)
    out["membership_tier"] = out["id"].apply(
        lambda cid: "Member" if cid in ph_ids else tier_map.get(cid, ("Member", 0))[0])
    out["points"] = out["id"].apply(
        lambda cid: 0 if cid in ph_ids else tier_map.get(cid, ("Member", 0))[1])

    out["updatedAt"] = datetime.now().isoformat(timespec="seconds")
    out["locations"] = None
    out["location"] = None
    out["level"] = None
    out["group"] = None
    out["_loaded_at"] = datetime.now().isoformat(timespec="seconds")
    out["_batch_id"] = "batch_final"

    cols = ["id","type","name","mobile","gender","birthday","points","startedDate",
            "locations","location","level","group","totalAmount","updatedAt",
            "frequencyBought","daysNotBought","membership_tier","_loaded_at","_batch_id"]
    df_customers = out[cols]

    t = out[["id","name","mobile","totalAmount","daysNotBought"]].copy()
    t = t.rename(columns={"id":"customer_id","name":"customer_name"})
    q = t["totalAmount"]
    labels_all = ["Chưa mua", "Thường", "Tiềm năng", "VIP", "VVIP"]
    raw_edges = [-1, 1, q.quantile(.5), q.quantile(.8), q.quantile(.95), q.max() + 1]
    # Dữ liệu quy mô nhỏ (hoặc nhiều khách chưa mua) có thể khiến các quantile
    # trùng nhau -> pd.cut đòi bin tăng ngặt. Khử trùng, giữ nhãn tương ứng.
    edges, labels = [raw_edges[0]], []
    for e, lab in zip(raw_edges[1:], labels_all):
        if e > edges[-1]:
            edges.append(e)
            labels.append(lab)
    if len(edges) < 2:
        t["Potential_Tier"] = "Chưa mua"
    else:
        t["Potential_Tier"] = pd.cut(q, bins=edges, labels=labels).astype(str)
    t["Activity_Status"] = t["daysNotBought"].apply(
        lambda d: "Chưa mua" if pd.isna(d) else
                  ("Đang hoạt động" if d <= 90 else
                   ("Có nguy cơ rời bỏ" if d <= 180 else "Đã rời bỏ")))
    t["Final_Tier"] = np.where(
        t["Activity_Status"] == "Đã rời bỏ", "Cần kích hoạt lại", t["Potential_Tier"])
    return df_customers, t


# ==============================================================================
# 15. GHI FILE — CSV cho bảng phẳng, NDJSON cho bảng có cột nested [FIX #11]
# ==============================================================================
def _sanitize_nan(obj):
    """NaN/Infinity -> None trước json.dumps (BigQuery chỉ nhận JSON chuẩn RFC 8259)."""
    if isinstance(obj, float) and (obj != obj or obj in (float("inf"), float("-inf"))):
        return None
    if isinstance(obj, dict):
        return {k: _sanitize_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_nan(v) for v in obj]
    return obj


def write_ndjson(df, path, chunk=20_000):
    """[v3] Ghi theo LÔ thay vì df.to_dict("records") một phát.

    Bản cũ dựng nguyên một list Python chứa toàn bộ bảng trước khi ghi — với
    bills_raw/orders_raw (hàng trăm nghìn dòng, mỗi dòng có mảng products lồng)
    đây là bản sao đầy đủ của bảng trong RAM và là chỗ tốn bộ nhớ nhất cả
    pipeline. Ghi theo lô 20.000 dòng giữ đỉnh bộ nhớ gần như không đổi.
    """
    with open(path, "w", encoding="utf-8") as f:
        for i in range(0, len(df), chunk):
            for rec in df.iloc[i:i + chunk].to_dict("records"):
                rec = _sanitize_nan(rec)
                f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")


# ==============================================================================
# 16. MAIN
# ==============================================================================
def main(cfg=CONFIG):
    CONFIG.update(cfg)
    cfg = CONFIG
    init_seed(cfg["seed"])
    out = cfg["output_dir"]
    dirs = ["shop_data","product_data","customer_data","retail_data",
            "order_data","bill_data","inventory_data","palexy_data"]
    for d in dirs:
        os.makedirs(os.path.join(out, d), exist_ok=True)

    start, end = cfg["start_date"], cfg["end_date"]

    print("→ 1/9 shop_data ...")
    df_depots, stores = gen_depots()
    df_map = gen_depot_id_mapping(stores)

    print("→ 2/9 product_data ...")
    df_cat, df_int = gen_categories()
    parents, children = gen_products(df_cat, df_int, int(cfg["n_products_parent"]))
    df_prod = build_products_df(parents, children, stores)
    child_by_collection = {}
    for c in children:
        child_by_collection.setdefault(c["col_name"], []).append(c)

    print("→ 3/9 employees & work_schedule ...")
    df_emp = gen_employees(stores)
    df_ws = gen_work_schedule(df_emp, start, end)

    print("→ 4/9 customers (base) + trọng số mua hàng theo khách ...")
    df_cust = gen_customers(int(cfg["n_customers"]))
    placeholder_ids = set(df_cust[df_cust["is_placeholder"]]["id"])
    picker = CustomerPicker(df_cust[~df_cust["is_placeholder"]]["id"].tolist(),
                            cfg["customer_weight_shape"])

    print("→ 5/9 hiệu chỉnh quy mô theo năm (calibrate_offline_scale) ...")
    target_total = cfg["yearly_total_target"]
    online_share = cfg["online_share"]
    target_offline = {y: int(round(t * (1 - online_share))) for y, t in target_total.items()}
    scale_mult = calibrate_offline_scale(stores, start, end, target_offline)
    for y, m in sorted(scale_mult.items()):
        print(f"   năm {y}: offline target≈{target_offline.get(y,0):,}  scale_mult={m:.4f}")

    print("→ 6/9 bills_raw — hóa đơn bán (chưa gồm đổi/trả) ...")
    bill_ctr = IdGen(5_000_000)
    df_sales, bills_per_day, sold_history = gen_sales_bills(
        stores, children, df_cust, df_emp, start, end, bill_ctr, scale_mult,
        child_by_collection, picker)
    print(f"   → {len(df_sales):,} hóa đơn bán")

    # THỨ TỰ MỚI (v2.1): orders phải sinh TRƯỚC returns, vì cửa sổ đổi/trả phụ
    # thuộc hạng thẻ, mà hạng thẻ nay tính trên chi tiêu XUYÊN KÊNH.
    print("→ 7/9 orders_raw (đơn online, mục tiêu tổng năm - offline ước tính) ...")
    ret_rate = cfg["return_rate"]
    sales_by_year = {}
    for bd in df_sales["bill_date"]:
        y = int(bd[:4])
        sales_by_year[y] = sales_by_year.get(y, 0) + 1
    online_target_by_year = {}
    for y, tot in target_total.items():
        # mỗi phiếu đổi sinh thêm 1 hóa đơn bán mới -> offline cuối cùng ≈ ×(1+ret_rate)
        est_offline = int(sales_by_year.get(y, 0) * (1 + ret_rate))
        online_target_by_year[y] = max(0, tot - est_offline)
        print(f"   năm {y}: offline ước tính={est_offline:,}  -> online target={online_target_by_year[y]:,}")
    order_ctr = IdGen(700_000_000)
    df_orders = gen_orders(stores, children, df_cust, start, end, online_target_by_year,
                            order_ctr, child_by_collection, picker)
    print(f"   → {len(df_orders):,} dòng orders_raw")

    print("→ 8/9 đổi/trả offline (2 phiếu, cửa sổ theo hạng thẻ xuyên kênh) ...")
    sold_history_real = [r for r in sold_history if r["customer_id"] not in placeholder_ids]
    online_events = orders_as_spend_events(df_orders, placeholder_ids)
    tier_lookup = build_tier_lookup(sold_history_real, online_events)
    df_returns = gen_returns(stores, children, sold_history, tier_lookup, end, bill_ctr,
                              child_by_collection, df_emp)
    df_bills = pd.concat([df_sales, df_returns], ignore_index=True).sort_values("bill_datetime").reset_index(drop=True)
    print(f"   → {len(df_bills):,} dòng bills_raw sau khi gộp đổi/trả")

    print("→ 9/9 inventory + nhanh_bills_full + palexy + membership/points ...")
    # [v3] THỨ TỰ MỚI: engine tồn kho chạy TRƯỚC gen_nhanh_bills_full, vì phiếu
    # chuyển kho/nhập kho nay lấy từ chính sổ cái tồn kho (không còn rỗng).
    df_snap, df_hc, df_sum = gen_inventory(
        children, stores, start, end, cfg["inventory_snapshot_freq_days"],
        df_bills=df_bills, df_orders=df_orders,
        return_events=df_orders.attrs.get("return_events", []))
    df_xnk = gen_nhanh_bills_full(df_bills, stores, start, end,
                                  return_events=df_orders.attrs.get("return_events", []),
                                  receipt_docs=df_snap.attrs.get("receipts", []))
    df_daily, df_hourly, df_smap = gen_palexy(stores, start, end, bills_per_day)

    # [v3] birthday của khách placeholder là None -> pandas biến thành NaN (float)
    # khi cột trộn kiểu, nên phải lọc theo isinstance(str) chứ không phải `is None`.
    cust_birthday = {
        cid: date.fromisoformat(bday)
        for cid, bday in zip(df_cust["id"], df_cust["birthday"])
        if isinstance(bday, str) and bday
    }
    df_bills, tier_info = apply_membership_and_points(
        df_bills, online_events, placeholder_ids, cust_birthday)
    df_customers, df_tier = finalize_customers(
        df_cust, df_bills, df_orders, cfg["migration_date"], end, tier_info)

    # ---- ghi file ----
    df_depots.to_csv(f"{out}/shop_data/depots.csv", index=False)
    df_map.to_csv(f"{out}/shop_data/depot_id_mapping.csv", index=False)
    df_smap.to_csv(f"{out}/shop_data/store_mapping.csv", index=False)

    df_cat.to_csv(f"{out}/product_data/nhanh_categories.csv", index=False)
    df_int.to_csv(f"{out}/product_data/nhanh_internal_categories.csv", index=False)
    write_ndjson(df_prod, f"{out}/product_data/nhanh_products_full.ndjson")

    df_emp.to_csv(f"{out}/retail_data/employees.csv", index=False)
    df_ws.to_csv(f"{out}/retail_data/work_schedule.csv", index=False)
    write_ndjson(df_bills, f"{out}/retail_data/bills_raw.ndjson")

    write_ndjson(df_orders, f"{out}/order_data/orders_raw.ndjson")

    # [v3] Giải phóng nhanh_bills_full NGAY sau khi ghi. Đây là bảng nặng nhất
    # (mỗi dòng mang một mảng products lồng, cộng cả phiếu chuyển kho/nhập kho
    # nay đã có hàng thật), và ở quy mô đầy đủ nó nằm trong RAM cùng lúc với
    # bills_raw + orders_raw -> đỉnh bộ nhớ vượt ngưỡng máy 4GB. Ghi xong là
    # xoá, các bảng còn lại đều nhỏ.
    write_ndjson(df_xnk, f"{out}/bill_data/nhanh_bills_full.ndjson")
    n_xnk = len(df_xnk)
    del df_xnk
    gc.collect()

    df_customers.to_csv(f"{out}/customer_data/nhanh_customers_full.csv", index=False)
    df_tier.to_csv(f"{out}/customer_data/t_customer_tier_final.csv", index=False)

    df_daily.to_csv(f"{out}/palexy_data/daily_visits_v2.csv", index=False)
    df_hourly.to_csv(f"{out}/palexy_data/hourly_traffic.csv", index=False)

    df_snap.to_csv(f"{out}/inventory_data/daily_snapshot.csv", index=False)
    df_hc.to_csv(f"{out}/inventory_data/health_check_log.csv", index=False)
    df_sum.to_csv(f"{out}/inventory_data/v_daily_summary.csv", index=False)

    print("\n" + "=" * 62)
    print("HOÀN TẤT — tóm tắt bộ dữ liệu")
    print("=" * 62)
    stats = [
        ("depots", len(df_depots)), ("products (mã con)", len(df_prod)),
        ("employees", len(df_emp)), ("work_schedule", len(df_ws)),
        ("customers", len(df_customers)),
        ("bills_raw (tổng)", len(df_bills)),
        ("  ├ hóa đơn bán (type=2)", int((df_bills.bill_type == "2").sum())),
        ("  └ phiếu trả (type=1)", int((df_bills.bill_type == "1").sum())),
        ("orders_raw", len(df_orders)),
        ("nhanh_bills_full", n_xnk),
        ("palexy daily / hourly", f"{len(df_daily)} / {len(df_hourly)}"),
        ("inventory snapshot", len(df_snap)),
    ]
    for k, v in stats:
        print(f"  {k:<34} {v:>12,}" if isinstance(v, int) else f"  {k:<34} {v:>12}")

    rev = df_bills[df_bills.bill_type == "2"].copy()
    rev["y"] = pd.to_datetime(rev["bill_date"]).dt.year
    ordy = df_orders.copy()
    if not ordy.empty:
        ordy["y"] = pd.to_datetime(ordy["created_at"]).dt.year
    print("\n  Tổng hóa đơn/đơn hàng theo năm (offline + online, so với mục tiêu):")
    for y in sorted(set(rev["y"]) | (set(ordy["y"]) if not ordy.empty else set())):
        n_off = int((rev["y"] == y).sum())
        n_on = int((ordy["y"] == y).sum()) if not ordy.empty else 0
        tgt = target_total.get(y, "-")
        print(f"    {y}: offline={n_off:>9,} | online={n_on:>9,} | tổng={n_off+n_on:>9,}  (mục tiêu≈{tgt})")
    real_cust = df_customers[df_customers["id"] > 3]
    print(f"\n  Hạng thẻ (khách thật, tại {end.isoformat()}):")
    n_real_cust = len(real_cust)
    for t in ["Member", "Silver", "Gold", "Platinum", "Diamond"]:
        c = int((real_cust["membership_tier"] == t).sum())
        pct = 100 * c / max(n_real_cust, 1)
        flag = "  ⚠ TRỐNG" if c == 0 else ""
        print(f"    {t:<10} {c:>9,}  ({pct:5.2f}%){flag}")

    # [FIX v3.1] Dải 60-90 ngày suy ra trên cơ sở OFFLINE (Generation Rules v2
    # mục 5.3: "hiệu chỉnh trên cơ sở doanh thu offline riêng"). Từ khi
    # finalize_customers() được sửa, `frequencyBought` là XUYÊN KÊNH nên không
    # còn so trực tiếp với dải này được. Gate theo offline, in xuyên kênh để
    # quan sát. Mã "GR-CUST.12" bỏ đi: chuỗi này không tồn tại trong
    # Generation Rules v2, nó là chốt chặn hồi quy kế thừa từ v2.1.
    span_days = (end - start).days + 1
    yrs = span_days / 365.25
    n_off_real = int(((~df_bills["customer_id"].isin(placeholder_ids))
                      & (df_bills["bill_type"] == "2")).sum())
    if n_real_cust and n_off_real:
        f_off = n_off_real / n_real_cust / yrs
        gap = 365.25 / f_off
        ok = 60 <= gap <= 90
        print(f"\n  Tần suất mua OFFLINE: {f_off:.2f} giao dịch/khách/năm "
              f"-> khoảng cách ~{gap:.0f} ngày  "
              f"[{'ĐẠT' if ok else 'LỆCH'} — chốt chặn hồi quy v2.1, 60-90 ngày]")
    n_txn_real = int(real_cust["frequencyBought"].sum())
    if n_real_cust and n_txn_real:
        f_all = n_txn_real / n_real_cust / yrs
        print(f"  Tần suất mua XUYÊN KÊNH: {f_all:.2f} giao dịch/khách/năm "
              f"-> khoảng cách ~{365.25 / f_all:.0f} ngày  [quan sát, không gate]")

    # Kiểm chứng mức độ tập trung doanh thu (bán lẻ thật: ~20% khách tạo 60-80%)
    ta = real_cust["totalAmount"].sort_values(ascending=False)
    if ta.sum() > 0:
        top20 = ta.head(max(1, int(len(ta) * 0.2))).sum() / ta.sum()
        print(f"  Tập trung doanh thu: 20% khách hàng đầu tạo {100*top20:.1f}% tổng chi tiêu "
              f"(bán lẻ thật thường 60-80%)")

    print(f"\n  Thư mục output: ./{out}/")
    return {"bills": df_bills, "orders": df_orders, "customers": df_customers}


if __name__ == "__main__":
    main()

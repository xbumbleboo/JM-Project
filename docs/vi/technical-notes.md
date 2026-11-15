# Tài liệu kỹ thuật — JM Synthetic Data

> **Dữ liệu mô phỏng.** Toàn bộ dữ liệu trong dự án do tác giả tự sinh bằng Python, dựa trên quy mô, chính sách, giá và chương trình khuyến mãi công khai của JM. Đây không phải số liệu thật của JM và không phản ánh tình hình kinh doanh của JM.

*Bản 08/11/2026 · Python (generator, mô hình CLV) · Google BigQuery, GoogleSQL · Power BI Desktop, DAX · Đi kèm [#3 Báo cáo insight](insight-report.md) và [#8 Thiết kế dữ liệu mô phỏng](synthetic-data-design.md)*

**Phạm vi.** [#8](synthetic-data-design.md) trình bày đường đi từ quy tắc nghiệp vụ đến 18 bảng do generator sinh ra. Tài liệu này trình bày phần tiếp theo: từ các bảng đó lên BigQuery, qua các tầng view, đến mô hình Power BI. Tài liệu cũng nói cách kiểm để mọi con số trên dashboard khớp với BigQuery.

**Tóm tắt**

- Dữ liệu đi qua bốn tầng: bảng nguồn → chuẩn hóa từng kênh → bảng sự kiện dùng chung → view riêng cho dashboard. Mỗi chỉ số được định nghĩa một lần ở tầng dùng chung, không định nghĩa lại trong từng báo cáo.
- Power BI nạp 7 view `pbi_*` theo mô hình sao. Slicer Năm và Tháng là bảng tách rời; mọi measure đi qua bộ khuôn thời gian dùng chung.
- Mỗi view có số kiểm chạy trên BigQuery. Mỗi trang dashboard được đối chiếu với số BigQuery trước khi chốt.

---

## 1. Kiến trúc dữ liệu

| Tầng | Đối tượng trên BigQuery | Vai trò |
|---|---|---|
| Nguồn | `bills_raw`<br>`orders_raw`<br>`depots`<br>`nhanh_products_full`<br>`nhanh_categories`<br>`nhanh_internal_categories` | 6 bảng từ generator, theo cấu trúc Nhanh.vn, nạp bằng `WRITE_TRUNCATE` |
| Nguồn dẫn xuất | `customer_analytic_base`<br>`customer_clv`<br>`dim_platform_fee` | Bảng vật lý, tính một lần rồi dùng lại:<br>1 dòng mỗi khách (RFM hai kênh, hạng thẻ, phân hạng)<br>kết quả mô hình CLV<br>phí sàn theo khoảng hiệu lực |
| Chuẩn hóa | `stg_offline_revenue`<br>`stg_online_revenue` | Mỗi kênh một view: lọc trạng thái, đặt tên cột thống nhất |
| Sự kiện dùng chung | `fct_retail_revenue`<br>`fct_product_revenue` | Định nghĩa doanh thu (theo giao dịch) và doanh số (theo dòng hàng) cho cả hai kênh |
| Lớp phân tích | `fct_offline_bill`<br>`fct_online_order`<br>`dim_diem_ban`<br>`dim_product`<br>`dim_price_band` | Dùng trong giai đoạn phân tích trước khi dựng dashboard; dashboard không dùng |
| Lớp dashboard | `pbi_giao_dich`<br>`pbi_dong_hang`<br>`pbi_don_online`<br>`pbi_ngay_mua`<br>`pbi_dim_diem_ban`<br>`pbi_dim_san_pham`<br>`pbi_dim_khach` | Mỗi view đúng đơn vị đo của một bảng trong Power BI |

**Từ generator đến BigQuery.** Generator ghi 18 bảng. Phân tích giữ 6 bảng làm nguồn. Hai bảng khách `nhanh_customers_full` và `t_customer_tier_final` chỉ dùng một lần để dựng `customer_analytic_base`; sau đó mọi phân tích khách đọc từ bảng này. 10 bảng còn lại không dùng; lý do từng bảng ở [#8](synthetic-data-design.md) mục [2.2](synthetic-data-design.md#22-các-bảng) và [6](synthetic-data-design.md#6-giới-hạn-của-dữ-liệu). Trên BigQuery hiện có 9 bảng và 16 view.

**Vì sao dashboard đọc từ view `pbi_*`** thay vì viết truy vấn ngay trong Power BI:

- Một view phục vụ nhiều trang, sửa ở một chỗ.
- Số kiểm chạy thẳng trên BigQuery, không phải mở Power BI.
- Đường đi của mỗi con số đọc được từ đầu đến cuối: nguồn → stg → fct → pbi.

Bốn bảng tĩnh nhỏ (waterfall, SKU chết, lịch khuyến mãi, uplift; 3–27 dòng) được nhập thẳng vào Power BI vì là kết quả phân tích đã chốt, không cần tính lại.

---

## 2. Định nghĩa chỉ số dùng chung

| Chỉ số | Định nghĩa | Nguồn và bộ lọc |
|---|---|---|
| Doanh thu offline | Tiền phiếu bán, cộng phí đổi trả của phiếu trả | `fct_retail_revenue` |
| Doanh thu online | Tiền doanh nghiệp nhận (`business_payment`) của đơn giao thành công | `fct_retail_revenue`. Bỏ dòng "Khách trả lại hàng" |
| Giao dịch | Mỗi dòng `fct_retail_revenue`: phiếu bán, phiếu trả offline, đơn online thành công | `fct_retail_revenue` |
| Doanh số | Giá × số lượng − giảm giá, theo dòng hàng, trước trả hàng | `fct_product_revenue`. Chỉ phiếu bán offline và đơn "Giao hàng tận nhà" |
| Bán thường | Dòng hàng online, hoặc dòng offline thuộc hóa đơn không tiêu điểm | Mẫu số của biên gộp và tỉ lệ giảm giá, vì hóa đơn tiêu điểm ghi giảm giá bằng 0 |
| Hạng lúc mua | Suy ra từ số điểm tích trên mỗi 100.000 đ của phiếu bán: 1, 2, 3, 5, 8 ứng với 5 hạng thẻ | `pbi_giao_dich` |
| Khách định danh | Bỏ 3 tài khoản dùng chung (id 1, 2, 3) | Mọi phân tích theo khách |
| Tỉ lệ hủy, chuyển hoàn | Số đơn trong nhóm ÷ số đơn đặt | `pbi_don_online` |
| Tỉ lệ trả sau giao | Số đơn có phiếu trả ÷ số đơn giao thành công | `pbi_don_online`. Mẫu số khác hai tỉ lệ trên |

Ba cơ chế không thành công của đơn online được giữ riêng, mỗi cơ chế một mẫu số, không cộng thành một tỉ lệ chung.

**Hai con số khác nhau vì khác định nghĩa.** Ở trang Offline, donut hạng thẻ cho tổng 149,9 tỷ, còn KPI doanh thu offline là 150,2 tỷ (T1–T8/2026). Donut chỉ tính phiếu bán xác định được hạng, vì hạng thẻ gắn với lần mua. KPI tính mọi phiếu. Hai số cùng đúng. Phần chênh 275 triệu gồm phí đổi trả của phiếu trả (269 triệu) và phiếu bán dưới 100.000 đ, không suy được hạng (6 triệu).

---

## 3. Mô hình Power BI

| Bảng | Nguồn | Đơn vị một dòng | Số dòng | Nối với (cột khóa) |
|---|---|---|---:|---|
| `F_GiaoDich` | `pbi_giao_dich` | giao dịch | 826.943 | `Date` (`ngay`)<br>`DimDiemBan` (`diem_ban_key`)<br>`DimKenh` (`kenh`) |
| `F_DongHang` | `pbi_dong_hang` | dòng hàng | 1.136.072 | `Date` (`ngay`)<br>`DimSanPham` (`code`)<br>`DimKenh` (`kenh`) |
| `F_DonOnline` | `pbi_don_online` | đơn online gốc | 384.873 | `Date` (`ngay_dat`)<br>`DimDiemBan` (`san`) |
| `F_NgayMua` | `pbi_ngay_mua` | khách định danh × ngày mua | 706.121 | `Date` (`ngay`)<br>`DimKhach` (`customer_id`) |
| `DimKhach` | `pbi_dim_khach` | khách | 39.531 | |
| `DimSanPham` | `pbi_dim_san_pham` | SKU | 7.213 | |
| `DimDiemBan` | `pbi_dim_diem_ban` | cửa hàng và sàn | 36 | |
| `PhiSan` | `dim_platform_fee` | khoảng hiệu lực phí của một sàn | 12 | `DimDiemBan` (`diem_ban_key`) |
| `Date` | tạo trong Power BI | ngày, 2024–2026 | 1.096 | |
| `DimKenh` | tạo trong Power BI | kênh | 2 | |
| `SL_Nam`, `SL_Thang`, `SL_Decile`, 4 bảng tĩnh | tạo trong Power BI | | 3–27 | Không nối |

Dữ liệu nhỏ (bảng lớn nhất khoảng 1,1 triệu dòng) và không thay đổi, nên mô hình dùng **Import mode**. Mọi quan hệ là một-nhiều, một chiều: dim lọc fact.

**Slicer Năm và Tháng không nối quan hệ với bảng nào.** Chart theo tháng phải giữ đủ ba năm và đủ trục T1–T12 khi người xem chọn một năm hoặc một tháng. Nếu slicer lọc thẳng bảng `Date`, chart sẽ mất các năm và tháng còn lại. Vì vậy slicer chỉ được đọc bên trong measure, qua 7 khuôn dùng chung:

| Khuôn | Trả về |
|---|---|
| A · kỳ | Giá trị trong năm và tháng đang chọn; chưa chọn năm thì lấy năm mới nhất có dữ liệu cho các tháng đó (2026, hoặc 2025 nếu chỉ chọn T9–T12) |
| B · năm trước | Cùng kỳ năm trước, chỉ gồm các tháng có dữ liệu ở năm đang xem |
| C · YoY | Tỉ lệ thay đổi so với cùng kỳ năm trước |
| D · MoM | Tỉ lệ thay đổi của tháng cuối được chọn so với tháng liền trước |
| E · nhãn kỳ | Hậu tố tiêu đề: `2025`, `T1–T8/2026`, `T3–T5/2025` |
| F · dòng so sánh | Dòng phụ dưới số KPI và màu ▲/▼ theo tốt/xấu cho kinh doanh |
| G · chart tháng | Chart tháng trang Online chỉ hiện năm đang xem và năm trước |

Khuôn A đặt năm và tháng đang chọn lên bảng `Date`:

```DAX
X · kỳ =
VAR y = [_Năm]                              -- năm đang xem
VAR ThangChon = VALUES ( SL_Thang[Tháng] )  -- tháng đang chọn; chưa chọn = cả 12
RETURN
    CALCULATE ( [X], 'Date'[Năm] = y, TREATAS ( ThangChon, 'Date'[Tháng] ) )
```

Khuôn B giữ cho YoY luôn so cùng kỳ. Năm 2026 có dữ liệu đến T8, nên T1–T8/2026 được so với T1–T8/2025, không so với cả năm 2025:

```DAX
X · năm trước =
VAR y = [_Năm]
VAR ThangChon = VALUES ( SL_Thang[Tháng] )
VAR ThangCoDuLieu =                         -- tháng đang chọn mà năm y có dữ liệu
    CALCULATETABLE ( VALUES ( 'Date'[Tháng] ), REMOVEFILTERS ( 'Date' ),
        'Date'[Năm] = y, 'Date'[Có dữ liệu] = TRUE (), TREATAS ( ThangChon, 'Date'[Tháng] ) )
RETURN
    IF ( y - 1 >= 2024,
         CALCULATE ( [X], 'Date'[Năm] = y - 1, TREATAS ( ThangCoDuLieu, 'Date'[Tháng] ) ) )
```

Mỗi measure trên dashboard ghép từ một khuôn với một measure nền (VD `[Doanh thu]`). Toàn bộ measure nằm trong file `.pbix`, chia thư mục theo khuôn, measure nền, measure theo kỳ, nhãn và màu.

---

## 4. Kiểm số

### 4.1 Ba bước kiểm

Lệch ở bước nào thì dừng ở bước đó.

1. **Mỗi view có số kiểm** chạy trên BigQuery trước khi nạp vào Power BI: số dòng, tổng doanh thu theo kỳ, số giá trị rỗng ở cột khóa. VD `pbi_giao_dich` có 826.943 dòng, doanh thu T1–T8/2026 là 203.716.541.898 đ, cả năm 2025 là 347.528.780.193 đ.
2. **Các con số phải cộng khớp với nhau.** VD hai bước của waterfall 2025 (thay đổi do số giao dịch và do giá trị mỗi giao dịch) cộng lại đúng bằng doanh thu T1–T8/2025: 189.857.630.120 + 17.998.780.358 = 207.856.410.478 đ.
3. **Mỗi trang dashboard** ở trạng thái mặc định (T1–T8/2026) được đối chiếu với số BigQuery. Sau đó thử thêm ba trạng thái: chọn 2024 (không có năm trước), chọn 2025 (cả năm), chọn T3 mà không chọn năm (phải ra T3/2026, MoM so với T2/2026).

### 4.2 Ba lỗi truy vấn không báo lỗi và cách chặn

Ba lỗi dưới đây không làm truy vấn thất bại; chúng chỉ làm số sai. Mỗi lỗi được phát hiện bằng một phép kiểm ở mục 4.1 và được chặn bằng một quy tắc áp cho mọi truy vấn sau đó.

| Lỗi | Phát hiện bằng | Quy tắc chặn |
|---|---|---|
| Join theo `order_id` nhân đôi dòng | So `COUNT(*)` với `COUNT(DISTINCT order_id)`: 417.981 dòng nhưng 384.873 mã đơn. Phiếu trả online dùng lại mã đơn gốc | Khóa của `orders_raw` là `(order_id, order_type)`; mọi join phải kèm `order_type` |
| Doanh số online dư 11,1% | Dựng lại doanh số theo hai cách lọc rồi so | Dòng trả online cũng mang danh sách sản phẩm. Bảng dòng hàng lọc loại phiếu ở cả nhánh offline và online, không chỉ dựa vào danh sách mã đơn hợp lệ |
| Sửa view làm đổi số đã công bố | Trong cùng truy vấn, dựng lại số cũ (cộng lại phần bị loại) | Chỉ thay số trên dashboard khi giải thích được chính xác phần chênh |

---

## Tài liệu nguồn

- [`sql/`](../../sql/): định nghĩa 16 view và 2 bảng dẫn xuất, chạy theo thứ tự số file từ [`01_staging_views.sql`](../../sql/01_staging_views.sql) đến [`05_powerbi_views.sql`](../../sql/05_powerbi_views.sql).
- [`sql/05_powerbi_views.sql`](../../sql/05_powerbi_views.sql): 7 view `pbi_*`, mỗi view có số kiểm.
- [Khuôn DAX thời gian](../dax-time-patterns.md): đủ 7 khuôn measure thời gian, kèm giải thích song ngữ.
- [`dashboard/JM_theme_v1.json`](../../dashboard/JM_theme_v1.json): theme màu của dashboard.
- [`data-generator/generate_data.py`](../../data-generator/generate_data.py), [`data-generator/qa_checks.py`](../../data-generator/qa_checks.py): sinh dữ liệu và kiểm chất lượng.
- [#8 Thiết kế dữ liệu mô phỏng](synthetic-data-design.md): quy tắc sinh dữ liệu và lý do không dùng 10 bảng.
- [#3 Báo cáo insight](insight-report.md): các phát hiện từ dữ liệu.

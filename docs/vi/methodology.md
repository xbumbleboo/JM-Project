# Phụ lục phương pháp — JM Synthetic Data

> **Dữ liệu mô phỏng.** Toàn bộ dữ liệu trong dự án do tác giả tự sinh bằng Python, dựa trên quy mô, chính sách, giá và chương trình khuyến mãi công khai của JM. Đây không phải số liệu thật của JM và không phản ánh tình hình kinh doanh của JM.

*Phiên bản 14/11/2026 · Đi kèm [#3 Báo cáo insight](insight-report.md)*

Tài liệu này trình bày cách đi tới và cách kiểm các kết luận của [#3](insight-report.md), trên cùng bộ dữ liệu và cùng truy vấn.

**Nguyên tắc.** (1) Chỉ gọi một chênh lệch là thật khi vượt rõ mức nhiễu; khi so nhiều nhóm, đếm trước số nhóm vượt ngưỡng do may rủi. Không vượt ngưỡng nghĩa là **chưa đủ bằng chứng**, không chứng minh các nhóm giống nhau. (2) Đo ở đúng đơn vị: biên gộp so trên 600 mẫu, không phải 7.213 SKU, vì giá vốn gán theo mẫu. (3) Mỗi tỉ lệ ghi rõ mẫu số. (4) Kiểm phương pháp trên dữ liệu đã biết đáp án (mục 7).

Bảng tóm tắt xếp mỗi kết luận vào ba mức: **Đã kiểm chứng** (không đổi khi đổi cách tính hợp lý), **Có điều kiện** (đúng trong phạm vi giả định ghi kèm), **Chưa đủ bằng chứng**.

---

## 1. Tách biến động doanh thu

*[#3](insight-report.md) mục [2.1](insight-report.md#21-ít-lượt-mua-hơn-giá-bù-lại) · Doanh thu giảm vì ít lượt mua hay vì giá trị mỗi lượt?*

Doanh thu = số giao dịch (N) × giá trị mỗi giao dịch (A). Thay thế liên hoàn: phần do số giao dịch = (N₁ − N₀) × A₀; phần do giá trị = N₁ × (A₁ − A₀); hai phần cộng đúng bằng tổng thay đổi. Kết quả phụ thuộc thứ tự thay thế, nên tính lại bốn cách (T1–T8/2026 so với cùng kỳ 2025, tỷ đồng):

| Cách tách | Do số giao dịch | Do giá trị mỗi giao dịch |
|---|---:|---:|
| Thay số giao dịch trước (dùng trong [#3](insight-report.md)) | −21,53 | +17,39 |
| Thay giá trị trước | −23,54 | +19,40 |
| Điểm giữa hai thứ tự | −22,53 | +18,39 |
| LMDI (chia theo logarit) | −22,50 | +18,36 |

Kết luận không đổi: giá trị mỗi giao dịch bù 81–82% phần mất do số giao dịch. Không tách tiếp số giao dịch thành số khách × tần suất, vì mục 5 cho thấy cách chia đó chỉ là cơ học.

---

## 2. Hiệu quả khuyến mãi: hồi quy quasi-Poisson theo ngày

*[#3](insight-report.md) mục [4](insight-report.md#4-hiệu-quả-khuyến-mãi--khuyến-mãi-mang-lại-gì) · Mỗi chương trình kéo thêm bao nhiêu hóa đơn và doanh thu so với ngày nền?*

**Mô hình** trên 974 ngày (01/01/2024–31/08/2026): `log E[số hóa đơn bán offline] = năm + tháng + cuối tuần + chương trình`. Ngày nền là ngày không có chương trình. Ngày trùng chương trình gán cho chương trình tác động lớn hơn (13–15/7 thuộc Sinh nhật JM, 16–17/7 thuộc Sale 15/7). "Ra mắt BST mới" phủ kín T10–T12 nên Black Friday đo so với nền đó. Chạy cùng mô hình trên doanh thu phiếu bán và số đơn online.

**Đọc hệ số.** Uplift = e^β − 1. Khoảng tin cậy 95% tính trên thang log: [e^(β − 1,96·SE) − 1 ; e^(β + 1,96·SE) − 1]; [#3](insight-report.md) ghi gọn dạng ± (xấp xỉ delta). Mỗi biến phụ thuộc có 7 hệ số gộp (mô hình chính) và 20 hệ số theo năm (mô hình tương tác, trừ Black Friday 2026); trên cả 54 khoảng, hai cách lệch tối đa 0,6 điểm và không đổi kết luận nào. Thay đổi AOV = (1 + uplift doanh thu) ÷ (1 + uplift hóa đơn) − 1; ví dụ Hot Sale 8/3: 1,162 ÷ 1,442 − 1 = −19,4%.

**Vì sao chọn.** Dạng log cho các tác động nhân với nhau, đúng cách kinh doanh nghĩ ("cuối tuần gấp khoảng 1,35 lần ngày thường"), và tách mùa vụ, cuối tuần, chương trình chồng nhau trong một mô hình. **Quasi-Poisson** vì dữ liệu phân tán hơn Poisson (hệ số phân tán 1,48 với hóa đơn, 2,77 với doanh thu); bỏ bước này khoảng tin cậy hẹp giả tạo. Với doanh thu (biến liên tục), hệ số nhất quán khi dạng trung bình đúng; sai số chuẩn dựa thêm vào giả định phương sai tỉ lệ với trung bình.

**Kiểm thế nào.** Tương tác chương trình × năm (13 tham số thêm): p = 0,28 (hóa đơn), 0,36 (doanh thu), nên [#3](insight-report.md) dùng hệ số gộp. Uplift đơn online cùng chiều, cùng cỡ với offline ở cả 7 chương trình. Mỗi chương trình có 6–96 ngày; Sale 15/7 ít nhất nên khoảng tin cậy rộng nhất (±6,1). Tìm lại hệ số đã cài: mục 7.

**Giới hạn.** Uplift là so với ngày nền, **không** phải doanh thu tăng thêm: khách có thể chỉ dời ngày mua.

---

## 3. Chênh lệch giữa các nhóm: thật hay nhiễu?

*[#3](insight-report.md) mục [2.3](insight-report.md#23-theo-tỉnh-sàn-và-dòng-hàng), [3.1](insight-report.md#31-theo-cửa-hàng-quy-mô-và-sức-mua), [5.2](insight-report.md#52-lý-do-trả-hàng-và-cơ-cấu-hàng-online), [6](insight-report.md#6-sản-phẩm--doanh-số-đến-từ-đâu-trong-danh-mục) · Một cửa hàng, dòng hàng hay BST khác mức chung là thật hay do may rủi?*

Mỗi nhóm đo độ lệch theo sai số chuẩn (z). Với ngưỡng |z| > 2, khoảng 4,6% nhóm vượt dù không có khác biệt (khoảng 1,3 trong 29 cửa hàng). Bốn phép kiểm có giả định sai số khác nhau, nên mỗi phép có một kiểm độ vững riêng.

### 3.1 Tăng giảm theo cửa hàng

Giả định số hóa đơn mỗi năm là Poisson. Kỳ vọng 2026 = số hóa đơn 2025 × mức giảm chung k; z = (n₂₀₂₆ − kỳ vọng) ÷ √(n₂₀₂₆ + n₂₀₂₅ × k²).

- 3/29 cửa hàng vượt 2 sai số chuẩn (|z| lớn nhất 2,69), so với khoảng 1,3 do ngẫu nhiên. Kiểm tổng thể: tổng z² so với χ² 28 bậc tự do (đã trừ 1 vì k ước lượng từ chính các cửa hàng), p ≈ 0,08 năm 2026, 0,18 năm 2025. Đây là xấp xỉ theo giả định Poisson; p-value chỉ mang tính tham khảo.
- Độ nhạy: chia z cho căn hệ số phân tán ước lượng từ chính 29 cửa hàng (1,40 năm 2026, 1,23 năm 2025), còn 1/29 và 0/29 cửa hàng vượt ngưỡng.
- Tăng giảm 2025 và 2026 của cùng cửa hàng tương quan −0,66: giảm thật thì hai năm cùng chiều, tương quan âm là dấu hiệu nhiễu.

Chưa đủ bằng chứng có cửa hàng nào giảm khác mức chung, nên [#3](insight-report.md) không xếp hạng cửa hàng theo tăng trưởng.

### 3.2 AOV theo cửa hàng

Hồi quy log AOV của 29 cửa hàng × 3 năm theo nhóm thị trường, TTTM, trung tâm, Hải Phòng và năm: nhóm 2 thấp hơn nhóm 1 khoảng 12%, nhóm 3 khoảng 24%; TTTM cao hơn khoảng 6%, trung tâm khoảng 4%; Hải Phòng thấp hơn cửa hàng cùng nhóm khoảng 28%. Các đặc điểm giải thích 96,1% khác biệt AOV giữa cửa hàng (81,1% nếu bỏ biến Hải Phòng, vốn chỉ dựa trên 2 cửa hàng).

Ba năm của cùng cửa hàng không độc lập, nên kiểm thêm: phân tích phương sai cửa hàng × năm F(28, 56) = 333; sai số chuẩn phân cụm theo cửa hàng (lớn hơn 1,3–1,8 lần) vẫn cho cả 5 đặc điểm có ý nghĩa, kiểm Wald đồng thời F(5, 28) = 1.046; hồi quy một dòng mỗi cửa hàng cũng vậy. Hệ số yếu nhất là trung tâm (p = 0,012 với sai số phân cụm, 0,017 với hồi quy một dòng mỗi cửa hàng), nên mức +4% nên đọc như xu hướng.

### 3.3 Lý do trả hàng theo sàn

Bảng 7 sàn × 5 lý do (6.408 đơn trả), kỳ vọng mỗi ô theo tỉ trọng lý do toàn online. 0/35 ô vượt 2 sai số chuẩn (so với khoảng 1,6 do ngẫu nhiên). χ² tổng thể: p = 0,86; hoán vị 20.000 lần giữ nguyên tổng theo sàn và theo lý do (vì có ô kỳ vọng dưới 5): p = 0,85; Cramér's V = 0,03. Chưa đủ bằng chứng cơ cấu lý do trả khác nhau giữa các sàn; các sàn khác rõ về *mức* trả hàng.

### 3.4 SKU chết so với tốc độ bán

SKU chết là SKU không bán món nào trong 30 ngày cuối kỳ. Xác suất thô pᵢ = exp(−số dòng bán trong 365 ngày trước × 30/365), cho cả 7.213 SKU; nhân hệ số chung k để tổng kỳ vọng E bằng tổng thực tế (k = 2,99 ở mốc 2025, 2,01 ở mốc 2026). Nhân với k là hiệu chỉnh thực dụng (tháng 8 là mùa thấp, tốc độ bán không đều), nên mô hình chỉ dùng để so giữa các nhóm. z dùng trong kết quả dưới đây tính theo xấp xỉ Poisson: (thực tế − E) ÷ √E. Kiểm độ nhạy bằng phương sai đúng của tổng các biến 0/1, E − k² × Σpᵢ² (mọi k × pᵢ ≤ 0,38): z đổi tối đa 4%, không nhóm nào đổi kết luận so với ngưỡng 2.

Dòng hàng: không nhóm nào |z| > 2 năm 2026 (2025: Phụ kiện +2,07); kiểm tổng thể p = 0,38 (2026) và 0,35 (2025). BST: 18/20 trong 2 sai số chuẩn. BST TẾT vượt rõ (19 so với 6,6; z = +4,82) vì tháng 8 chỉ bán 63,7% mức bình quân của chính nó (các BST khác 80,1%); tính mùa vụ thì kỳ vọng khoảng 16, z ≈ 0,7. BST STREET lệch ngược (z = −2,16), có thể gặp khi so 20 nhóm.

---

## 4. Phép thử nhãn rời bỏ trên nhóm khách cố định

*[#3](insight-report.md) mục [7.2](insight-report.md#72-ranh-giới-thật-mua-một-lần-và-mua-lặp-lại) · Nhãn "có nguy cơ rời bỏ" có cho biết khách nào sẽ không quay lại?*

**Nhãn.** Tỉ số im lặng = số ngày từ lần mua cuối ÷ nhịp mua, với nhịp mua = số ngày từ lần mua đầu đến mốc ÷ số lần mua lặp lại. Khách mua lặp lại (từ 2 ngày mua) xếp vào "đang mua đều" (dưới 1), "có nguy cơ" (1–2), "đã rời" (trên 2).

**Thiết kế.** 35.638 khách định danh có ngày mua đến 31/08/2025, gắn nhãn tại mốc này, theo dõi 12 tháng sau; "quay lại" = có ít nhất một ngày mua có doanh thu.

| Nhóm tại 31/08/2025 | Số khách | Quay lại trong 12 tháng | Doanh thu mỗi khách, 12 tháng |
|---|---:|---:|---:|
| Mua lặp lại, đang mua đều | 18.090 | 85,4% | 9,29 tr |
| Mua lặp lại, "có nguy cơ" | 7.079 | 92,3% | 11,00 tr |
| Mua lặp lại, "đã rời" | 3.514 | 98,0% | 15,86 tr |
| Mới mua một lần¹ | 6.955 | 37,8% | 0,75 tr |

*¹ [#3](insight-report.md) ghi khoảng 36,4–38,3% và 0,72–0,76 tr: hai nhóm con mua lần đầu trong 189 ngày trước mốc (1.756 khách) và trước đó (5.199).*

**Hiệu ứng thành phần.** Nhóm "đã rời" quay lại nhiều hơn vì chứa nhiều khách mua thường xuyên. So trong cùng số lần mua lặp lại, ba nhãn gần như bằng nhau (11–20 lần: 99,7% ở cả ba).

**Lỗi công thức, đúng trên mọi dữ liệu.** Với T là số ngày từ lần mua đầu đến mốc và f là số lần mua lặp lại: tỉ số im lặng = f × (số ngày im lặng ÷ T) ≤ f. Khách quay lại 1–2 lần có tỉ số không quá 2, nên **không bao giờ** vào nhóm "đã rời" (trên 2). Hướng sửa đề xuất, chưa kiểm định trong dự án này: nhịp mua = số ngày giữa lần mua đầu và lần mua cuối ÷ f, để khoảng im lặng không còn bị tính lẫn vào nhịp mua (T hiện gồm cả khoảng im lặng). Nhãn sửa vẫn cần qua đúng phép thử ở trên trước khi dùng.

Dữ liệu không có cơ chế rời bỏ, nên các tỉ lệ quay lại không nói về giữ chân thực tế; điều mang sang dữ liệu thật là phép thử và lỗi công thức.

---

## 5. Mô phỏng tập khách cố định: khách mới giảm 49% có nghĩa là gì?

*[#3](insight-report.md) mục [7.1](insight-report.md#71-số-khách-giảm-ít-nhưng-mỗi-khách-mua-ít-lần-hơn) · Khách mới giảm một nửa có cho thấy thu hút khách kém đi?*

"Khách mới" là khách lần đầu xuất hiện trong dữ liệu (bắt đầu 01/01/2024), nên càng về sau càng ít khách "mới" dù không có gì thay đổi. Phép thử **kiểm một cơ chế của dữ liệu**, không ước lượng số khách thật: không có khách mới nào đến thì số "khách mới" có tự giảm không?

Thiết lập: 75.000 khách có sẵn từ đầu, mỗi khách một trọng số mua Gamma (hình dạng 0,18, trung bình 1), đúng hai tham số của bộ sinh dữ liệu, không chỉnh theo phép thử. Mỗi lượt chọn một khách theo trọng số, có hoàn lại; số lượt bằng số giao dịch khách định danh thật, rút theo 5 đoạn từ T1–T8/2024 (202.848), T9–T12/2024 (125.729), T1–T8/2025 (164.248), T9–T12/2025 (102.253) đến T1–T8/2026 (147.727). Lặp 20 lần (seed 2026); ± là độ lệch chuẩn giữa các lần.

| | Thật¹ | Mô phỏng (không có khách mới) |
|---|---:|---:|
| Số khách T1–T8/2026 | 27.135 | 26.988 ± 133 |
| Khách mới T1–T8/2025 → 2026 | 2.921 → 1.489 (−49,0%) | 2.867 → 1.447 (−49,5%) |

*¹ Đếm theo cùng cách với mô phỏng: khách có ít nhất một giao dịch trong kỳ. KPI dashboard đếm khách có ngày mua có doanh thu (26.827 khách; 1.506 khách mới, −48,9%); chênh 308 khách là những khách mà mọi giao dịch trong kỳ đều có doanh thu bằng 0 (đơn bị trả hết).*

Chạy 200 lần: mức giảm trung bình −49,3%, khoảng phân vị 2,5%–97,5% từ −52,5% đến −46,2%; số khách 26.819–27.223. Cả hai số thật nằm trong các khoảng này. Vì vậy "khách mới −48,9%" **không đủ** để kết luận thu hút khách kém đi.

---

## 6. CLV: BG/NBD và Gamma-Gamma

*[#3](insight-report.md) mục [7.3](insight-report.md#73-tập-trung-doanh-thu-theo-10-khách) · Khách nào có giá trị cao nhất trong 12 tháng tới?*

**Mô hình.** BG/NBD dự báo số lần mua; Gamma-Gamma dự báo giá trị mỗi lần, giả định không phụ thuộc số lần mua. CLV 12 tháng = Σ (tháng i = 1…12) [giá trị mỗi lần × số lần mua dự báo trong tháng i ÷ 1,01^i]; chiết khấu 1%/tháng giảm mức tuyệt đối khoảng 6%, gần như không đổi thứ hạng. Đầu vào: 706.121 ngày mua của 38.446 khách định danh đến 31/08/2026.

**Kiểm tách thời gian.** Ước lượng trên 2024–2025, dự báo T1–T8/2026 cho 36.940 khách đã mua trước kỳ kiểm:

| Năng lực | Chỉ số | Kết quả |
|---|---|---|
| Dự báo mức | Ngày mua dự báo / thực tế | 187.593 / 139.905 (cao hơn 34,1%) |
| Xếp hạng | Spearman, BG/NBD · theo số lần đã mua · theo số ngày im lặng | 0,808 · **0,832** · 0,624 |
| Xếp hạng | Lift 10% cao nhất so với 10% thấp nhất | 57,6 lần; không decile nào đảo thứ tự |
| Giả định Gamma-Gamma | Tương quan số lần mua × giá trị mỗi lần | +0,04 (2026), +0,08 (2025) |

**Đọc kết quả.**
- *Dự báo mức sai, có lời giải thích phù hợp:* cường độ mua toàn hệ thống giảm 24,5% (772,1 xuống 583,0 ngày mua mỗi ngày lịch), trong khi BG/NBD giả định nhịp mua không đổi; riêng mức này tương ứng dự báo cao hơn khoảng 32% (1 ÷ 0,755). Phần còn lại từ 1.193 khách mua một lần cuối kỳ hiệu chỉnh (dự báo 2.427 ngày mua, thực tế 375); bỏ nhóm này, dự báo còn cao hơn 32,7%. Kỳ kiểm chỉ có T1–T8 nên mức giảm có lẫn mùa vụ.
- *Xếp hạng tốt nhưng không hơn cách xếp theo số lần đã mua.*
- *Tham số rời bỏ gần như không xác định được* (a từ 0,0009 sang 0,0023 chỉ đổi log-likelihood 8 trên khoảng 2,2 triệu), nên không dùng xác suất "còn hoạt động".
- *Giả định Gamma-Gamma được ủng hộ* (tương quan dưới 0,1), không phải chứng minh độc lập.

**Kết luận quản trị.** Mô hình **chưa chứng minh được giá trị gia tăng so với xếp theo số lần mua**, nên chưa có cơ sở dùng để phân bổ ngân sách; [#3](insight-report.md) chỉ dùng CLV để mô tả mức tập trung giá trị dự báo.

**Kiểm cài đặt.** Với numpy 2.x, thư viện `lifetimes` trả giá trị rỗng âm thầm cho 1.193 khách, khiến lần chạy đầu ghi mức dự báo dư 32,35% thay vì 34,1%. Mô hình được viết lại bằng scipy theo Fader, Hardie & Lee (2005), kiểm trên bộ CDNOW (ra đúng tham số công bố: r 0,243 · α 4,414 · a 0,793 · b 2,426) và so với bảng CLV gốc (Spearman 0,9998; `models/clv_model.py`).

---

## 7. Dữ liệu mô phỏng thì kiểm được gì?

Dữ liệu sinh từ quy tắc, nên kiểm được điều dữ liệu thật không cho phép: **phương pháp có tìm lại đúng thứ đã cài, và không tìm ra thứ không có?** Mô hình khuyến mãi tìm lại cả 7 hệ số đã cài trong khoảng tin cậy 95% (gộp 2024–2026):

| Chương trình | Hệ số cài | Uplift đo được |
|---|---:|---:|
| Hot Sale 8/3 | +45% | +44,2% ±3,5 |
| Black Friday (so với nền "Ra mắt BST mới") | 1,45 ÷ 1,10 = +31,8% | +32,2% ±2,7 |
| Xả kho cuối năm & Chào Xuân | +30% | +30,2% ±3,2 |
| Sinh nhật JM | +25% | +23,2% ±2,3 |
| 30/4 – 1/5 | +25% | +23,0% ±2,8 |
| Sale giữa tháng 15/7 | +20% | +18,0% ±6,1 |
| End of Season | +15% | +15,6% ±2,3 |

Theo năm, 19/20 ô chứa hệ số cài (ngoài: 30/4 – 1/5 năm 2024, +19,5% ±4,3), đúng mức kỳ vọng của khoảng 95%. Đây là **một lần sinh dữ liệu** (seed 42), chưa phải nghiên cứu độ phủ. Nhãn rời bỏ (mục 4) và mức giảm khách mới (mục 5) trông như tín hiệu thật nhưng đều được giải thích bằng cơ chế khác. Tìm lại đúng hệ số chỉ cho thấy phương pháp đúng **khi mô hình khớp cách dữ liệu được sinh**.

---

## Tóm tắt

| Phương pháp | [#3](insight-report.md) | Kết luận | Mức | Chưa đủ bằng chứng để nói |
|---|---|---|---|---|
| Thay thế liên hoàn | 2.1 | Giá trị mỗi giao dịch bù 81–82% phần mất do số giao dịch | Đã kiểm chứng | Phần do số khách, phần do tần suất |
| Quasi-Poisson theo ngày | 4 | Uplift so với ngày nền | Có điều kiện | Doanh thu tăng thêm thật |
| So với nhiễu: AOV theo cửa hàng | 3.1 | AOV khác thật theo đặc điểm cửa hàng | Đã kiểm chứng | Mức +4% của trung tâm là chính xác |
| So với nhiễu: các phép kiểm không phát hiện khác biệt | 2.3, 3.1, 5.2, 6 | Không phát hiện khác biệt vượt nhiễu (trừ BST TẾT, do mùa vụ) | Chưa đủ bằng chứng về khác biệt | Xếp hạng theo tăng trưởng; các nhóm giống nhau |
| Phép thử nhóm cố định | 7.2 | Nhãn rời bỏ không thêm thông tin ngoài số lần mua; công thức có lỗi | Đã kiểm chứng | Tỉ lệ giữ chân thực tế |
| Mô phỏng đối chứng | 7.1 | Mức giảm khách mới tái tạo được không cần khách mới | Đã kiểm chứng | Thu hút khách tốt lên hay kém đi |
| BG/NBD + Gamma-Gamma | 7.3 | Xếp hạng dùng được, ngang xếp theo số lần mua | Có điều kiện | Mô hình hơn baseline; giá trị tuyệt đối |

## Áp vào doanh nghiệp thật

| Phương pháp | Điều nên làm |
|---|---|
| Tách biến động | Ghi thứ tự thay thế hoặc dùng LMDI; tách thêm theo kênh, cơ cấu sản phẩm |
| Uplift khuyến mãi | Thêm lễ âm lịch, thời tiết, ngân sách quảng cáo; đo doanh thu tăng thêm bằng nhóm cửa hàng đối chứng (difference-in-differences) |
| So với nhiễu | Ngưỡng cảnh báo theo sai số chuẩn, ước lượng dao động từ dữ liệu lịch sử; kiểm năm trước (vấn đề thật lặp lại, nhiễu đảo chiều); loại BST trái mùa khỏi cảnh báo SKU chết |
| Nhãn rời bỏ | Gắn nhãn tại mốc quá khứ, xem 12 tháng sau, so trong cùng số lần mua, trước khi chi ngân sách |
| Khách mới | Định nghĩa bằng cửa sổ nhìn lại (ví dụ 24 tháng không mua) |
| CLV | Kiểm tách thời gian, đo riêng dự báo mức và xếp hạng, luôn so với xếp theo số lần mua |

## Thuật ngữ

**Ngày nền:** ngày không có khuyến mãi, mốc đo uplift. **Hệ số phân tán:** Pearson χ² ÷ bậc tự do, bằng 1 nếu dữ liệu đúng Poisson. **LMDI:** tách biến động theo logarit, không phụ thuộc thứ tự. **Sai số chuẩn phân cụm:** có tính đến việc quan sát cùng một cửa hàng không độc lập. **Lift theo decile:** tỉ số giá trị thực tế giữa 10% xếp cao nhất và 10% thấp nhất.

## Nguồn

Mã trong repo: `models/promo_uplift.py` (mục 2, 7), `models/clv_model.py` (mục 6), `sql/03_derived_tables.sql` và `sql/04_analysis_views.sql`. Các truy vấn kiểm riêng của báo cáo và script mô phỏng mục 5 không đưa vào repo; mục 5 ghi đủ tham số để dựng lại. Liên quan: [#3 Báo cáo insight](insight-report.md) · [#6 Tài liệu kỹ thuật](technical-notes.md) · [#8 Thiết kế dữ liệu mô phỏng](synthetic-data-design.md).

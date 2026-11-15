# Báo cáo insight — JM Synthetic Data

> **Dữ liệu mô phỏng.** Toàn bộ số liệu trong tài liệu này là dữ liệu mô phỏng, do tác giả tự sinh bằng Python dựa trên quy mô, chính sách, giá và chương trình khuyến mãi công khai của JM. Đây không phải số liệu thật của JM và không phản ánh tình hình kinh doanh của JM.

*Bản 14/11/2026 · Dataset v3.1 · Đi kèm dashboard Power BI (6 trang chính và 2 trang chi tiết)*

---

## 0. Cách đọc báo cáo

- **Kỳ.** Dữ liệu từ 01/01/2024 đến 31/08/2026. Phép so sánh chính là T1–T8/2026 với cùng kỳ T1–T8/2025.
- **Doanh thu và Doanh số.** Doanh thu là tiền thu về sau khi trừ hàng khách trả lại. Doanh số là giá trị các dòng hàng đã bán (giá sau giảm giá), chưa trừ hàng trả lại, dùng ở phần sản phẩm. Hai số không đặt cạnh nhau (T1–T8/2026: doanh thu 203,7 tỷ, doanh số 215,2 tỷ).
- **Mẫu số.** Phần kinh doanh tính trên toàn bộ giao dịch, gồm 3 tài khoản khách dùng chung. Phần khách hàng (mục 7) chỉ tính khách định danh.
- **Định dạng.** Dấu phẩy thập phân, dấu chấm hàng nghìn (203,7 tỷ; 164.384). Ảnh dashboard hiển thị ngược lại do định dạng vùng của Windows. *tỷ* = tỷ đồng, *tr* = triệu đồng, *điểm* = điểm phần trăm; ▲/▼ so với cùng kỳ năm trước.
- **Nhiễu.** Chênh lệch có thể xuất hiện ngay cả khi không có gì thay đổi thật, chỉ vì số đơn mỗi ngày, mỗi năm tự lên xuống; nhóm càng nhỏ dao động càng rộng. Báo cáo chỉ gọi một chênh lệch là có thật khi nó vượt rõ mức này.
- **Ô "Cách đọc"** ghi định nghĩa, chênh lệch nào chỉ là nhiễu, và câu "vì sao" nào dữ liệu chưa trả lời được. Cách kiểm chi tiết ở **[#5 Phụ lục phương pháp](methodology.md)**. Bảng đối chiếu từng phát hiện với quy tắc tạo dữ liệu đứng sau nó ở **[#8 Thiết kế dữ liệu mô phỏng](synthetic-data-design.md)**.
- **Cấp phân tích.** Mục 2–7 mô tả và chẩn đoán; mục 8 dự đoán và đề xuất.

---

## 1. Tóm tắt cho lãnh đạo

**Doanh thu T1–T8/2026 đạt 203,7 tỷ, giảm 2,0%, sau khi đã giảm 11,0% ở T1–T8/2025. Khách mua ít lượt hơn (số giao dịch ▼ 10,4%); giá bán tăng bù lại phần lớn.**

**Bốn phát hiện chính**

1. **Khuyến mãi kéo thêm lượt mua nhưng trả giá bằng giá trị đơn.** Số hóa đơn tăng 15,6–44,2% trong ngày khuyến mãi, nhưng nhìn chung giảm giá càng sâu thì AOV càng giảm. End of Season thêm 15,6% hóa đơn mà doanh thu chỉ thêm 2,6%. Chương trình có điều kiện số lượng (Black Friday) giữ AOV tốt nhất, vì khách gom thêm món (mục 4).
2. **TikTok Shop để mất gần một nửa đơn đặt.** Cứ 100 đơn đặt chỉ 48 đơn còn doanh thu, so với 66 của toàn online: chuyển hoàn gấp khoảng 2 lần các sàn khác và tỉ lệ trả toàn phần cao nhất; sàn này cũng có phí cao nhất (mục 5).
3. **Điểm nghẽn về khách là lần mua thứ hai, không phải khách lâu không mua.** Khách đã mua lặp lại quay lại 85–98% trong 12 tháng, kể cả nhóm bị dán nhãn "đã rời". Khách chỉ mới mua một lần quay lại khoảng 37% (mục 7.2).
4. **Doanh thu tập trung ở hai chỗ.** Hà Nội chiếm 70,2% doanh thu offline; 10% khách chi nhiều nhất tạo 40,9% doanh thu khách định danh (mục 3, 7).

*Bối cảnh:* mức giảm so với cùng kỳ phân bổ đều. Cả 29 cửa hàng đều giảm số hóa đơn; 7 sàn, 7 dòng hàng và 20 BST đều thay đổi trong biên độ hẹp quanh mức chung, không nhóm nào giảm khác hẳn (mục 2–6). TikTok Shop là vấn đề về mức, đã có từ năm trước, không phải về đà giảm.

**Dự đoán.** Nếu xu hướng 2026 lặp lại, doanh thu T1–T8/2027 khoảng 199,7 tỷ (▼ 2,0%); nếu giá ngừng tăng, chỉ còn 182,6 tỷ (▼ 10,4%) (mục 8.1).

**Ba đề xuất ưu tiên** (bảng ưu tiên đầy đủ ở mục 8.2)

1. **Lấy số lượt mua làm chỉ tiêu chính,** tăng số món mỗi hóa đơn bằng bán kèm, và dồn ngân sách giữ chân vào lần mua thứ hai của khách mới. Tăng UPT offline thêm 0,02–0,05 món: +1,8 đến +4,4 tỷ mỗi kỳ.
2. **Đánh giá mọi sàn trên doanh thu sau trả và sau phí; ưu tiên giảm chuyển hoàn, trả hàng ở TikTok Shop và trả hàng vì sai size.** Thu hẹp 25–50% khoảng cách của TikTok Shop với Shopee: +0,9 đến +1,8 tỷ mỗi kỳ trước phí sàn (+0,7 đến +1,5 tỷ sau phí).
3. **Đánh giá khuyến mãi bằng doanh thu, thử cơ chế "mua nhiều giảm thêm".** Riêng End of Season offline: +0,6 đến +1,2 tỷ mỗi năm.

---

## 2. Tổng quan — doanh thu thay đổi vì đâu?

*Trang dashboard: TỔNG QUAN*

| | T1–T8/2024 | T1–T8/2025 | T1–T8/2026 | 2026 so với 2025 |
|---|---:|---:|---:|---:|
| Doanh thu | 233,4 tỷ | 207,9 tỷ | 203,7 tỷ | ▼ 2,0% |
| Giao dịch | 225.457 | 183.378 | 164.384 | ▼ 10,4% |
| Giá trị mỗi giao dịch | 1.035.335 đ | 1.133.486 đ | 1.239.272 đ | ▲ 9,3% |
| Số lượng bán (món) | 362.897 | 293.656 | 263.962 | ▼ 10,1% |
| Tỉ trọng online trên tổng doanh thu | 26,3% | 26,1% | 26,3% | ▲ 0,2 điểm |

Cả năm: 2024 là 389,4 tỷ, 2025 là 347,5 tỷ (▼ 10,8%).

### 2.1 Ít lượt mua hơn, giá bù lại

| Biến động doanh thu (T1–T8) | 2025 so với 2024 | 2026 so với 2025 |
|---|---:|---:|
| Do số giao dịch | −43,6 tỷ | −21,5 tỷ |
| Do giá trị mỗi giao dịch | +18,0 tỷ | +17,4 tỷ |
| Tổng thay đổi | −25,6 tỷ | −4,1 tỷ |
| Phần giá trị mỗi giao dịch bù lại | 41% | 81% |

*Tách bằng phương pháp thay thế liên hoàn, thay số giao dịch trước; cách tách và độ nhạy theo thứ tự ở [#5](methodology.md).*

- **Ít lượt mua hơn, không ít món hơn mỗi lượt.** Số giao dịch và số món cùng giảm khoảng 10%; số món mỗi giao dịch giữ 1,61 · 1,60 · 1,61 qua ba năm (UPT phiếu bán offline 1,70 · 1,69 · 1,70).
- **Giá trị mỗi giao dịch tăng vì giá.** Giá trung bình mỗi món tăng 9,0% (747.849 → 815.191 đ).
- **Đà giảm chậm lại vì số giao dịch giảm chậm hơn** (▼ 18,7% rồi ▼ 10,4%), không vì giá trị đơn tăng nhanh hơn (▲ 9,5% rồi ▲ 9,3%). Mất ít hơn không có nghĩa là tăng trưởng: doanh thu vẫn giảm ở cả hai năm.
- **Tỉ trọng online đứng yên quanh 26%.** Offline giảm 2,3%, online giảm 1,2%; khoảng chênh quá nhỏ để kết luận kênh online giữ tốt hơn.

> **Cách đọc.** Không trình bày phần tăng giá trị mỗi giao dịch như thành tích bán hàng. Dữ liệu chưa trả lời được số giao dịch giảm vì mất khách, vì khách mua thưa hơn hay vì thiếu khách mới; phần này cần dữ liệu lượt khách (mục 7.1, 8.4).

### 2.2 Theo tháng

- **Ba năm cùng một hình dạng:** đỉnh T1 (18,7% doanh thu T1–T8/2026), đáy T2 (8,3%), tăng dần đến T5, giảm ở T6–T7.
- **Năm 2026 thấp hơn 2025 ở 7/8 tháng** (▼ 0,2% ở T2 đến ▼ 5,3% ở T6); chỉ T8 cao hơn (▲ 0,6%). Số giao dịch thấp hơn ở cả 8 tháng (▼ 8,7% đến ▼ 13,3%).

> **Cách đọc.** Đáy luôn ở T2 dù Tết rơi vào 10/02/2024, 29/01/2025 hay 17/02/2026, nên chưa gắn đáy T2 với kỳ nghỉ Tết khi chưa xem doanh thu theo ngày. Không kết luận "đà giảm đang thu hẹp" từ một tháng T8: số giao dịch T8 vẫn giảm 8,7%.

### 2.3 Theo tỉnh, sàn và dòng hàng

**Mọi nhóm đều thay đổi, nhưng không nhóm nào lệch hẳn khỏi mức chung ▼ 2,0%:**

| Chart | Nhóm lớn nhất | Mức thay đổi |
|---|---|---|
| Doanh thu theo tỉnh/thành | Hà Nội ▼ 2,4% · TP. Hồ Chí Minh 0,0% · Hải Phòng ▼ 3,4% | ▼ 3,4% → 0,0% |
| Doanh thu theo sàn | 7 sàn | ▼ 2,6% (Lazada) → ▲ 1,8% (Instagram) |
| Doanh số theo dòng hàng | 7 dòng hàng | ▼ 2,6% (Set bộ) → ▼ 1,6% (Quần) |

- **Offline tập trung cao:** Hà Nội chiếm 70,2% doanh thu offline từ 11/29 cửa hàng; ba tỉnh đầu chiếm 85,2%.
- **Online phân tán hơn:** ba sàn đầu (Facebook 24,0%, Shopee 21,1%, TikTok Shop 18,1%) chiếm 63,2%; không sàn nào vượt 24%.
- **Áo khoác và Set bộ chiếm 58,6% doanh số vì giá cao,** không phải vì bán nhiều món hơn hẳn: hai dòng này chỉ chiếm 37,9% số món, giá trung bình 1,36 tr và 1,16 tr mỗi món. **Phụ kiện thì ngược lại:** đứng thứ ba về số món (14,2%) nhưng cuối về doanh số (4,5%), giá khoảng 259 nghìn mỗi món.

> **Cách đọc.** Tỉnh ít cửa hàng có thể dao động rộng hơn vì nền số nhỏ (Hải Dương ▼ 15,5%, Ninh Bình ▼ 9,4%, Đồng Nai ▲ 3,8%), dù nhiều tỉnh một cửa hàng vẫn nằm gọn quanh mức chung (Thái Bình ▲ 0,4%, Thanh Hóa ▼ 1,7%). Phép thử theo cửa hàng ở [#5](methodology.md) cho thấy các chênh lệch này nằm trong mức nhiễu; không xếp hạng tỉnh theo tăng trưởng.

---

## 3. Offline — doanh thu nằm ở đâu trong chuỗi cửa hàng?

*Trang dashboard: OFFLINE*

| | T1–T8/2026 | So với T1–T8/2025 |
|---|---:|---:|
| Doanh thu | 150,2 tỷ | ▼ 2,3% |
| Số hóa đơn bán | 103.238 | ▼ 10,7% |
| AOV (giá trị mỗi hóa đơn bán) | 1.452.154 đ | ▲ 9,4% |
| UPT (số món mỗi hóa đơn bán) | 1,70 | 2025: 1,69 · 2024: 1,70 |
| Tỉ lệ chiết khấu | 17,45% | không so |

**Ít lượt mua hơn, giỏ hàng giữ nguyên.** Giá sản phẩm tăng bao nhiêu thì AOV tăng xấp xỉ bấy nhiêu (khoảng 9% và 9,4%); UPT giữ 1,69–1,70 qua ba năm. Phần dữ liệu trả lời được là **cấu trúc** doanh thu offline, và cấu trúc này đứng yên qua ba năm.

> **Cách đọc.** AOV và UPT tính trên phiếu bán, khác "giá trị mỗi giao dịch" ở mục 2 (gồm cả phiếu trả). Tỉ lệ chiết khấu = tiền giảm giá ÷ giá trị hàng trước giảm giá, chỉ trên hóa đơn không dùng điểm tích lũy: hóa đơn dùng điểm ghi giảm giá bằng 0 kể cả ngày khuyến mãi, tính vào sẽ kéo tỉ lệ thấp giả tạo. Phần được tính chiếm 79,7% doanh số offline.

### 3.1 Theo cửa hàng: quy mô và sức mua

- **Tập trung ở Hà Nội.** Năm cửa hàng đầu chiếm 40,9% doanh thu offline, mười cửa hàng đầu (đều ở Hà Nội) chiếm 66,4%; cửa hàng đầu bảng bán gấp 16,8 lần cửa hàng cuối bảng.
- **Quy mô theo nhóm thị trường.** Mỗi cửa hàng nhóm 1 (Hà Nội) bán bình quân 9,58 tỷ, nhóm 2 (TP. Hồ Chí Minh, Hải Phòng, Đà Nẵng) 4,26 tỷ, nhóm 3 (11 tỉnh còn lại, 12 cửa hàng) 1,60 tỷ. Tỉ trọng Hà Nội giữ 70,1–70,3% trong ba năm.
- **Thứ hạng gần như không đổi:** không cửa hàng nào đổi quá 2 bậc từ 2024 đến 2026. Xếp hạng là thông tin về quy mô, không phải bảng chấm điểm quản lý.
- **AOV khác nhau thật giữa các cửa hàng và đi theo đặc điểm cửa hàng.** AOV 2026 trải từ 946.833 đ (JM HP 02) đến 1.692.146 đ (JM HN 06), chênh 1,79 lần. So trong cùng điều kiện khác: nhóm 2 thấp hơn nhóm 1 khoảng 12%, nhóm 3 thấp hơn khoảng 24%; cửa hàng trong trung tâm thương mại cao hơn khoảng 6%, ở khu trung tâm cao hơn khoảng 4%; hai cửa hàng Hải Phòng thấp hơn cửa hàng cùng nhóm khoảng 28%. Các yếu tố này giải thích khoảng 96% khác biệt AOV giữa cửa hàng; con số cao một phần vì yếu tố Hải Phòng chỉ dựa trên 2 cửa hàng, gần như hiệu ứng riêng của hai cửa hàng đó; bỏ yếu tố này thì còn khoảng 81%. UPT gần như như nhau (1,60–1,73), nên khác biệt nằm ở giá món khách chọn.

> **Cách đọc.** Cột YoY từng cửa hàng không đọc thành thành tích: chênh lệch nằm trong mức nhiễu. Năm 2026, 3/29 cửa hàng có số hóa đơn lệch quá 2 sai số chuẩn so với mức giảm chung, trong khi chỉ do ngẫu nhiên đã kỳ vọng khoảng 1–2 cửa hàng; cửa hàng giảm mạnh năm nay thường là cửa hàng giảm nhẹ năm trước (tương quan YoY hai kỳ −0,66), dấu hiệu của dao động ngẫu nhiên chứ không phải xu hướng riêng ([#5](methodology.md)). Cả 29 cửa hàng đều giảm số hóa đơn, tăng AOV ở cả hai năm. Chart AOV cho biết sức mua mỗi lượt, không phải năng lực bán hàng của nhân viên; dữ liệu chưa cho biết vì sao Hải Phòng thấp hơn hẳn. Nhóm thị trường là cách JM phân bổ nguồn lực, không phải nguyên nhân doanh thu.

### 3.2 Thời điểm bán

- **AOV thấp hơn ở tháng có khuyến mãi dài:** T1 bằng 0,93 lần AOV cả kỳ, T7 bằng 0,96 lần; các tháng không có hoặc chỉ vài ngày khuyến mãi (T2; T4 và T5 có 7 ngày của đợt 30/4 – 1/5) cao hơn khoảng 1,06 lần (đo cụ thể ở mục 4).
- **Cuối tuần:** doanh thu bình quân mỗi ngày 753 tr (T7) và 766 tr (CN), so với 552–570 tr ngày thường, khoảng 1,34–1,37 lần. Cuối tuần chiếm 28,8% số ngày nhưng tạo 35,4% doanh thu offline. Năm ngày thường chênh nhau 2–4%, không xếp hạng.

### 3.3 Theo hạng thẻ

| Hạng thẻ lúc mua | Tỉ trọng doanh thu | AOV | Hóa đơn mỗi khách |
|---|---:|---:|---:|
| Khách lẻ (3 tài khoản dùng chung) | 7,6% | 1.398.407 đ | — |
| Member | 19,6% | 1.432.799 đ | 1,5 |
| Silver | 26,8% | 1.461.292 đ | 3,0 |
| Gold | 17,4% | 1.469.832 đ | 4,4 |
| Platinum | 14,9% | 1.459.525 đ | 6,9 |
| Diamond | 13,7% | 1.470.659 đ | 14,3 |

*T1–T8/2026; tỉ trọng trên doanh thu phiếu bán offline 149,9 tỷ; hạng thẻ tại thời điểm mua, nên một khách có thể nằm ở nhiều hạng.*

**Khác biệt giữa các hạng nằm ở số lần mua, không ở giá trị mỗi lần.** AOV của 5 hạng thẻ gần như bằng nhau (1,43–1,47 tr); Diamond chỉ có 978 khách (từng mua ở hạng Diamond trong kỳ; khác số 694 khách Diamond tại ngày 31/08/2026 ở mục 7.4) nhưng tạo 13,7% doanh thu phiếu bán vì mỗi khách mua bình quân 14,3 lần trong kỳ.

> **Cách đọc.** Hạng thẻ xét bằng chính chi tiêu 365 ngày, nên "hạng cao chi nhiều hơn" là định nghĩa, không phải phát hiện. Năm 2024 hạng lệch về Member vì dữ liệu bắt đầu 01/01/2024.

---

## 4. Hiệu quả khuyến mãi — khuyến mãi mang lại gì?

*Trang dashboard: HIỆU QUẢ KM*

T1–T8/2026 có 100 ngày khuyến mãi trên 243 ngày; các ngày này tạo 45,0% doanh thu offline và 48,5% số hóa đơn bán offline của kỳ (cùng kỳ 2025: 44,7% và 48,1%).

| Chương trình | Thời gian | Giảm thêm | Uplift số hóa đơn | Uplift doanh thu | Thay đổi AOV | Uplift đơn online |
|---|---|---:|---:|---:|---:|---:|
| Hot Sale 8/3 | 1/3–8/3 | 20% | +44,2% ±3,5 | +16,2% ±3,5 | −19,4% | +44,2% |
| Black Friday¹ | 30/10–13/11² | 30%; hóa đơn từ 4 món giảm tối thiểu 15%² | +32,2% ±2,7 | +25,5% ±3,0 | −5,1% | +31,7% |
| Xả kho & Chào Xuân | 1/1–25/1 | 15% | +30,2% ±3,2 | +10,1% ±3,2 | −15,5% | +30,4% |
| Sinh nhật JM | 20/6–15/7 | 15% | +23,2% ±2,3 | +8,5% ±2,4 | −11,9% | +26,7% |
| 30/4 – 1/5 | 27/4–3/5 | 10% | +23,0% ±2,8 | +12,6% ±3,1 | −8,4% | +24,4% |
| Sale giữa tháng 15/7 | 16/7–17/7 | 10% | +18,0% ±6,1 | +10,2% ±6,8 | −6,7% | +17,0% |
| End of Season | 20/7–20/8 | 15% | +15,6% ±2,3 | +2,6% ±2,4 | −11,2% | +14,5% |

*Gộp 2024–2026; ± là nửa độ rộng khoảng tin cậy 95% (xấp xỉ; khoảng chính xác ở [#5](methodology.md) mục [2](methodology.md#2-hiệu-quả-khuyến-mãi-hồi-quy-quasi-poisson-theo-ngày)); so với ngày thường cùng tháng, cùng năm, cùng loại ngày. ¹ Chỉ có 2024–2025, đo so với nền "Ra mắt BST mới" (phủ kín T10–T12). ² Theo quy tắc của dữ liệu mô phỏng. Chương trình công khai của JM khác: năm 2024 chạy 12–21/11 với mua 2 giảm 10%, mua 3 giảm 15%; năm 2025 mua 2 giảm 5%, mua 3 giảm 10%, mua 4 giảm 15%; cả hai năm có giảm đến 70% và đồng giá từ 111 nghìn. Phần lệch này ghi ở [#8](synthetic-data-design.md). Ảnh tĩnh của dashboard chỉ hiện 5/7 dòng; bảng đủ ở đây.*

- **Mọi chương trình đổi giá trị đơn lấy lượt mua, và nhìn chung giảm càng sâu AOV càng giảm:** giảm thêm 10% làm AOV giảm 6,7–8,4%; 15% giảm 11,2–15,5%; 20% giảm 19,4%. Chỉ có 7 điểm đo và cùng mức 15% đã dao động khá rộng, nên đây là xu hướng, không phải tỉ lệ cố định. Uplift doanh thu vì vậy luôn thấp hơn uplift số hóa đơn; End of Season (+15,6% hóa đơn, +2,6% doanh thu) vừa sát ngưỡng có ý nghĩa.
- **Cơ chế có điều kiện số lượng giữ AOV tốt nhất:** Black Friday chỉ làm AOV giảm 5,1% dù giảm thêm sâu nhất. Khách gom thêm món: UPT trong cửa sổ Black Friday là 2,11, so với 1,71 ở các ngày T10–T12 còn lại (2024–2025).
- **Ổn định qua các năm** (khác biệt giữa 2024, 2025, 2026 không vượt nhiễu: p = 0,28 với số hóa đơn, 0,36 với doanh thu) và **tác động cả chuỗi:** uplift đơn online cùng chiều, cùng cỡ với offline; lệch lớn nhất ở Sinh nhật JM (online +26,7%, offline +23,2% ±2,3).

> **Cách đọc.** Không xếp hạng Black Friday với 6 chương trình còn lại theo doanh thu vì nền so sánh khác. Uplift so với ngày thường không chứng minh doanh thu cả năm tăng thêm đúng mức đó, vì một phần khách có thể chỉ dời ngày mua; muốn biết phần tăng thêm thật cần một nhóm đối chứng không chạy chương trình. Uplift đo bằng hồi quy quasi-Poisson theo ngày, tách mùa vụ, cuối tuần và các chương trình chồng nhau ([#5](methodology.md)).

---

## 5. Online — doanh thu online mất đi ở đâu?

*Trang dashboard: ONLINE và trang chi tiết TRẢ HÀNG THEO SÀN*

| | T1–T8/2026 | So với T1–T8/2025 |
|---|---:|---:|
| Doanh thu | 53,5 tỷ | ▼ 1,2% |
| Đơn đặt | 76.769 | ▼ 9,5% |
| Giao thành công | 56.694 | ▼ 9,5% |
| Còn doanh thu sau trả | 50.583 | ▼ 9,3% |
| AOV online | 1.058.265 đ | ▲ 8,9% |

Một đơn online đi qua ba bước: **đặt đơn** → **giao thành công** (không bị hủy, không bị chuyển hoàn) → **còn doanh thu** (khách không trả lại toàn bộ; đơn trả một phần vẫn còn doanh thu).

**Đơn giảm từ đầu, không rơi rụng thêm ở các bước sau.** Giao thành công ÷ đơn đặt giữ 73,85% ở cả hai năm; còn doanh thu ÷ giao thành công là 89,22% (2025: 89,06%). AOV online tăng 8,9%, cùng cỡ mức tăng giá.

> **Cách đọc.** AOV online = doanh thu online ÷ số đơn còn doanh thu, không đặt cạnh AOV offline hay giá trị mỗi giao dịch ở mục 2.

### 5.1 TikTok Shop tách hẳn khỏi các sàn khác

| Sàn | Còn doanh thu | Hủy | Chuyển hoàn | Trả toàn phần |
|---|---:|---:|---:|---:|
| Admin | 77,22% | 10,27% | 11,75% | 0,76% |
| Website | 72,66% | 9,75% | 12,03% | 5,57% |
| Instagram | 72,15% | 10,26% | 11,46% | 6,12% |
| Facebook | 71,66% | 10,56% | 12,04% | 5,74% |
| Lazada | 70,09% | 10,89% | 11,90% | 7,12% |
| Shopee | 69,08% | 10,02% | 12,37% | 8,53% |
| **TikTok Shop** | **48,24%** | **12,71%** | **25,08%** | **13,97%** |
| Toàn online | 65,89% | 10,90% | 15,25% | 7,96% |

*% trên số đơn đặt, T1–T8/2026.*

- Sáu sàn giữ được 69–77% đơn đặt thành doanh thu; **TikTok Shop chỉ 48,2%**, vì chuyển hoàn (25,1%) gấp khoảng 2 lần các sàn khác (11,5–12,4%) và trả toàn phần (14,0%) cao nhất. Tính trên đơn đã giao thành công, TikTok Shop giữ 77,5% đơn, toàn online 89,2%.
- Theo giá trị, TikTok Shop mất 22,4% giá trị đơn đã giao vì trả hàng (Shopee 11,1%, Facebook 7,5%, toàn online 10,8%).
- **Tình trạng ổn định:** so với cùng kỳ, các tỉ lệ của TikTok Shop thay đổi dưới 1 điểm; tỉ lệ hủy cao hơn toàn online ở cả 8 tháng năm 2026.
- TikTok Shop cũng có **phí theo % cao nhất**: phí giao dịch 6% + hoa hồng 12,5%, cộng 3.000 đ/đơn (Shopee 6% + 3%¹; Lazada 4% + 3,99%, cộng 2.000 đ/đơn; Facebook, Instagram, Website, Admin không có phí sàn).

*¹ Hoa hồng Shopee là suy luận, chưa xác nhận từ nguồn công khai.*

> **Cách đọc.** Ba tỉ lệ dùng ba mẫu số: hủy và chuyển hoàn chia đơn đặt; trả sau giao chia đơn giao thành công (TikTok Shop 23,6%); trả theo giá trị chia giá trị đơn đã giao, gồm phí ship (22,4%). Điểm trả hàng T8/2026 trên trang chi tiết để trống vì nhiều đơn chưa hết hạn trả. Doanh thu online trong dữ liệu ghi theo cùng một tỉ lệ trên giá trị đơn ở mọi sàn, chưa trừ phí thực tế; báo cáo không so lợi nhuận giữa các sàn.

### 5.2 Lý do trả hàng và cơ cấu hàng online

| Lý do trả (6.408 đơn, T1–T8/2026) | Sai size | Không như mô tả | Lỗi sản phẩm | Thất lạc vận chuyển | Giao nhầm |
|---|---:|---:|---:|---:|---:|
| Tỉ trọng | 65,7% | 14,5% | 10,2% | 5,1% | 4,6% |

- **Gần hai phần ba đơn trả là do sai size;** lỗi sản phẩm và giao nhầm cộng lại 14,8%. **Lý do như nhau ở mọi sàn:** có sàn bị trả nhiều, có sàn bị trả ít, nhưng cơ cấu lý do không khác (0/35 ô sàn × lý do lệch quá 2 sai số chuẩn).
- **Online bán ít hàng giá cao hơn:** Áo khoác chiếm 27,3% và Set bộ 24,8% doanh số online, thấp hơn mức chung (32,1% và 26,6%).

> **Cách đọc.** Lý do trả không khác theo sản phẩm, nên không xếp hạng sản phẩm theo lý do trả. Lý do hủy phân bố đều trên 16 mã ở mọi sàn, không có hình dạng để phân tích. Câu "vì sao online bán ít hàng giá cao", chẳng hạn món đắt cần thử trực tiếp, chưa kiểm được bằng dữ liệu bán hàng.

---

## 6. Sản phẩm — doanh số đến từ đâu trong danh mục?

*Trang dashboard: SẢN PHẨM và trang chi tiết CHI TIẾT BST*

| | T1–T8/2026 | So với T1–T8/2025 |
|---|---:|---:|
| Doanh số | 215,2 tỷ | ▼ 2,0% |
| Số lượng bán | 263.962 món | ▼ 10,1% |
| Biên gộp | 60,25% | không so |
| Tỉ lệ giảm giá | 17,56% | không so |
| SKU chết (không bán món nào trong 30 ngày cuối kỳ) | 261 | ▲ 60 (2025: 201) |

- **Mọi dòng hàng và BST giảm cùng nhịp,** không nhóm nào thay đổi khác hẳn mức chung. Thứ hạng doanh số theo dòng hàng gần như là thứ hạng giá (mục 2.3).
- **SKU chết tăng phù hợp với việc cả danh mục bán chậm hơn, không dồn vào nhóm nào.** Trong 12 tháng trước cửa sổ 30 ngày, mỗi SKU bán bình quân 63,5 món, so với 74,2 món một năm trước; SKU bán chậm hơn thì dễ chạm 0 món trong 30 ngày hơn.
  - *Theo dòng hàng*, tỉ lệ SKU chết năm 2026 trải từ 0,96% (Áo khoác) đến 6,02% (Áo), nhưng đi theo tốc độ bán: dòng hàng bán nhiều món mỗi SKU (Áo khoác 76,9, Set bộ 71,1) ít SKU chết nhất. Khi tính kỳ vọng theo tốc độ bán của từng SKU, không dòng hàng nào lệch quá 2 sai số chuẩn.
  - *Theo BST*, chỉ BST TẾT có nhiều SKU chết hơn rõ so với kỳ vọng (19 so với 6,6). Đây là mùa vụ, không phải hàng tồn: BST TẾT bán dồn vào T1 (mục 6.1), nên tháng 8/2026 chỉ bán 63,7% mức bình quân một tháng trong 12 tháng trước của chính nó, so với 80,1% ở các BST còn lại. Khi tính thêm mức chậm mùa vụ này, kỳ vọng của BST TẾT lên khoảng 16, sát thực tế 19. Trong 19 BST còn lại, 18 BST nằm trong 2 sai số chuẩn; BST STREET vượt ở chiều ngược lại (ít SKU chết hơn), mức có thể gặp do ngẫu nhiên khi so 20 nhóm.

> **Cách đọc.** SKU chết là SKU đã từng bán nhưng không bán món nào trong 30 ngày cuối kỳ; kỳ vọng tính bằng xác suất một SKU không có dòng bán nào trong 30 ngày nếu giữ tốc độ bán 12 tháng trước, nhân hệ số chung để tổng kỳ vọng bằng tổng thực tế (cách tính ở [#5](methodology.md)). Biên gộp và tỉ lệ giảm giá không tính đơn dùng điểm (như mục 3). Biên tăng theo năm chủ yếu vì giá vốn mỗi món gần như đứng yên (315.389 → 315.999 đ, 2024–2026) trong khi giá bán mỗi món tăng 9,9% năm 2025 và 9,0% năm 2026, nên card biên không so với năm trước. Chênh lệch biên giữa BST hay dòng hàng không vượt rõ mức nhiễu, nên không so biên giữa các nhóm.

### 6.1 BST: số mẫu, cơ cấu và thời điểm bán

- **20 BST đều giảm,** từ ▼ 0,2% (BST RESORT) đến ▼ 4,2% (BST TWEED), quanh mức chung ▼ 2,0%; mỗi BST chỉ vài chục mẫu nên chênh lệch này là nhiễu.
- **Số mẫu giải thích phần lớn thứ hạng.** Mỗi BST có 23–37 mẫu (SP cha). BST TẾT (37 mẫu, 17,0 tỷ) bán gấp 2,4 lần FOB THU ĐÔNG (23 mẫu, 7,0 tỷ), nhưng tính trên mỗi mẫu chỉ gấp 1,5 lần (458,5 so với 303,4 tr; mức chung 358,6 tr).
- **Ba BST dịp lễ bán mạnh nhất trong dịp lễ của mình, nhưng vẫn bán quanh năm.** Cửa sổ dịp lễ: BST TẾT 01–25/01, BST 14/2 01–14/02, BST 8/3 01–10/03. 17 BST còn lại bám sát nhịp tháng chung (lệch tối đa 1,5 điểm).

| BST | Tỉ trọng doanh số tháng đỉnh | Mức chung tháng đó | Bán trong KM 2026 | Tỉ lệ giảm giá 2026 |
|---|---:|---:|---:|---:|
| BST TẾT (T1) | 40,8% | 18,7% | 58,88% | 19,77% |
| BST 8/3 (T3) | 19,9% | 11,5% | 47,75% | 18,26% |
| BST 14/2 (T2) | 16,7% | 8,3% | 38,43% | 16,66% |
| Tất cả BST | | | 44,66% | 17,56% |

- **Mức giảm giá của ba BST trùng với việc dịp lễ có rơi vào đợt khuyến mãi hay không** (chỉ 3 BST, và dịp lễ luôn trùng đợt khuyến mãi nên dữ liệu không tách được phần nào do BST, phần nào do khuyến mãi): cửa sổ BST TẾT trùng "Xả kho & Chào Xuân" (giảm thêm 15%), BST 8/3 trùng "Hot Sale 8/3" (20%), BST 14/2 không trùng đợt nào. Xếp theo tỉ trọng bán trong khuyến mãi hay theo tỉ lệ giảm giá đều ra cùng thứ tự TẾT > 8/3 > 14/2.
- **Cơ cấu dòng hàng khác nhau rõ:** BST 8/3 có 54,7% doanh số từ Set bộ (mức chung 26,6%), BST TRENCH COAT 51,8% từ Áo khoác. **Tỉ trọng online gần như như nhau** giữa các BST (27,2–32,8%).

> **Cách đọc.** Kỳ T1–T8 có cả ba dịp lễ nhưng không có quý 4, nên thứ hạng BST trong kỳ nghiêng về BST dịp lễ; không suy ra cả năm. Tên BST không phải lúc nào khớp nội dung (BST T-SHIRT có 48,1% doanh số từ Set bộ). Mỗi BST giữ nguyên danh sách mẫu qua cả ba năm, nên so sánh BST giữa các năm là so cùng một bộ mẫu.

### 6.2 Top 10 sản phẩm

**Nhóm dẫn đầu ổn định, mức tập trung thấp.** Top 10 chiếm 12,61 tỷ, tức 5,86% doanh số; sản phẩm đầu (2R36.2601, 1,41 tỷ) chiếm 0,65%. Bảy sản phẩm đầu năm 2026 đều nằm trong top 7 năm 2025; tám trên mười là Áo khoác.

> **Cách đọc.** Từ khoảng hạng 8 trở xuống, thứ hạng đổi chủ yếu do nhiễu: mỗi sản phẩm bán khoảng 600–860 món nên tự dao động khoảng ±4% mỗi năm, trong khi hai hạng liền nhau chỉ cách 0,3–4,9%. Ví dụ, sản phẩm hạng 11 năm 2026 (5S65.2545) lên từ hạng 17 dù số món bán ra giảm 7,3% (ít hơn mức giảm chung 10,1%, nhưng vẫn trong mức nhiễu). Báo cáo không bàn sản phẩm nào lọt hay trượt top 10.

---

## 7. Khách hàng — doanh thu đến từ những khách nào, và bao nhiêu khách quay lại?

*Trang dashboard: KHÁCH HÀNG · Mẫu số: khách định danh. "Ngày mua" = một ngày khách có giao dịch có doanh thu.*

| | T1–T8/2026 | So với T1–T8/2025 |
|---|---:|---:|
| Khách mua | 26.827 | ▼ 2,7% |
| Khách mới | 1.506 | ▼ 48,9% |
| Tỉ lệ mua lặp lại (≥ 2 ngày mua trong T1–T8/2026) | 71,0% | ▼ 1,0 điểm |
| Doanh thu mỗi khách | 7,16 tr | ▲ 1,0% |
| Doanh thu khách định danh | 192,1 tỷ = 94,3% doanh thu toàn công ty | |

### 7.1 Số khách giảm ít, nhưng mỗi khách mua ít lần hơn

Số khách giảm 2,7%, trong khi giao dịch toàn công ty giảm 10,4%. Phần chênh nằm ở tần suất: bình quân 5,28 ngày mua mỗi khách trong T1–T8/2026, so với 5,70 cùng kỳ 2025.

> **Cách đọc.** Dữ liệu cho biết mỗi khách mua ít lần hơn, chưa cho biết vì sao. "Khách mới" là khách lần đầu xuất hiện trong dữ liệu (bắt đầu 01/01/2024), không nhất thiết là khách lần đầu mua ở JM, nên những tháng đầu bị đẩy lên rất cao (T1/2024: 16.330) rồi giảm dần. Phép mô phỏng ở [#5](methodology.md) rút giao dịch từ một tập khách cố định, không có khách mới thật sự đến; nó vẫn cho số "khách mới" giảm 49,5%, gần như bằng mức giảm thực tế (49,0% theo cùng cách đếm; dashboard 48,9%). Vì vậy con số này chưa đủ để kết luận thu hút khách mới yếu đi.

### 7.2 Ranh giới thật: mua một lần và mua lặp lại

| | T1–T8/2026 | T1–T8/2025 |
|---|---:|---:|
| Mua 1 ngày: % số khách · % doanh thu | 29,0% · 5,3% | 28,0% · 4,6% |
| Mua ≥ 2 ngày: % số khách · % doanh thu | 71,0% · 94,7% | 72,0% · 95,4% |

**Phép thử theo nhóm khách.** Xếp 35.638 khách tại ngày 31/08/2025 theo nhãn thường dùng trong báo cáo RFM, rồi theo dõi 12 tháng sau:

| Nhóm tại 31/08/2025 | Số khách | Quay lại mua trong 12 tháng | Doanh thu mỗi khách 12 tháng |
|---|---:|---:|---:|
| Mua lặp lại, đang mua đều | 18.090 | 85,4% | 9,29 tr |
| Mua lặp lại, lâu chưa mua ("có nguy cơ") | 7.079 | 92,3% | 11,00 tr |
| Mua lặp lại, rất lâu chưa mua ("đã rời") | 3.514 | 98,0% | 15,86 tr |
| Chỉ mới mua một lần | 6.955 | 36,4–38,3% | 0,72–0,76 tr |

- **Khách bị dán nhãn "có nguy cơ" hay "đã rời" lại quay lại nhiều hơn khách đang mua đều.** Nhãn tính bằng thời gian chưa mua so với nhịp mua của chính khách, và cách tính này dễ đẩy khách mua nhiều lần vào nhóm "lâu chưa mua". Khi so trong cùng mức số lần đã mua, ba nhóm quay lại gần như bằng nhau (ví dụ đã mua lặp lại 11–20 lần: 99,7% ở cả ba nhóm). Nhãn không thêm thông tin gì ngoài số lần mua, nên dashboard không dùng.
- **Khoảng cách thật nằm giữa mua lặp lại (85–98% quay lại) và mua một lần (khoảng 37%).** 6.955 khách chỉ mới mua một lần, 19,5% số khách, chỉ tạo 1,7% doanh thu 12 tháng sau của cả nhóm 35.638 khách (5,2 trên 306,9 tỷ). Khách mua lặp lại chi nhiều hơn vì mua nhiều lần hơn, không vì chi nhiều hơn mỗi lần (tương quan giữa số lần mua và giá trị mỗi lần dưới +0,1: +0,08 tại 31/08/2025, +0,04 tại 31/08/2026).
- Đến 31/08/2026, **6.538 khách vẫn chỉ mua một lần** (17,0% trong 38.446 khách định danh đã có ngày mua), là nhóm mục tiêu của đề xuất 14 (mục 8.3).

> **Cách đọc.** Bài học về cách tính nhãn, dùng được cho dữ liệu thật: nếu nhịp mua = thời gian từ lần mua đầu đến hôm nay ÷ số lần mua lặp lại, thì khách mới quay lại 1–2 lần không bao giờ đủ điều kiện vào nhóm "đã rời" dù im lặng bao lâu. Nên tính nhịp mua từ khoảng giữa lần mua đầu và lần mua cuối, và kiểm nhãn bằng phép thử như trên trước khi chi ngân sách cho nó ([#5](methodology.md)).

### 7.3 Tập trung doanh thu theo 10% khách

Xếp khách mua trong kỳ theo doanh thu, chia 10 nhóm bằng nhau: **D1** là 10% chi nhiều nhất, … **D10** là 10% chi ít nhất.

| Nhóm | D1 | D2 | D3 | D4 | D5 | D6–D10 |
|---|---:|---:|---:|---:|---:|---:|
| Doanh thu T1–T8/2026 | 78,6 tỷ | 37,2 tỷ | 24,4 tỷ | 17,0 tỷ | 12,1 tỷ | |
| Tỉ trọng | 40,9% | 19,4% | 12,7% | 8,8% | 6,3% | khoảng 12% |

**Một phần năm số khách tạo hơn 60% doanh thu** (D1 + D2 = 60,3%). **Mô hình giá trị vòng đời khách hàng (Customer Lifetime Value, CLV)** dự báo cùng mức tập trung cho 12 tháng tới: nhóm 10% đầu (3.212 khách) nắm 42,5% giá trị dự báo. Mô hình gồm BG/NBD (dự báo số lần mua) và Gamma-Gamma (dự báo giá trị mỗi lần), ảnh chụp 31/08/2026.

> **Cách đọc.** CLV chỉ dùng để xếp hạng khách. Trên kỳ kiểm (T1–T8/2026), mô hình dự báo số lần mua cao hơn thực tế khoảng 34% (187.593 so với 139.905 ngày mua, tính trên 36.940 khách đã mua trước kỳ kiểm). Phần lớn sai số đến từ việc cường độ mua chung giảm theo thời gian, vi phạm giả định của mô hình: số ngày mua mỗi ngày giảm từ 772,1 ở kỳ hiệu chỉnh (2024–2025) xuống 583,0 ở kỳ kiểm, tức giảm 24,5%, tương ứng mức dự báo dư khoảng 32% (1 ÷ 0,755 ≈ 1,32). Phần còn lại đến từ 1.193 khách mới mua một lần, lần đầu trong 131 ngày cuối kỳ hiệu chỉnh: mô hình dự báo họ 2.427 ngày mua, thực tế chỉ 375. Mức giảm cường độ gồm cả mùa vụ, vì kỳ kiểm chỉ có T1–T8, nên đây là giải thích phù hợp, chưa phải chứng minh; mô hình cũng không xếp hạng tốt hơn cách xếp theo số lần đã mua ([#5](methodology.md)). 6.328 khách chỉ mua một ngày không có trong mô hình. Số này ít hơn 6.538 ở mục 7.2 là 210 khách, vì mục 7.2 bỏ cả ngày khách có phiếu trả: khách có thêm một ngày đổi hàng vẫn được tính là mua một lần.

### 7.4 Hạng thẻ và phân hạng khách

Ma trận trên dashboard (39.531 khách, ảnh chụp 31/08/2026) đặt **hạng thẻ** (chi tiêu offline 365 ngày) cạnh **phân hạng khách** (tần suất, giá trị và độ gần của lần mua cuối, trên cả hai kênh).

- **Đầu bảng gần như trùng nhau:** 688/694 khách Diamond là VVIP.
- **Cuối bảng thì không:** một nửa khách Member (11.390/22.679) thuộc nhóm "Cần kích hoạt lại"; 1.974 khách VVIP trải từ Diamond xuống Silver. 4.008 khách "Ngoài CT" (chưa có hóa đơn offline) chủ yếu thuộc "Cần kích hoạt lại" (2.637) và "Chưa mua" (796), không ai là VIP hay VVIP.

> **Cách đọc.** "Cần kích hoạt lại" là nhóm có lần mua cuối đã lâu, không phải dự báo rời bỏ (mục 7.2). Hai hệ phân loại được giữ riêng.

---

## 8. Dự đoán và đề xuất

Mỗi con số trong mục này là một **phép tính kịch bản** "nếu … thì …", ghi rõ công thức, đầu vào (từ mục 2–7 hoặc query nhóm KB, DB ở phụ lục) và giả định; không phải dự báo chắc chắn. Mỗi đề xuất có hai mức: **thận trọng** và **kỳ vọng**. Hai mức này là giả định của người phân tích, chọn thấp so với khoảng cách quan sát được (ví dụ chỉ thu hẹp 25–50% khoảng cách TikTok Shop – Shopee), vì dữ liệu không có thử nghiệm nào cho biết mức cải thiện thực tế. Ở doanh nghiệp thật, nên thử ở quy mô nhỏ có nhóm đối chứng trước khi mở rộng.

### 8.1 Dự đoán: doanh thu T1–T8/2027

**Công thức:** Doanh thu 2027 = 203,7 tỷ × (1 + thay đổi số giao dịch) × (1 + thay đổi giá trị mỗi giao dịch); đầu vào mục 2.

| Kịch bản | Số giao dịch | Giá trị mỗi giao dịch | Doanh thu T1–T8/2027 | So với 2026 |
|---|---:|---:|---:|---:|
| A. Xu hướng 2026 lặp lại | ▼ 10,4% | ▲ 9,3% | 199,7 tỷ | ▼ 2,0% |
| B. Giá ngừng tăng | ▼ 10,4% | không đổi | 182,6 tỷ | ▼ 10,4% |
| C. Giữ được số giao dịch | không đổi | ▲ 9,3% | 222,7 tỷ | ▲ 9,3% |

Khoảng cách giữa B và C là 40,1 tỷ, gần 20% doanh thu một kỳ: **số lượt mua là đòn bẩy lớn nhất.** *Giả định: tốc độ thay đổi 2026 lặp lại một năm; cơ cấu kênh, sản phẩm và lịch khuyến mãi không đổi. Ngoại suy một bước từ ba kỳ, chưa đủ dữ liệu cho khoảng tin cậy.*

### 8.2 Bảng ưu tiên

*Độ khó là đánh giá định tính: Thấp = điều chỉnh vận hành, Trung bình = cần thiết kế chương trình hoặc phối hợp nhiều bộ phận, Cao = phụ thuộc đối tác bên ngoài hoặc thay đổi lớn.*

| # | Đề xuất | Tác động: thận trọng → kỳ vọng | Đơn vị | Độ khó | Ưu tiên |
|---:|---|---:|---|---|---|
| 2 | Tăng số món mỗi hóa đơn offline (bán kèm, combo) | +1,8 → +4,4 tỷ | mỗi kỳ T1–T8 | Thấp | **1** |
| 6 | End of Season dùng "mua nhiều giảm thêm" | +0,6 → +1,2 tỷ | mỗi năm | Thấp | **1** |
| 11 | Giảm trả hàng vì sai size | +0,5 → +0,9 tỷ | mỗi kỳ T1–T8 | Thấp | **1** |
| 10 | Giảm chuyển hoàn, trả hàng ở TikTok Shop | +0,9 → +1,8 tỷ (sau phí +0,7 → +1,5) | mỗi kỳ T1–T8 | Cao | **2** |
| 15 | Giữ chân nhóm 10% khách đầu | độ nhạy¹: mất 5–10% khách = −3,9 → −7,9 tỷ | mỗi kỳ T1–T8 | Trung bình | **2** |
| 14 | Chuyển khách mua một lần sang mua lần hai | +0,3 → +0,6 tỷ | mỗi năm | Trung bình | **2** |
| 4 | Nhân sự, trưng bày theo nhịp cuối tuần | chưa lượng hóa | | Thấp | 3 |
| 1, 3, 5, 7, 8, 9, 12, 13, 16 | Thay đổi cách đo và theo dõi | không trực tiếp tạo doanh thu | | Thấp | nền tảng |

*Ưu tiên 1 = tác động rõ, triển khai trong tầm kiểm soát. Ưu tiên 2 = tác động hoặc rủi ro lớn nhưng tốn công hơn. Các đề xuất "nền tảng" thay đổi cách đo, cần làm song song để đánh giá được các đề xuất còn lại. Đơn vị khác nhau, nên so trong cùng đơn vị. ¹ Đề xuất 15 là rủi ro nếu mất khách, không phải tác động kỳ vọng: dữ liệu không cho biết tỉ lệ rời bỏ của nhóm này, nên không so trực tiếp với các dòng khác.*

### 8.3 Chi tiết từng đề xuất

#### Lượt mua toàn chuỗi

**1. Lấy số lượt mua làm chỉ tiêu chính, không dựa vào tăng giá.** Căn cứ: mục 2.1 và kịch bản B–C ở 8.1. Mỗi 1% số giao dịch giữ lại ≈ 2,0 tỷ một kỳ (= 203,7 tỷ × 1%). *Theo dõi:* số giao dịch so với cùng kỳ, theo tháng và kênh.

#### Offline

**2. Tăng số món mỗi hóa đơn bằng bán kèm và combo.** Căn cứ: UPT giữ 1,69–1,70 qua ba năm, trong khi Black Friday cho thấy điều kiện số lượng đẩy được UPT lên 2,11, tức +0,40 món (mục 4); AOV = UPT × giá mỗi món. Mức +0,02–0,05 món chỉ bằng 5–12,5% mức tăng đó.
- *Tác động:* doanh thu phiếu bán offline × ΔUPT ÷ 1,70. Thận trọng +0,02 món: **+1,8 tỷ**; kỳ vọng +0,05 món: **+4,4 tỷ** một kỳ (= 149,9 tỷ × 0,05 ÷ 1,70).
- *Giả định:* giá mỗi món và số hóa đơn không đổi. Combo thường đi kèm giảm giá; phần giảm này chưa được trừ, nên cần đo doanh thu chứ không chỉ UPT khi thử. *Theo dõi:* UPT và AOV theo cửa hàng, theo tháng.

**3. Theo dõi rủi ro tập trung ở Hà Nội, và so thị trường theo doanh thu mỗi cửa hàng.** Độ nhạy: Hà Nội giảm 10% làm doanh thu offline giảm 10,5 tỷ, tức 7,0%. Khi xét mở rộng, so theo doanh thu mỗi cửa hàng và AOV, không theo tổng doanh thu tỉnh. *Theo dõi:* tỉ trọng Hà Nội theo tháng.

**4. Bố trí nhân sự và hàng trưng bày theo nhịp cuối tuần,** khoảng 1,35 lần ngày thường (tỉ lệ doanh thu mỗi ngày, mục 3.2). *Giả định:* nhu cầu nhân sự tỉ lệ với doanh thu. *Theo dõi:* doanh thu mỗi giờ công.

#### Khuyến mãi

**5. Đánh giá mỗi chương trình bằng uplift doanh thu, không bằng uplift số hóa đơn** (mục 4), đo bằng cùng mô hình.

**6. Mang cơ chế "mua nhiều giảm thêm" của Black Friday sang End of Season.** JM đã dùng cơ chế bậc thang theo số món cho Black Friday (mua 2, 3, 4 món giảm dần sâu hơn), nên đây là mở rộng một cơ chế sẵn có, không phải thiết kế mới. Căn cứ: trong dữ liệu, AOV giảm 11,2% ở End of Season so với 5,1% ở Black Friday.
- *Tác động:* doanh thu phiếu bán offline 32 ngày End of Season 2026 là 17,01 tỷ, tương ứng nền không khuyến mãi 16,58 tỷ (= 17,01 ÷ 1,026). Giữ uplift hóa đơn +15,6%:
  - Kỳ vọng, AOV chỉ giảm 5,1% như Black Friday (đây là giả thuyết cần thử: Black Friday đo trên nền khác, mục 4): uplift doanh thu +9,7% (= 1,156 × 0,949 − 1), thêm **1,18 tỷ** mỗi năm.
  - Thận trọng, AOV giảm 8,15% (giữa hai mức): uplift +6,2%, thêm **0,59 tỷ**.
- *Giả định:* cơ chế mới không làm giảm lượt mua; chỉ tính offline. *Theo dõi:* uplift doanh thu, AOV, UPT trong cửa sổ, có nhóm cửa hàng đối chứng.

**7. Lên kế hoạch BST dịp lễ cùng lịch khuyến mãi** (mục 6.1). Chưa lượng hóa: dữ liệu chưa đủ để ước tính doanh số BST thay đổi ra sao nếu dời lịch. *Theo dõi:* tỉ lệ bán trong khuyến mãi và tỉ lệ giảm giá từng BST dịp lễ.

**8. Dùng chung lịch khuyến mãi cốt lõi cho hai kênh, điều chỉnh riêng từng sàn.** Hai kênh phản ứng như nhau (mục 4), nhưng mỗi sàn có lịch sale, quy định và cách hiển thị giá riêng, khó kiểm soát đồng bộ hơn; cần đối chiếu lịch từng sàn và theo dõi giá bán thực tế.

#### Online

**9. Đánh giá mọi sàn trên doanh thu còn lại sau trả hàng và sau phí, không trên đơn đặt.**

| Sàn | Doanh thu trên 100 đơn đặt | Phí theo % hiện hành | Sau phí |
|---|---:|---:|---:|
| Admin | 81,4 tr | 0% | 81,4 tr |
| Website | 76,6 tr | 0% | 76,6 tr |
| Facebook | 76,2 tr | 0% | 76,2 tr |
| Instagram | 75,8 tr | 0% | 75,8 tr |
| Lazada | 74,0 tr | 7,99% | 68,1 tr |
| Shopee | 73,3 tr | 9%¹ | 66,7 tr |
| **TikTok Shop** | **51,0 tr** | **18,5%** | **41,6 tr** |

*Công thức: doanh thu T1–T8/2026 của sàn ÷ đơn đặt × 100 × (1 − phí %). Chưa tính phí cố định theo đơn; doanh thu trong dữ liệu chưa trừ phí, nên cột cuối là phép tính minh họa. ¹ Suy luận.* Cùng 100 đơn đặt, TikTok Shop mang về khoảng 62% của Shopee và 55% của Facebook sau phí. *Theo dõi:* doanh thu sau phí trên 100 đơn đặt, từng sàn, theo tháng.

**10. Giảm chuyển hoàn và trả hàng ở TikTok Shop.**
- *Tác động:* nếu chuyển hoàn và trả toàn phần về mức Shopee (12,37% và 8,53%), đơn còn doanh thu tăng từ 48,24% lên 66,39% (= 100% − 12,71% − 12,37% − 8,53%), tức thêm 3.451 đơn trên 19.018 đơn đặt × AOV 1.057.203 đ = 3,65 tỷ (toàn bộ khoảng cách, trước phí). Thận trọng, thu hẹp 25% khoảng cách: **+0,9 tỷ**; kỳ vọng, 50%: **+1,8 tỷ** một kỳ. Trừ phí theo % 18,5%: +0,7 và +1,5 tỷ.
- *Giả định:* tỉ lệ hủy và AOV không đổi. Độ khó cao vì phụ thuộc đơn vị vận chuyển và chính sách của sàn. *Theo dõi:* chuyển hoàn, trả toàn phần TikTok Shop theo tháng.

**11. Giảm trả hàng, bắt đầu từ size.** Bảng size rõ hơn, gợi ý size theo số đo, hoặc đổi size thay vì trả.
- *Tác động:* giá trị hoàn tiền đơn trả T1–T8/2026 là 7,05 tỷ; sai size chiếm 65,7%. Giảm 10% đơn trả vì sai size: **+0,46 tỷ**; giảm 20%: **+0,93 tỷ** một kỳ (= 7,05 × 65,7% × 20%).
- *Giả định:* giá trị mỗi đơn trả như nhau giữa các lý do. *Theo dõi:* tỉ lệ trả vì sai size theo dòng hàng.

#### Sản phẩm

**12. Đánh giá BST trên tổng doanh số kèm số mẫu và doanh số mỗi mẫu,** rồi xem cơ cấu và thời điểm bán trước khi kết luận (mục 6.1).

**13. Theo dõi SKU chết theo tốc độ bán, không theo số đếm thô.** Hiện chưa nhóm nào bất thường ngoài BST TẾT, mà BST TẾT là do mùa vụ (mục 6). Cảnh báo khi số SKU chết của một dòng hàng hay BST vượt kỳ vọng theo tốc độ bán quá 2 sai số chuẩn, và loại trừ BST dịp lễ ngoài mùa (như BST TẾT trong tháng 8) để không xả hàng nhầm.

#### Khách hàng

**14. Dồn ngân sách giữ chân vào lần mua thứ hai của khách mới, không vào chiến dịch kéo lại khách lâu không mua.**
- *Tác động:* 6.538 khách hiện chỉ mua một lần. Theo phép thử ở mục 7.2, khách mua một lần chi 0,747 tr trong 12 tháng tiếp theo, khách đã quay lại 1–2 lần chi 1,711 tr; chênh 0,964 tr mỗi khách. Thận trọng, 5% chuyển được: **+0,32 tỷ/năm**; kỳ vọng, 10%: **+0,63 tỷ/năm** (= 654 × 0,96 tr). Nếu toàn bộ chuyển được: 6,30 tỷ/năm.
- *Giả định:* khách chuyển được chi như nhóm đã quay lại 1–2 lần. Dữ liệu chỉ cho thấy khách mua một lần ít quay lại, chưa cho thấy chương trình nào chuyển đổi được họ, và không có dữ liệu chiến dịch; cần thử có nhóm đối chứng. *Theo dõi:* tỉ lệ khách mới mua lần hai trong 90 ngày.

**15. Ưu tiên chăm sóc và đặc quyền cho nhóm 10% khách chi nhiều nhất** (D1: 78,6 tỷ, 40,9% doanh thu khách định danh).
- *Độ nhạy:* mất 5% khách nhóm này: **−3,9 tỷ**; mất 10% (khoảng 270 trên 2.680 khách): **−7,9 tỷ** một kỳ, tức 4,1% doanh thu khách định danh. *Giả định:* khách mất chi bằng bình quân nhóm.
- Nhận diện sớm khách sẽ vào nhóm bằng xếp hạng CLV hoặc xếp theo số lần đã mua: hai cách cho thứ hạng gần như nhau (mục 7.3), nên cách đơn giản hơn là đủ. Đọc cả phân hạng khách theo hai kênh, không chỉ hạng thẻ (mục 7.4). *Theo dõi:* tỉ lệ giữ chân nhóm D1 theo quý.

**16. Kiểm mọi nhãn "có nguy cơ rời bỏ" bằng phép thử theo nhóm trước khi chi ngân sách cho nhóm đó** (mục 7.2).

### 8.4 Dữ liệu cần có để trả lời tiếp

- **Lượt khách vào cửa hàng, lượt truy cập trên sàn:** biết số giao dịch giảm vì ít người đến hay vì tỉ lệ mua giảm.
- **Chi phí marketing và vận hành theo kênh:** tính hiệu quả khuyến mãi và lợi nhuận theo cửa hàng, theo sàn.
- **Phí sàn thực trừ trên từng đơn:** thay phép tính minh họa ở đề xuất 9.
- **Lý do hủy đơn được ghi có kiểm soát:** biết phần hủy nào xử lý được.

---

## 9. Giới hạn dữ liệu

Bảng đối chiếu đầy đủ giữa từng phát hiện và quy tắc tạo dữ liệu ở **[#8 Thiết kế dữ liệu mô phỏng](synthetic-data-design.md)**.

- **Không có dữ liệu lượt khách dùng được** (lượt khách cửa hàng trong dữ liệu được tính ngược từ số hóa đơn, xem [#8](synthetic-data-design.md)) **và không có lượt truy cập trên sàn:** biết số giao dịch giảm, chưa biết vì sao.
- **Không có chi phí ngoài giá vốn; giá vốn mỗi món gần như không đổi qua ba năm:** không tính được lợi nhuận ròng, hiệu quả marketing; biên gộp không so theo thời gian hay giữa nhóm.
- **Doanh thu online ghi theo cùng một tỉ lệ trên giá trị đơn ở mọi sàn,** chưa trừ phí thực tế.
- **Một số trường không có hình dạng để phân tích:** lý do hủy phân bố đều; giờ đặt đơn và thời gian xử lý đơn không khác theo sàn; lý do trả không khác theo sàn hay sản phẩm.
- **Lịch sử khách bắt đầu từ 01/2024,** nên "khách mới" giai đoạn đầu gồm cả khách cũ; đơn online không có địa chỉ khách.
- **Định danh khách giữa sàn và cửa hàng:** ở doanh nghiệp thật, các sàn không chia sẻ định danh khách với cửa hàng, nên báo cáo không phân tích khách mua đa kênh dù dữ liệu mô phỏng có liên kết này.

---

## Phụ lục A — Nguồn số

Mọi số lấy từ dashboard hoặc query chạy trên BigQuery từ 27/10 đến 01/11/2026. Mã trong repo: các view và bảng trong `sql/`, mô hình khuyến mãi `models/promo_uplift.py` (mục 4), mô hình CLV `models/clv_model.py` (mục 7.3). Các truy vấn kiểm riêng của báo cáo không đưa vào repo; cột Query giữ mã nội bộ của từng truy vấn (TQ-1, KH-8…) để đối chiếu.

| Mục | Nội dung | Trang dashboard | Query |
|---|---|---|---|
| 2 | KPI; cả năm 2024–2025 | Tổng quan · KPI | TQ-1 |
| 2.1 | Số lượng bán, giá mỗi món, số món mỗi giao dịch; biến động doanh thu | Tổng quan · KPI, Biến động doanh thu | TQ-1, TQ-2 |
| 2.2 | Doanh thu, giao dịch theo tháng | Tổng quan · Doanh thu theo tháng | TQ-3 |
| 2.3 | Tỉnh, sàn, dòng hàng | Tổng quan · ba chart cột | TQ-4, TQ-5 |
| 3 | KPI offline; UPT 2024; phần doanh số không dùng điểm | Offline · KPI | dashboard, OF-7 |
| 3.1 | Tập trung, quy mô, thứ hạng; AOV, UPT theo cửa hàng; hệ số AOV; nhiễu YoY | Offline · Doanh thu theo cửa hàng | OF-1, OF-4, OF-5, OF-6, OF-8 |
| 3.2 | AOV theo tháng, cuối tuần | Offline · theo tháng, theo ngày trong tuần | OF-2 |
| 3.3 | Hạng thẻ | Offline · Doanh thu theo hạng thẻ | OF-3 |
| 4 | Ngày, tỉ trọng khuyến mãi; uplift; lịch chương trình; UPT Black Friday | Hiệu quả KM | dashboard, OF-7, KM-1 (`models/promo_uplift.py`) |
| 5 | KPI online; lý do trả; dòng hàng online | Online, Trả hàng theo sàn | dashboard, ON-3 |
| 5.1 | Tình trạng đơn theo sàn; phí sàn; tỉ lệ trả theo giá trị | Online · Tình trạng đơn; Trả hàng theo sàn; tooltip "Thẻ sàn" | ON-1, ON-2, ON-3 |
| 6 | KPI sản phẩm; giá vốn mỗi món; SKU chết theo dòng hàng, BST | Sản phẩm · KPI | dashboard, DB-1, SP-5 |
| 6.1 | BST: YoY, số mẫu, mỗi mẫu; tháng đỉnh, cơ cấu, online; tập mẫu qua các năm; bán trong KM, giảm giá | Sản phẩm · bảng BST; Chi tiết BST | dashboard, SP-2, DB-2 |
| 6.2 | Top 10, dao động theo số món | Sản phẩm · Top 10 | SP-1, SP-3, SP-4 |
| 7 | KPI khách hàng; khách mới T1/2024; mô phỏng tập khách cố định | Khách hàng · KPI | dashboard, KH-2, KH-6 |
| 7.2 | Mua một lần / lặp lại; phép thử theo nhóm khách; số khách mua một lần năm 2026; tương quan số lần × giá trị mỗi lần | Khách hàng · Mua một lần và mua lặp lại | dashboard, KH-3, KH-4, KH-5 |
| 7.3 | Tập trung theo 10% khách; CLV; cường độ mua kỳ hiệu chỉnh và kỳ kiểm; kiểm định ngược CLV | Khách hàng · Tập trung doanh thu | dashboard, KH-1, KH-7, KH-8; CLV `models/clv_model.py` |
| 7.4 | Hạng thẻ × phân hạng | Khách hàng · ma trận | dashboard |
| 8 | Kịch bản dự đoán và đề xuất | — | KB-1 đến KB-9; DB-3, DB-4 |

**Đã chạy lại 01/11/2026:** nhiễu theo cửa hàng (OF-8); lý do trả theo sàn và tỉ lệ trả theo giá trị (ON-3); SKU chết theo nhóm (SP-5); mô hình uplift khuyến mãi (KM-1: cả 7 chương trình, khoảng tin cậy, hệ số phân tán 1,48 và 2,77, p theo năm 0,28 và 0,36 khớp từng số); mô phỏng tập khách cố định (KH-6); cường độ mua của kỳ hiệu chỉnh và kỳ kiểm CLV (KH-7); kiểm định ngược mô hình CLV trên kỳ kiểm (KH-8). Lần chạy lại KH-8 tái lập đúng mọi số của phân tích gốc (dự báo 185.165 so với 185.168; Spearman 0,8214 và 0,8340; lift D1/D10 58,7 lần), đồng thời cho thấy phân tích gốc thiếu dự báo của 1.193 khách vì thư viện mô hình trả giá trị rỗng cho nhóm này. Số trong mục 7.3 đã tính lại trên đủ 36.940 khách: dự báo cao hơn thực tế 34,09% thay vì 32,35%; Spearman 0,8077 so với 0,8324 khi xếp theo số lần đã mua; kết luận không đổi.

**Mô hình CLV** dùng để xếp hạng (BG/NBD và Gamma-Gamma khớp trên toàn bộ dữ liệu đến 31/08/2026, chạy bằng Python ngoài BigQuery; kết quả trong bảng `customer_clv`) và các phép kiểm của nó trình bày ở [#5](methodology.md) mục [6](methodology.md#6-clv-bgnbd-và-gamma-gamma). Đã chạy lại thêm tương quan YoY hai kỳ theo cửa hàng: −0,66, khớp phân tích gốc.

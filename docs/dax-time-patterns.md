# Khuôn measure thời gian (DAX) · Time measure templates

> **Dữ liệu mô phỏng / Synthetic data.** Xem đầu README. / See the top of the README.

Mọi measure trên dashboard ghép từ một khuôn dưới đây với một measure nền `[X]` (VD `[Doanh thu]`): copy khuôn, thay `[X]` và tên measure. Lý do dùng khuôn: xem Tài liệu kỹ thuật, mục 3.
*Every measure on the dashboard combines one template below with a base measure `[X]` (e.g. `[Doanh thu]`, revenue): copy the template, replace `[X]` and the name. Why templates are needed: see the Technical Documentation, section 3.*

**Bảng dùng trong khuôn / Tables used**

- `SL_Nam`, `SL_Thang`: slicer Năm, Tháng, bảng tách rời, không nối quan hệ. *Year and Month slicers, disconnected tables.*
- `'Date'`: bảng ngày, cột `Năm`, `Tháng`, `Có dữ liệu` (TRUE đến 31/08/2026). *Date table; `Có dữ liệu` = has data (TRUE up to 31/08/2026).*

Bảng `Date` (Modeling → New table), đánh dấu là Date table; `Tên tháng` sắp theo `Tháng`, `Thứ` sắp theo `Thứ số`:
*The `Date` table (Modeling → New table), marked as a date table; `Tên tháng` sorted by `Tháng`, `Thứ` sorted by `Thứ số`:*

```DAX
Date =
VAR NgayCuoi = DATE ( 2026, 8, 31 )          -- dữ liệu đến 31/08/2026 / data ends 31/08/2026
RETURN
ADDCOLUMNS (
    CALENDAR ( DATE ( 2024, 1, 1 ), DATE ( 2026, 12, 31 ) ),
    "Năm", YEAR ( [Date] ),
    "Tháng", MONTH ( [Date] ),
    "Tên tháng", "T" & MONTH ( [Date] ),
    "Thứ số", WEEKDAY ( [Date], 2 ),
    "Thứ", SWITCH ( WEEKDAY ( [Date], 2 ), 1, "T2", 2, "T3", 3, "T4", 4, "T5", 5, "T6", 6, "T7", 7, "CN" ),
    "Có dữ liệu", [Date] <= NgayCuoi,
    "MD", MONTH ( [Date] ) * 100 + DAY ( [Date] )   -- tháng*100 + ngày, để khớp lịch khuyến mãi / month*100 + day, to match the promotion calendar
)
```

---

## 0. Năm đang xem · Year being viewed

Hai measure phụ trợ dùng trong mọi khuôn. Chưa chọn năm thì xem 2026; chỉ chọn T9–T12 mà không chọn năm thì xem 2025, vì 2026 chưa có các tháng đó.
*Two helper measures used by every template. With no year selected, the year is 2026; if only Sep–Dec is selected with no year, the year is 2025, because 2026 has no data for those months yet.*

```DAX
_Năm chọn =                              -- năm người xem bấm; BLANK khi chưa chọn / selected year, BLANK if none
IF ( ISFILTERED ( SL_Nam[Năm] ), MAX ( SL_Nam[Năm] ) )
-- Chọn nhiều năm thì lấy năm lớn nhất / several years selected -> the latest

_Năm =                                   -- năm visual một kỳ hiện / year shown by single-period visuals
VAR NamChon = [_Năm chọn]
VAR ChiQ4 =
    ISCROSSFILTERED ( SL_Thang )
        && MINX ( VALUES ( SL_Thang[Tháng] ), SL_Thang[Tháng] ) >= 9
RETURN
    COALESCE ( NamChon, IF ( ChiQ4, 2025, 2026 ) )
```

`ISCROSSFILTERED ( SL_Thang )` thay cho `ISFILTERED ( SL_Thang[Tháng] )`: slicer Tháng lọc qua cột nhãn `Tên tháng`, nên `ISFILTERED` trên cột số không bắt được.
*`ISCROSSFILTERED ( SL_Thang )` replaces `ISFILTERED ( SL_Thang[Tháng] )`: the Month slicer filters through the label column `Tên tháng`, which `ISFILTERED` on the numeric column does not detect.*

---

## A · Giá trị trong kỳ · Value in the period

KPI card và mọi visual một kỳ (bảng, bar theo cửa hàng, donut…).
*KPI cards and every single-period visual (tables, bar charts by store, donuts…).*

```DAX
X · kỳ =
VAR y = [_Năm]
VAR ThangChon = VALUES ( SL_Thang[Tháng] )   -- chưa chọn = đủ 12 tháng / none selected = all 12
RETURN
    CALCULATE ( [X], 'Date'[Năm] = y, TREATAS ( ThangChon, 'Date'[Tháng] ) )
```

Không dùng `REMOVEFILTERS ( 'Date' )`: bộ lọc `'Date'[Năm] = y` chỉ ghi đè cột Năm, nên trục khác của bảng `Date` (VD thứ trong tuần) vẫn giữ.
*`REMOVEFILTERS ( 'Date' )` is not used: the filter `'Date'[Năm] = y` only overrides the year column, so other `Date` axes (e.g. day of week) are kept.*

## B · Cùng kỳ năm trước · Same period, prior year

YoY luôn so cùng kỳ: T1–T8/2026 so T1–T8/2025, không so cả năm 2025.
*YoY is always like-for-like: Jan–Aug 2026 against Jan–Aug 2025, not the whole of 2025.*

```DAX
X · năm trước =
VAR y = [_Năm]
VAR ThangChon = VALUES ( SL_Thang[Tháng] )
VAR ThangCoDuLieu =                          -- tháng đang chọn mà năm y có dữ liệu / selected months with data in year y
    CALCULATETABLE (
        VALUES ( 'Date'[Tháng] ),
        REMOVEFILTERS ( 'Date' ),
        'Date'[Năm] = y,
        'Date'[Có dữ liệu] = TRUE (),
        TREATAS ( ThangChon, 'Date'[Tháng] )
    )
RETURN
    IF ( y - 1 >= 2024,                      -- 2024 không có năm trước / 2024 has no prior year
         CALCULATE ( [X], 'Date'[Năm] = y - 1, TREATAS ( ThangCoDuLieu, 'Date'[Tháng] ) ) )
```

## C · YoY

```DAX
X · YoY =
VAR Ky = [X · kỳ]
VAR Truoc = [X · năm trước]
RETURN IF ( NOT ISBLANK ( Truoc ) && Truoc <> 0, DIVIDE ( Ky, Truoc ) - 1 )
-- Chỉ số tỉ lệ dùng hiệu số điểm: Ky - Truoc / for rate metrics use the point difference: Ky - Truoc
```

## D · MoM

Tháng cuối được chọn so với tháng liền trước; T1 so T12 năm trước. Mặc định T8/2026 so T7/2026.
*Last selected month against the month before; January against December of the prior year. Default: Aug 2026 against Jul 2026.*

```DAX
X · MoM =
VAR y = [_Năm]
VAR ThangChon = VALUES ( SL_Thang[Tháng] )
VAR L =                                      -- tháng cuối có dữ liệu trong lựa chọn / last selected month with data
    CALCULATE (
        MAX ( 'Date'[Tháng] ),
        REMOVEFILTERS ( 'Date' ),
        'Date'[Năm] = y,
        'Date'[Có dữ liệu] = TRUE (),
        TREATAS ( ThangChon, 'Date'[Tháng] )
    )
VAR yTruoc = IF ( L = 1, y - 1, y )
VAR mTruoc = IF ( L = 1, 12, L - 1 )
VAR Nay   = CALCULATE ( [X], 'Date'[Năm] = y, 'Date'[Tháng] = L )
VAR Truoc = IF ( yTruoc >= 2024, CALCULATE ( [X], 'Date'[Năm] = yTruoc, 'Date'[Tháng] = mTruoc ) )
RETURN IF ( NOT ISBLANK ( Truoc ) && Truoc <> 0, DIVIDE ( Nay, Truoc ) - 1 )

_Tháng MoM =                                 -- nhãn: "T8/2026 so với T7/2026" / label: "Aug 2026 vs Jul 2026"
VAR y = [_Năm]
VAR ThangChon = VALUES ( SL_Thang[Tháng] )
VAR L =
    CALCULATE ( MAX ( 'Date'[Tháng] ), REMOVEFILTERS ( 'Date' ), 'Date'[Năm] = y,
                'Date'[Có dữ liệu] = TRUE (), TREATAS ( ThangChon, 'Date'[Tháng] ) )
RETURN
    "T" & L & "/" & y & " so với "
        & IF ( L = 1, "T12/" & ( y - 1 ), "T" & ( L - 1 ) & "/" & y )
```

## E · Nhãn kỳ · Period label

Hậu tố tiêu đề: đủ kỳ của năm → `2025` hoặc `T1–T8/2026`; một tháng → `T3/2025`; liền nhau → `T3–T5/2025`; rời → `T1, T3/2025`.
*Title suffix: full year → `2025` or `T1–T8/2026`; one month → `T3/2025`; consecutive → `T3–T5/2025`; non-consecutive → `T1, T3/2025` (T = month).*

```DAX
_Nhãn kỳ =
VAR y = [_Năm]
VAR ThangChon = VALUES ( SL_Thang[Tháng] )
VAR Ms =
    CALCULATETABLE ( VALUES ( 'Date'[Tháng] ), REMOVEFILTERS ( 'Date' ), 'Date'[Năm] = y,
                     'Date'[Có dữ liệu] = TRUE (), TREATAS ( ThangChon, 'Date'[Tháng] ) )
VAR N  = COUNTROWS ( Ms )
VAR Lo = MINX ( Ms, 'Date'[Tháng] )
VAR Hi = MAXX ( Ms, 'Date'[Tháng] )
VAR SoThangCuaNam =
    CALCULATE ( DISTINCTCOUNT ( 'Date'[Tháng] ), REMOVEFILTERS ( 'Date' ), 'Date'[Năm] = y,
                'Date'[Có dữ liệu] = TRUE () )
RETURN
    SWITCH (
        TRUE (),
        N = 0, "không có dữ liệu",
        N = SoThangCuaNam && N = 12, FORMAT ( y, "0" ),
        N = SoThangCuaNam, "T1–T" & Hi & "/" & y,
        N = 1, "T" & Lo & "/" & y,
        Hi - Lo + 1 = N, "T" & Lo & "–T" & Hi & "/" & y,
        CONCATENATEX ( Ms, "T" & 'Date'[Tháng], ", ", 'Date'[Tháng], ASC ) & "/" & y
    )

_Nhãn kỳ năm trước =                         -- cùng tháng có dữ liệu, lùi một năm / same months with data, one year back
VAR y = [_Năm]
VAR ThangChon = VALUES ( SL_Thang[Tháng] )
VAR Ms =
    CALCULATETABLE ( VALUES ( 'Date'[Tháng] ), REMOVEFILTERS ( 'Date' ), 'Date'[Năm] = y,
                     'Date'[Có dữ liệu] = TRUE (), TREATAS ( ThangChon, 'Date'[Tháng] ) )
VAR N  = COUNTROWS ( Ms )
VAR Lo = MINX ( Ms, 'Date'[Tháng] )
VAR Hi = MAXX ( Ms, 'Date'[Tháng] )
VAR yT = y - 1
RETURN
    SWITCH (
        TRUE (),
        yT < 2024, BLANK (),
        N = 12, FORMAT ( yT, "0" ),
        N = 1, "T" & Lo & "/" & yT,
        Hi - Lo + 1 = N, "T" & Lo & "–T" & Hi & "/" & yT,
        CONCATENATEX ( Ms, "T" & 'Date'[Tháng], ", ", 'Date'[Tháng], ASC ) & "/" & yT
    )
```

## F · Dòng so sánh dưới KPI · Comparison line under a KPI

`TotKhiTang` = 1 nếu tăng là tốt, −1 nếu tăng là xấu (SKU chết, tỉ lệ hủy, chuyển hoàn, trả hàng).
*`TotKhiTang` = 1 if an increase is good, −1 if it is bad (dead SKUs, cancellation, return-to-sender and return rates).*

```DAX
X · dòng so sánh =
VAR d = [X · YoY]
RETURN
    IF (
        ISBLANK ( d ),
        "không có năm trước",
        IF ( d >= 0, "▲ ", "▼ " ) & FORMAT ( ABS ( d ), "0.0%" ) & " · " & [_Nhãn kỳ năm trước]
    )
-- VD / e.g. "▼ 2.0% · T1–T8/2025"

X · màu so sánh =
VAR d = [X · YoY]
VAR TotKhiTang = 1                           -- -1 nếu tăng là xấu / -1 if an increase is bad
RETURN IF ( ISBLANK ( d ), "#6E6E6E", IF ( d * TotKhiTang >= 0, "#2F6E5A", "#B3243F" ) )
```

## G · Chart theo tháng · Monthly charts

Chart tháng dùng trục `'Date'[Tên tháng]`, chú giải `'Date'[Năm]` và **measure nền** `[X]`: slicer tách rời không lọc chart, nên chart luôn giữ đủ năm và đủ trục. Khuôn dưới dùng thêm cho chart tháng trang Online.
*Monthly charts use the axis `'Date'[Tên tháng]`, legend `'Date'[Năm]` and the **base measure** `[X]`: the disconnected slicers do not filter them, so they always keep every year and the full axis. The template below is used in addition on the Online page.*

```DAX
X · 2 năm =                                  -- trang Online: chỉ năm đang xem và năm trước / Online page: viewed year and prior year only
                                             -- VD / e.g. Số đơn · 2 năm, với [X] = [Còn doanh thu sau trả]
VAR y = [_Năm]
VAR yDiem = SELECTEDVALUE ( 'Date'[Năm] )
RETURN IF ( yDiem = y || yDiem = y - 1, [X] )
```

Màu theo năm trên chart tháng đặt cố định (2024 `#E3A8BC` · 2025 `#D4778F` · 2026 `#8E2F4E`), không qua measure.
*Year colours on monthly charts are set directly (2024 `#E3A8BC` · 2025 `#D4778F` · 2026 `#8E2F4E`), not through a measure.*

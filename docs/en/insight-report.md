# Insight Report — JM Synthetic Data

> **Synthetic data.** Every figure in this document comes from synthetic data that the author generated in Python, based on JM's public scale, policies, prices and promotions. These are not JM's real figures and do not reflect JM's actual business performance.

*Version 14/11/2026 · Dataset v3.1 · Companion to the Power BI dashboard (6 main pages and 2 detail pages; Vietnamese only)*

---

## 0. How to read this report

- **Period.** Data runs from 01/01/2024 to 31/08/2026. The main comparison is Jan–Aug 2026 against the same period of 2025 (Jan–Aug 2025).
- **Revenue and Sales.** *Revenue* is money collected after deducting goods returned by customers. *Sales* is the value of line items sold (after discounts), before returns, and is used in the product section. The two are never compared directly (Jan–Aug 2026: revenue VND 203.7bn, sales VND 215.2bn).
- **Denominators.** Business sections cover all transactions, including 3 shared walk-in customer accounts. The customer section (section 7) covers identified customers only.
- **Number format.** Dot decimals and comma thousands separators (203.7; 164,384). Dashboard screenshots use the same number format as this report. *VND bn* = billion dong, *VND m* = million dong, *pp* = percentage points; ▲/▼ compare with the same period of the previous year. Dates are written day/month/year.
- **Noise.** A difference can appear even when nothing has really changed, simply because the number of orders per day or per year fluctuates on its own; the smaller the group, the wider the fluctuation. This report only calls a difference real when it clearly exceeds that level.
- **"How to read" boxes** give definitions, say which differences are only noise, and flag "why" questions the data cannot answer yet. Detailed tests are in **[#5 Methodology Appendix](methodology.md)**. A table mapping each finding to the data-generation rule behind it is in **[#8 Synthetic Data Design](synthetic-data-design.md)**.
- **Level of analysis.** Sections 2–7 are descriptive and diagnostic; section 8 is predictive and prescriptive.

**Glossary of Vietnamese names used in the dashboard**

| In the dashboard | In this report |
|---|---|
| BST (bộ sưu tập) | collection |
| Áo khoác · Set bộ · Đầm · Áo · Quần · Chân váy · Phụ kiện | Outerwear · Sets · Dresses · Tops · Trousers · Skirts · Accessories |
| Member · Silver · Gold · Platinum · Diamond | loyalty card tiers (unchanged) |
| VVIP · VIP · Cần kích hoạt lại · Chưa mua · Ngoài CT | customer segments: VVIP · VIP · Needs reactivation · No purchase yet · Outside programme |
| Nhóm 1 / 2 / 3 | market tier 1 / 2 / 3 |
| TTTM | shopping mall |

---

## 1. Executive summary

**Revenue for Jan–Aug 2026 reached VND 203.7bn, down 2.0%, after an 11.0% fall in Jan–Aug 2025. Customers made fewer purchases (transactions ▼ 10.4%); higher prices made up most of the gap.**

**Four key findings**

1. **Promotions bring in more purchases but cost order value.** Invoices rise 15.6–44.2% on promotion days, but in general the deeper the discount, the lower the AOV. End of Season added 15.6% invoices but only 2.6% revenue. The programme with a quantity condition (Black Friday) protects AOV best, because customers add items to the basket (section 4).
2. **TikTok Shop loses almost half of its orders.** Out of every 100 orders placed, only 48 keep any revenue, against 66 for online overall: returns to sender (RTS, parcels the customer never accepted) are about twice the level of other channels and the full-return rate is the highest. The channel also has the highest fees (section 5).
3. **The customer bottleneck is the second purchase, not lapsed customers.** Repeat customers came back at 85–98% within 12 months, including the group labelled "lapsed". Customers who had bought only once came back at about 37% (section 7.2).
4. **Revenue is concentrated in two places.** Hanoi accounts for 70.2% of offline revenue; the top 10% of customers generate 40.9% of identified-customer revenue (sections 3, 7).

*Context:* the year-on-year decline is spread evenly. All 29 stores issued fewer invoices; the 7 online channels, 7 product lines and 20 collections all moved within a narrow band around the overall rate, with none falling markedly more (sections 2–6). TikTok Shop's problem is its level, which already existed a year earlier, not the pace of decline.

**Prediction.** If the 2026 trend repeats, revenue for Jan–Aug 2027 would be about VND 199.7bn (▼ 2.0%); if prices stop rising, only VND 182.6bn (▼ 10.4%) (section 8.1).

**Three priority recommendations** (full priority table in section 8.2)

1. **Make the number of purchases the main target,** raise items per invoice through add-on selling, and focus retention budget on new customers' second purchase. Raising offline UPT by 0.02–0.05 items: +VND 1.8bn to +4.4bn per period.
2. **Evaluate every channel on revenue after returns and after fees; prioritise cutting RTS and returns on TikTok Shop, and returns due to wrong size.** Closing 25–50% of the gap between TikTok Shop and Shopee: +VND 0.9bn to +1.8bn per period before channel fees (+VND 0.7bn to +1.5bn after fees).
3. **Evaluate promotions on revenue, and test the "buy more, save more" mechanism.** End of Season offline alone: +VND 0.6bn to +1.2bn per year.

---

## 2. Overview — what drove the change in revenue?

*Dashboard page: TỔNG QUAN (Overview)*

| | Jan–Aug 2024 | Jan–Aug 2025 | Jan–Aug 2026 | 2026 vs 2025 |
|---|---:|---:|---:|---:|
| Revenue | VND 233.4bn | VND 207.9bn | VND 203.7bn | ▼ 2.0% |
| Transactions | 225,457 | 183,378 | 164,384 | ▼ 10.4% |
| Value per transaction | VND 1,035,335 | VND 1,133,486 | VND 1,239,272 | ▲ 9.3% |
| Units sold | 362,897 | 293,656 | 263,962 | ▼ 10.1% |
| Online share of total revenue | 26.3% | 26.1% | 26.3% | ▲ 0.2 pp |

Full years: 2024 VND 389.4bn, 2025 VND 347.5bn (▼ 10.8%).

### 2.1 Fewer purchases, offset by price

| Revenue change (Jan–Aug) | 2025 vs 2024 | 2026 vs 2025 |
|---|---:|---:|
| From number of transactions | −VND 43.6bn | −VND 21.5bn |
| From value per transaction | +VND 18.0bn | +VND 17.4bn |
| Total change | −VND 25.6bn | −VND 4.1bn |
| Share offset by value per transaction | 41% | 81% |

*Split by chain substitution, replacing the number of transactions first; the method and its sensitivity to ordering are in [#5](methodology.md).*

- **Fewer purchases, not fewer items per purchase.** Transactions and units both fell about 10%; items per transaction held at 1.61 · 1.60 · 1.61 over three years (offline sales-invoice UPT 1.70 · 1.69 · 1.70).
- **Value per transaction rose because of price.** The average price per item rose 9.0% (VND 747,849 → 815,191).
- **The decline slowed because transactions fell more slowly** (▼ 18.7% then ▼ 10.4%), not because order value rose faster (▲ 9.5% then ▲ 9.3%). Losing less is not growth: revenue still fell in both years.
- **The online share stayed at about 26%.** Offline fell 2.3% and online 1.2%; the gap is too small to conclude that online held up better.

> **How to read.** Do not present the rise in value per transaction as a sales achievement. The data cannot yet say whether transactions fell because customers were lost, because customers bought less often, or because of a lack of new customers; that needs footfall data (sections 7.1, 8.4).

### 2.2 By month

- **All three years share the same shape:** a peak in January (18.7% of Jan–Aug 2026 revenue), a trough in February (8.3%), a gradual rise to May, and a dip in June–July.
- **2026 was below 2025 in 7 of 8 months** (from ▼ 0.2% in February to ▼ 5.3% in June); only August was higher (▲ 0.6%). Transactions were lower in all 8 months (▼ 8.7% to ▼ 13.3%).

> **How to read.** The trough is always in February, although Tết (Lunar New Year) fell on 10/02/2024, 29/01/2025 and 17/02/2026, so the February trough is not attributed to the Tết holiday until daily revenue has been examined. Do not conclude that "the decline is narrowing" from August alone: August transactions were still down 8.7%.

### 2.3 By province, channel and product line

**Every group changed, but none departed markedly from the overall ▼ 2.0%:**

| Chart | Largest groups | Range of change |
|---|---|---|
| Revenue by province/city | Hanoi ▼ 2.4% · Ho Chi Minh City 0.0% · Hai Phong ▼ 3.4% | ▼ 3.4% → 0.0% |
| Revenue by channel | 7 channels | ▼ 2.6% (Lazada) → ▲ 1.8% (Instagram) |
| Sales by product line | 7 product lines | ▼ 2.6% (Sets) → ▼ 1.6% (Trousers) |

- **Offline is highly concentrated:** Hanoi accounts for 70.2% of offline revenue from 11 of 29 stores; the top three provinces account for 85.2%.
- **Online is more spread out:** the top three channels (Facebook 24.0%, Shopee 21.1%, TikTok Shop 18.1%) account for 63.2%; no channel exceeds 24%.
- **Outerwear and Sets make up 58.6% of sales because they are expensive,** not because they sell far more items: the two lines account for only 37.9% of units, at an average of VND 1.36m and VND 1.16m per item. **Accessories are the opposite:** third by units (14.2%) but last by sales (4.5%), at about VND 259k per item.

> **How to read.** Provinces with few stores can swing more because of their small base (Hai Duong ▼ 15.5%, Ninh Binh ▼ 9.4%, Dong Nai ▲ 3.8%), although many one-store provinces sit close to the overall rate (Thai Binh ▲ 0.4%, Thanh Hoa ▼ 1.7%). The store-level test in [#5](methodology.md) shows these differences are within noise; provinces are not ranked by growth.

---

## 3. Offline — where does revenue sit within the store chain?

*Dashboard page: OFFLINE*

| | Jan–Aug 2026 | vs Jan–Aug 2025 |
|---|---:|---:|
| Revenue | VND 150.2bn | ▼ 2.3% |
| Sales invoices | 103,238 | ▼ 10.7% |
| AOV (value per sales invoice) | VND 1,452,154 | ▲ 9.4% |
| UPT (items per sales invoice) | 1.70 | 2025: 1.69 · 2024: 1.70 |
| Discount rate | 17.45% | not compared |

**Fewer purchases, unchanged baskets.** AOV rose by roughly as much as product prices did (about 9% and 9.4%); UPT held at 1.69–1.70 for three years. What the data can answer is the **structure** of offline revenue, and that structure has stood still for three years.

> **How to read.** AOV and UPT are computed on sales invoices, unlike "value per transaction" in section 2 (which includes return invoices). Discount rate = discount amount ÷ value of goods before discount, on invoices that did not use loyalty points only: invoices paid with points record a discount of zero even on promotion days, and including them would push the rate artificially low. The invoices counted make up 79.7% of offline sales.

### 3.1 By store: scale and spending power

- **Concentrated in Hanoi.** The top five stores account for 40.9% of offline revenue, the top ten (all in Hanoi) for 66.4%; the top store sells 16.8 times as much as the bottom store.
- **Scale follows market tier.** Each tier-1 store (Hanoi) sells VND 9.58bn on average, tier 2 (Ho Chi Minh City, Hai Phong, Da Nang) VND 4.26bn, tier 3 (the remaining 11 provinces, 12 stores) VND 1.60bn. Hanoi's share held at 70.1–70.3% over three years.
- **Rankings barely move:** no store moved more than 2 places between 2024 and 2026. The ranking is information about scale, not a management scorecard.
- **AOV genuinely differs between stores and follows store characteristics.** AOV in 2026 ranges from VND 946,833 (JM HP 02) to VND 1,692,146 (JM HN 06), a ratio of 1.79. Holding other characteristics equal: tier 2 is about 12% below tier 1, tier 3 about 24% below; stores in shopping malls are about 6% higher, those in city centres about 4% higher; the two Hai Phong stores are about 28% below stores in the same tier. These factors explain about 96% of the AOV differences between stores; the figure is high partly because the Hai Phong factor rests on just 2 stores and is close to a store-specific effect; without it, about 81%. UPT is nearly identical (1.60–1.73), so the difference lies in the price of the items customers choose.

> **How to read.** The YoY column for each store should not be read as performance: the differences are within noise. In 2026, 3 of 29 stores had invoice counts more than 2 standard errors away from the overall decline, while chance alone would produce about 1–2; stores that fell sharply this year tend to be those that fell only slightly the year before (correlation between two consecutive YoY figures −0.66), a sign of random fluctuation rather than a store-specific trend ([#5](methodology.md)). All 29 stores issued fewer invoices and raised AOV in both years. The AOV chart shows spending per visit, not the selling ability of staff; the data does not say why Hai Phong is so much lower. Market tier is how JM allocates resources, not a cause of revenue.

### 3.2 Timing of sales

- **AOV is lower in months with long promotions:** January is 0.93 times the period AOV, July 0.96 times; months with no or only a few promotion days (February; April and May have the 7 days of the 30/4 – 1/5 programme) are about 1.06 times (measured in section 4).
- **Weekends:** average daily revenue is VND 753m (Saturday) and VND 766m (Sunday), against VND 552–570m on weekdays, about 1.34–1.37 times. Weekends are 28.8% of days but generate 35.4% of offline revenue. The five weekdays differ by 2–4% and are not ranked.

### 3.3 By loyalty card tier

| Card tier at time of purchase | Share of revenue | AOV | Invoices per customer |
|---|---:|---:|---:|
| Walk-in (3 shared accounts) | 7.6% | VND 1,398,407 | — |
| Member | 19.6% | VND 1,432,799 | 1.5 |
| Silver | 26.8% | VND 1,461,292 | 3.0 |
| Gold | 17.4% | VND 1,469,832 | 4.4 |
| Platinum | 14.9% | VND 1,459,525 | 6.9 |
| Diamond | 13.7% | VND 1,470,659 | 14.3 |

*Jan–Aug 2026; share of offline sales-invoice revenue of VND 149.9bn; tier at the time of purchase, so one customer can appear in several tiers.*

**The difference between tiers lies in how often customers buy, not in how much they spend each time.** AOV across the five tiers is nearly the same (VND 1.43–1.47m); Diamond has only 978 customers (who bought at Diamond tier during the period; different from the 694 Diamond customers at 31/08/2026 in section 7.4) but generates 13.7% of sales-invoice revenue because each customer bought 14.3 times on average during the period.

> **How to read.** Card tier is determined by spending over 365 days, so "higher tiers spend more" is a definition, not a finding. In 2024 tiers skew towards Member because the data starts on 01/01/2024.

---

## 4. Promotion effectiveness — what do promotions deliver?

*Dashboard page: HIỆU QUẢ KM (Promotion effectiveness)*

Jan–Aug 2026 had 100 promotion days out of 243; these days generated 45.0% of offline revenue and 48.5% of offline sales invoices for the period (same period 2025: 44.7% and 48.1%).

| Programme | Dates | Extra discount | Invoice uplift | Revenue uplift | AOV change | Online order uplift |
|---|---|---:|---:|---:|---:|---:|
| Hot Sale 8/3 (Women's Day) | 1/3–8/3 | 20% | +44.2% ±3.5 | +16.2% ±3.5 | −19.4% | +44.2% |
| Black Friday¹ | 30/10–13/11² | 30%; invoices of 4+ items at least 15% off² | +32.2% ±2.7 | +25.5% ±3.0 | −5.1% | +31.7% |
| Year-end Clearance & Spring | 1/1–25/1 | 15% | +30.2% ±3.2 | +10.1% ±3.2 | −15.5% | +30.4% |
| JM Anniversary | 20/6–15/7 | 15% | +23.2% ±2.3 | +8.5% ±2.4 | −11.9% | +26.7% |
| 30/4 – 1/5 holiday | 27/4–3/5 | 10% | +23.0% ±2.8 | +12.6% ±3.1 | −8.4% | +24.4% |
| Mid-month Sale 15/7 | 16/7–17/7 | 10% | +18.0% ±6.1 | +10.2% ±6.8 | −6.7% | +17.0% |
| End of Season | 20/7–20/8 | 15% | +15.6% ±2.3 | +2.6% ±2.4 | −11.2% | +14.5% |

*Pooled 2024–2026; ± is the approximate half-width of the 95% confidence interval (exact interval in [#5](methodology.md) section [2](methodology.md#2-promotion-effectiveness-daily-quasi-poisson-regression)); compared with ordinary days in the same month, year and day type. ¹ 2024–2025 only, measured against the "New collection launch" baseline (which covers all of Oct–Dec). ² As set in the synthetic data's rules. JM's public programme differs: in 2024 it ran 12–21/11 with buy 2 get 10% off, buy 3 get 15% off; in 2025, buy 2 get 5% off, buy 3 get 10% off, buy 4 get 15% off; both years also had up to 70% off and fixed prices from VND 111k. The deviation is recorded in [#8](synthetic-data-design.md). The dashboard's static image shows only 5 of 7 rows; the full table is here.*

- **Every programme trades order value for purchases, and in general the deeper the discount, the lower the AOV:** an extra 10% off lowers AOV by 6.7–8.4%; 15% by 11.2–15.5%; 20% by 19.4%. There are only 7 data points, and the 15% level alone varies widely, so this is a tendency, not a fixed rate. Revenue uplift is therefore always lower than invoice uplift; End of Season (+15.6% invoices, +2.6% revenue) is barely at the threshold of significance.
- **A quantity condition protects AOV best:** Black Friday lowered AOV by only 5.1% despite the deepest extra discount. Customers add items: UPT during the Black Friday window was 2.11, against 1.71 on the other days of Oct–Dec (2024–2025).
- **Stable across years** (differences between 2024, 2025 and 2026 do not exceed noise: p = 0.28 for invoices, 0.36 for revenue) and **chain-wide:** online order uplift moves in the same direction and at the same scale as offline; the largest gap is JM Anniversary (online +26.7%, offline +23.2% ±2.3).

> **How to read.** Black Friday is not ranked against the other 6 programmes on revenue because the baseline differs. Uplift against ordinary days does not prove that full-year revenue rises by that amount, because some customers may simply shift their purchase date; measuring the true incremental effect needs a control group without the programme. Uplift is estimated with a daily quasi-Poisson regression that separates seasonality, weekends and overlapping programmes ([#5](methodology.md)).

---

## 5. Online — where is online revenue lost?

*Dashboard pages: ONLINE and the detail page TRẢ HÀNG THEO SÀN (Returns by channel)*

| | Jan–Aug 2026 | vs Jan–Aug 2025 |
|---|---:|---:|
| Revenue | VND 53.5bn | ▼ 1.2% |
| Orders placed | 76,769 | ▼ 9.5% |
| Delivered | 56,694 | ▼ 9.5% |
| Orders with revenue retained after returns | 50,583 | ▼ 9.3% |
| Online AOV | VND 1,058,265 | ▲ 8.9% |

An online order passes through three steps: **placed** → **delivered** (not cancelled, not returned to sender) → **revenue retained** (the customer did not return everything; partially returned orders still count).

**Orders fell from the start; no extra leakage in later steps.** Delivered ÷ placed held at 73.85% in both years; revenue retained ÷ delivered was 89.22% (2025: 89.06%). Online AOV rose 8.9%, in line with price increases.

> **How to read.** Online AOV = online revenue ÷ orders with revenue retained; it is not compared with offline AOV or with value per transaction in section 2.

### 5.1 TikTok Shop stands apart from the other channels

| Channel | Revenue retained | Cancelled | Returned to sender | Full return |
|---|---:|---:|---:|---:|
| Admin | 77.22% | 10.27% | 11.75% | 0.76% |
| Website | 72.66% | 9.75% | 12.03% | 5.57% |
| Instagram | 72.15% | 10.26% | 11.46% | 6.12% |
| Facebook | 71.66% | 10.56% | 12.04% | 5.74% |
| Lazada | 70.09% | 10.89% | 11.90% | 7.12% |
| Shopee | 69.08% | 10.02% | 12.37% | 8.53% |
| **TikTok Shop** | **48.24%** | **12.71%** | **25.08%** | **13.97%** |
| All online | 65.89% | 10.90% | 15.25% | 7.96% |

*% of orders placed, Jan–Aug 2026. "Admin" = orders entered by staff.*

- Six channels convert 69–77% of orders placed into revenue; **TikTok Shop only 48.2%**, because returns to sender (25.1%) are about twice the other channels (11.5–12.4%) and full returns (14.0%) are the highest. Measured on delivered orders, TikTok Shop keeps 77.5% of orders, all online 89.2%.
- By value, TikTok Shop loses 22.4% of delivered order value to returns (Shopee 11.1%, Facebook 7.5%, all online 10.8%).
- **A stable condition:** against the same period last year, TikTok Shop's rates changed by less than 1 pp; its cancellation rate was above the online average in all 8 months of 2026.
- TikTok Shop also has the **highest percentage fees**: a 6% transaction fee + 12.5% commission, plus VND 3,000 per order (Shopee 6% + 3%¹; Lazada 4% + 3.99%, plus VND 2,000 per order; Facebook, Instagram, Website and Admin have no channel fee).

*¹ Shopee's commission is inferred, not confirmed from a public source.*

> **How to read.** The three rates use three denominators: cancellations and returns to sender are divided by orders placed; returns after delivery by delivered orders (TikTok Shop 23.6%); returns by value by the value of delivered orders, including shipping (22.4%). The August 2026 return point on the detail page is blank because many orders are still within the return window. Online revenue in the data is recorded at the same rate of order value on every channel, before actual fees; the report does not compare profit between channels.

### 5.2 Return reasons and the online product mix

| Return reason (6,408 orders, Jan–Aug 2026) | Wrong size | Not as described | Defective | Lost in transit | Wrong item sent |
|---|---:|---:|---:|---:|---:|
| Share | 65.7% | 14.5% | 10.2% | 5.1% | 4.6% |

- **Nearly two thirds of returns are due to wrong size;** defects and wrong items sent together make up 14.8%. **The reasons are the same on every channel:** some channels have more returns and some fewer, but the mix of reasons does not differ (0 of 35 channel × reason cells deviate by more than 2 standard errors).
- **Online sells fewer high-priced items:** Outerwear is 27.3% and Sets 24.8% of online sales, below the overall share (32.1% and 26.6%).

> **How to read.** Return reasons do not differ by product, so products are not ranked by return reason. Cancellation reasons are spread evenly across 16 codes on every channel and have no pattern to analyse. The question of why online sells fewer high-priced items (for example, because expensive items need to be tried on in person) cannot be tested with sales data.

---

## 6. Products — where do sales come from within the range?

*Dashboard pages: SẢN PHẨM (Products) and the detail page CHI TIẾT BST (Collection detail)*

| | Jan–Aug 2026 | vs Jan–Aug 2025 |
|---|---:|---:|
| Sales | VND 215.2bn | ▼ 2.0% |
| Units sold | 263,962 | ▼ 10.1% |
| Gross margin | 60.25% | not compared |
| Discount rate | 17.56% | not compared |
| Dead SKUs (no units sold in the last 30 days of the period) | 261 | ▲ 60 (2025: 201) |

- **All product lines and collections fell at the same pace,** with no group changing markedly differently from the overall rate. The ranking of product lines by sales is almost the ranking by price (section 2.3).
- **The rise in dead SKUs is consistent with the whole range selling more slowly, not with a build-up in any group.** In the 12 months before the 30-day window, each SKU sold 63.5 units on average, against 74.2 a year earlier; a slower-selling SKU is more likely to hit zero units in 30 days.
  - *By product line,* the dead-SKU rate in 2026 ranges from 0.96% (Outerwear) to 6.02% (Tops), but it follows sales speed: the lines that sell the most units per SKU (Outerwear 76.9, Sets 71.1) have the fewest dead SKUs. When the expected count is based on each SKU's own sales speed, no product line deviates by more than 2 standard errors.
  - *By collection,* only the TẾT collection has clearly more dead SKUs than expected (19 against 6.6). This is seasonality, not unsold stock: the TẾT collection sells mostly in January (section 6.1), so in August 2026 it sold only 63.7% of its own average monthly volume over the previous 12 months, against 80.1% for the other collections. Allowing for this seasonal slowdown, TẾT's expected count rises to about 16, close to the actual 19. Of the other 19 collections, 18 are within 2 standard errors; STREET exceeds it in the opposite direction (fewer dead SKUs), which can happen by chance when comparing 20 groups.

> **How to read.** A dead SKU is one that has sold before but sold no units in the last 30 days of the period. The expected count is the probability that an SKU sells no line in 30 days at its sales speed over the previous 12 months, scaled by a common factor so that total expected equals total actual (method in [#5](methodology.md)). Gross margin and discount rate exclude orders paid with points (as in section 3). Margin rises year on year mainly because cost per item barely moved (VND 315,389 → 315,999, 2024–2026) while the selling price per item rose 9.9% in 2025 and 9.0% in 2026, so the margin card is not compared with the previous year. Margin differences between collections or product lines do not clearly exceed noise, so margins are not compared between groups.

### 6.1 Collections: number of styles, mix and timing

- **All 20 collections fell,** from ▼ 0.2% (RESORT) to ▼ 4.2% (TWEED), around the overall ▼ 2.0%; each collection has only a few dozen styles, so these differences are noise.
- **The number of styles explains most of the ranking.** Each collection has 23–37 styles (parent products). The TẾT collection (37 styles, VND 17.0bn) sells 2.4 times as much as FOB THU ĐÔNG (autumn–winter; 23 styles, VND 7.0bn), but per style only 1.5 times (VND 458.5m against 303.4m; overall VND 358.6m).
- **The three holiday collections sell most strongly during their own holiday, but still sell all year round.** Holiday windows: TẾT 01–25/01, 14/2 (Valentine's Day) 01–14/02, 8/3 (Women's Day) 01–10/03. The other 17 collections follow the overall monthly pattern closely (at most 1.5 pp apart).

| Collection | Share of sales in peak month | Overall share that month | Sold during promotions 2026 | Discount rate 2026 |
|---|---:|---:|---:|---:|
| TẾT (January) | 40.8% | 18.7% | 58.88% | 19.77% |
| 8/3 (March) | 19.9% | 11.5% | 47.75% | 18.26% |
| 14/2 (February) | 16.7% | 8.3% | 38.43% | 16.66% |
| All collections | | | 44.66% | 17.56% |

- **The discount level of the three collections lines up with whether the holiday falls inside a promotion** (only 3 collections, and the holidays always fall inside a promotion, so the data cannot separate the effect of the collection from the effect of the promotion): the TẾT window overlaps "Year-end Clearance & Spring" (15% extra), the 8/3 window overlaps "Hot Sale 8/3" (20%), and the 14/2 window overlaps no programme. Ranking by share sold during promotions or by discount rate gives the same order: TẾT > 8/3 > 14/2.
- **Product-line mix differs clearly:** the 8/3 collection takes 54.7% of its sales from Sets (overall 26.6%), TRENCH COAT 51.8% from Outerwear. **The online share is almost the same** across collections (27.2–32.8%).

> **How to read.** The Jan–Aug period contains all three holidays but no fourth quarter, so collection rankings within the period lean towards the holiday collections; do not extrapolate to the full year. Collection names do not always match their content (T-SHIRT takes 48.1% of sales from Sets). Each collection keeps the same list of styles across all three years, so year-on-year comparisons of a collection compare the same set of styles.

### 6.2 Top 10 products

**The leaders are stable and concentration is low.** The top 10 account for VND 12.61bn, or 5.86% of sales; the top product (2R36.2601, VND 1.41bn) accounts for 0.65%. The top seven products of 2026 were all in the 2025 top seven; eight of the ten are Outerwear.

> **How to read.** From about rank 8 downwards, ranks change mainly because of noise: each product sells about 600–860 units, so it fluctuates by about ±4% a year on its own, while two adjacent ranks are only 0.3–4.9% apart. For example, the product ranked 11th in 2026 (5S65.2545) rose from 17th even though its units fell 7.3% (less than the overall fall of 10.1%, but still within noise). The report does not discuss which products entered or left the top 10.

---

## 7. Customers — which customers generate revenue, and how many come back?

*Dashboard page: KHÁCH HÀNG (Customers) · Denominator: identified customers. "Purchase day" = a day on which a customer has a transaction with revenue.*

| | Jan–Aug 2026 | vs Jan–Aug 2025 |
|---|---:|---:|
| Purchasing customers | 26,827 | ▼ 2.7% |
| New customers | 1,506 | ▼ 48.9% |
| Repeat rate (≥ 2 purchase days in Jan–Aug 2026) | 71.0% | ▼ 1.0 pp |
| Revenue per customer | VND 7.16m | ▲ 1.0% |
| Identified-customer revenue | VND 192.1bn = 94.3% of company revenue | |

### 7.1 Slightly fewer customers, but each buys less often

The number of customers fell 2.7%, while company transactions fell 10.4%. The gap lies in frequency: 5.28 purchase days per customer on average in Jan–Aug 2026, against 5.70 in the same period of 2025.

> **How to read.** The data shows that each customer bought less often, not why. A "new customer" is a customer appearing for the first time in the data (which starts on 01/01/2024), not necessarily someone buying from JM for the first time, so the early months are inflated (January 2024: 16,330) and then decline. A simulation in [#5](methodology.md) draws transactions from a fixed customer base, with no genuinely new customers arriving; it still shows "new customers" falling 49.5%, almost the same as the actual fall (49.0% on the same count; dashboard 48.9%). This figure is therefore not enough to conclude that customer acquisition has weakened.

### 7.2 The real dividing line: one-time and repeat buyers

| | Jan–Aug 2026 | Jan–Aug 2025 |
|---|---:|---:|
| 1 purchase day: % of customers · % of revenue | 29.0% · 5.3% | 28.0% · 4.6% |
| ≥ 2 purchase days: % of customers · % of revenue | 71.0% · 94.7% | 72.0% · 95.4% |

**Cohort test.** 35,638 customers at 31/08/2025 are given a recency-based churn label, as commonly used in RFM segmentation, then followed for the next 12 months:

| Group at 31/08/2025 | Customers | Came back within 12 months | Revenue per customer, 12 months |
|---|---:|---:|---:|
| Repeat buyers, buying regularly | 18,090 | 85.4% | VND 9.29m |
| Repeat buyers who haven't bought for a while ("at risk") | 7,079 | 92.3% | VND 11.00m |
| Repeat buyers who haven't bought for a long time ("lapsed") | 3,514 | 98.0% | VND 15.86m |
| Bought only once so far | 6,955 | 36.4–38.3% | VND 0.72–0.76m |

- **Customers labelled "at risk" or "lapsed" came back more often than those buying regularly.** The label compares time since the last purchase with the customer's own purchase interval, and this calculation tends to push frequent buyers into the "haven't bought for a while" groups. Comparing within the same number of past purchases, the three groups come back at almost the same rate (for example, with 11–20 repeat purchases: 99.7% in all three groups). The label adds no information beyond purchase count, so the dashboard does not use it.
- **The real gap is between repeat buyers (85–98% came back) and one-time buyers (about 37%).** The 6,955 customers who had bought only once, 19.5% of customers, generated only 1.7% of the following 12 months' revenue of the whole 35,638-customer cohort (VND 5.2bn of 306.9bn). Repeat buyers spend more because they buy more often, not because they spend more each time (the correlation between number of purchases and value per purchase is below +0.1: +0.08 at 31/08/2025, +0.04 at 31/08/2026).
- At 31/08/2026, **6,538 customers had still bought only once** (17.0% of the 38,446 identified customers with a purchase day); they are the target group of recommendation 14 (section 8.3).

> **How to read.** A lesson on how to build the label that also applies to real data: if the purchase interval = time from first purchase to today ÷ number of repeat purchases, a new customer who came back 1–2 times can never qualify as "lapsed", however long they stay silent. Compute the interval from the time between first and last purchase, and check any label with a cohort test like this before spending budget on it ([#5](methodology.md)).

### 7.3 Revenue concentration by customer decile

Customers who bought in the period are ranked by revenue and split into 10 equal groups: **D1** is the 10% who spent the most, … **D10** the 10% who spent the least.

| Group | D1 | D2 | D3 | D4 | D5 | D6–D10 |
|---|---:|---:|---:|---:|---:|---:|
| Revenue Jan–Aug 2026 | VND 78.6bn | VND 37.2bn | VND 24.4bn | VND 17.0bn | VND 12.1bn | |
| Share | 40.9% | 19.4% | 12.7% | 8.8% | 6.3% | about 12% |

**One fifth of customers generate more than 60% of revenue** (D1 + D2 = 60.3%). **The Customer Lifetime Value (CLV) model** predicts the same concentration for the next 12 months: the top 10% (3,212 customers) hold 42.5% of predicted value. The model combines BG/NBD (predicting the number of purchases) and Gamma-Gamma (predicting value per purchase), snapshot at 31/08/2026.

> **How to read.** CLV is used only to rank customers. On the hold-out period (Jan–Aug 2026) the model overpredicted purchases by about 34% (187,593 against 139,905 purchase days, across the 36,940 customers who had bought before the hold-out). Most of the error comes from overall purchase intensity declining over time, which violates the model's assumptions: purchase days per calendar day fell from 772.1 in the calibration period (2024–2025) to 583.0 in the hold-out period, a 24.5% fall that corresponds to an overprediction of about 32% (1 ÷ 0.755 ≈ 1.32). The rest comes from 1,193 one-time buyers whose first purchase fell in the last 131 days of the calibration period: the model predicted 2,427 purchase days for them, against an actual 375. The fall in intensity includes seasonality, since the hold-out covers only Jan–Aug, so it is a consistent explanation rather than proof; the model also ranks no better than simply ranking by past purchase count ([#5](methodology.md)). The 6,328 customers with a single purchase day are not in the model. This is 210 fewer than the 6,538 in section 7.2, because section 7.2 also drops days on which a customer had a return invoice: a customer with one extra exchange day still counts as a one-time buyer there.

### 7.4 Card tiers and customer segments

The dashboard matrix (39,531 customers, snapshot at 31/08/2026) places **card tier** (offline spending over 365 days) next to **customer segment** (frequency, value and recency of the last purchase, across both channels).

- **The top almost coincides:** 688 of 694 Diamond customers are VVIP.
- **The bottom does not:** half of Member customers (11,390 of 22,679) are in "Needs reactivation"; the 1,974 VVIP customers range from Diamond down to Silver. The 4,008 "Outside programme" customers (no offline invoice yet) are mostly "Needs reactivation" (2,637) and "No purchase yet" (796); none are VIP or VVIP.

> **How to read.** "Needs reactivation" is the group whose last purchase was long ago; it is not a churn prediction (section 7.2). The two classifications are kept separate.

---

## 8. Prediction and recommendations

Every figure in this section is a **scenario calculation** ("if … then …") with its formula, inputs (from sections 2–7 or the KB and DB queries in the appendix) and assumptions; none is a firm forecast. Each recommendation has two levels: **conservative** and **expected**. Both levels are the analyst's assumptions, deliberately set low against the observed gap (for example, closing only 25–50% of the TikTok Shop – Shopee gap), because the data contains no experiment showing the actual improvement achievable. In a real business, test at small scale with a control group before scaling up.

### 8.1 Prediction: revenue for Jan–Aug 2027

**Formula:** Revenue 2027 = VND 203.7bn × (1 + change in transactions) × (1 + change in value per transaction); inputs from section 2.

| Scenario | Transactions | Value per transaction | Revenue Jan–Aug 2027 | vs 2026 |
|---|---:|---:|---:|---:|
| A. The 2026 trend repeats | ▼ 10.4% | ▲ 9.3% | VND 199.7bn | ▼ 2.0% |
| B. Prices stop rising | ▼ 10.4% | unchanged | VND 182.6bn | ▼ 10.4% |
| C. Transactions are held | unchanged | ▲ 9.3% | VND 222.7bn | ▲ 9.3% |

The gap between B and C is VND 40.1bn, nearly 20% of one period's revenue: **the number of purchases is the biggest lever.** *Assumptions: the 2026 rates of change repeat for one year; channel mix, product mix and the promotion calendar are unchanged. A one-step extrapolation from three periods; not enough data for a confidence interval.*

### 8.2 Priority table

*Difficulty is a qualitative judgement: Low = operational adjustment; Medium = needs programme design or coordination across teams; High = depends on external partners or major change.*

| # | Recommendation | Impact: conservative → expected | Unit | Difficulty | Priority |
|---:|---|---:|---|---|---|
| 2 | Raise items per offline invoice (add-on selling, bundles) | +VND 1.8bn → +4.4bn | per Jan–Aug period | Low | **1** |
| 6 | Use "buy more, save more" for End of Season | +VND 0.6bn → +1.2bn | per year | Low | **1** |
| 11 | Reduce returns due to wrong size | +VND 0.5bn → +0.9bn | per Jan–Aug period | Low | **1** |
| 10 | Reduce RTS and returns on TikTok Shop | +VND 0.9bn → +1.8bn (after fees +0.7 → +1.5) | per Jan–Aug period | High | **2** |
| 15 | Retain the top 10% of customers | sensitivity¹: losing 5–10% of them = −VND 3.9bn → −7.9bn | per Jan–Aug period | Medium | **2** |
| 14 | Turn one-time buyers into second-time buyers | +VND 0.3bn → +0.6bn | per year | Medium | **2** |
| 4 | Staffing and display to match the weekend rhythm | not quantified | | Low | 3 |
| 1, 3, 5, 7, 8, 9, 12, 13, 16 | Changes to measurement and tracking | no direct revenue | | Low | foundation |

*Priority 1 = clear impact, within the company's control. Priority 2 = large impact or risk, but more effort. "Foundation" recommendations change how things are measured and should run in parallel so the others can be evaluated. Units differ, so compare within the same unit. ¹ Recommendation 15 is a risk if customers are lost, not an expected impact: the data does not show this group's churn rate, so it is not compared directly with the other rows.*

### 8.3 Recommendation details

#### Chain-wide purchases

**1. Make the number of purchases the main target, rather than relying on price rises.** Basis: section 2.1 and scenarios B–C in 8.1. Each 1% of transactions retained ≈ VND 2.0bn per period (= VND 203.7bn × 1%). *Track:* transactions against the same period last year, by month and channel.

#### Offline

**2. Raise items per invoice through add-on selling and bundles.** Basis: UPT held at 1.69–1.70 for three years, while Black Friday shows that a quantity condition can lift UPT to 2.11, i.e. +0.40 items (section 4); AOV = UPT × price per item. A gain of +0.02–0.05 items is only 5–12.5% of that increase.
- *Impact:* offline sales-invoice revenue × ΔUPT ÷ 1.70. Conservative, +0.02 items: **+VND 1.8bn**; expected, +0.05 items: **+VND 4.4bn** per period (= VND 149.9bn × 0.05 ÷ 1.70).
- *Assumptions:* price per item and number of invoices unchanged. Bundles usually come with a discount; that discount has not been deducted, so tests should measure revenue, not just UPT. *Track:* UPT and AOV by store, by month.

**3. Monitor concentration risk in Hanoi, and compare markets by revenue per store.** Sensitivity: a 10% fall in Hanoi reduces offline revenue by VND 10.5bn, or 7.0%. When considering expansion, compare revenue per store and AOV, not total provincial revenue. *Track:* Hanoi's share by month.

**4. Plan staffing and in-store display around the weekend rhythm,** about 1.35 times weekdays (ratio of daily revenue, section 3.2). *Assumption:* staffing needs are proportional to revenue. *Track:* revenue per labour hour.

#### Promotions

**5. Evaluate every programme on revenue uplift, not invoice uplift** (section 4), using the same model.

**6. Bring Black Friday's "buy more, save more" mechanism to End of Season.** JM already uses a tiered quantity mechanism for Black Friday (buy 2, 3, 4 items for progressively deeper discounts), so this extends an existing mechanism rather than designing a new one. Basis: in the data, AOV falls 11.2% during End of Season against 5.1% during Black Friday.
- *Impact:* offline sales-invoice revenue over the 32 days of End of Season 2026 was VND 17.01bn, equivalent to a no-promotion baseline of VND 16.58bn (= 17.01 ÷ 1.026). Keeping the invoice uplift at +15.6%:
  - Expected, AOV falls only 5.1% as at Black Friday (a hypothesis to test: Black Friday is measured against a different baseline, section 4): revenue uplift +9.7% (= 1.156 × 0.949 − 1), an extra **VND 1.18bn** per year.
  - Conservative, AOV falls 8.15% (midway between the two): uplift +6.2%, an extra **VND 0.59bn**.
- *Assumptions:* the new mechanism does not reduce purchases; offline only. *Track:* revenue uplift, AOV and UPT within the window, with a control group of stores.

**7. Plan holiday collections together with the promotion calendar** (section 6.1). Not quantified: the data cannot estimate how a collection's sales would change if its timing moved. *Track:* share sold during promotions and discount rate for each holiday collection.

**8. Use one core promotion calendar for both channels, adjusted per marketplace.** The two channels respond in the same way (section 4), but each marketplace has its own sale calendar, rules and price display, which are harder to keep in sync; check each marketplace's calendar and monitor actual selling prices.

#### Online

**9. Evaluate every channel on revenue remaining after returns and fees, not on orders placed.**

| Channel | Revenue per 100 orders placed | Current % fees | After fees |
|---|---:|---:|---:|
| Admin | VND 81.4m | 0% | VND 81.4m |
| Website | VND 76.6m | 0% | VND 76.6m |
| Facebook | VND 76.2m | 0% | VND 76.2m |
| Instagram | VND 75.8m | 0% | VND 75.8m |
| Lazada | VND 74.0m | 7.99% | VND 68.1m |
| Shopee | VND 73.3m | 9%¹ | VND 66.7m |
| **TikTok Shop** | **VND 51.0m** | **18.5%** | **VND 41.6m** |

*Formula: channel revenue Jan–Aug 2026 ÷ orders placed × 100 × (1 − % fee). Fixed per-order fees not included; revenue in the data is before fees, so the last column is illustrative. ¹ Inferred.* For the same 100 orders placed, TikTok Shop brings in about 62% of Shopee's and 55% of Facebook's revenue after fees. *Track:* revenue after fees per 100 orders placed, by channel, by month.

**10. Reduce returns to sender and customer returns on TikTok Shop.**
- *Impact:* if RTS and full returns fell to Shopee's levels (12.37% and 8.53%), orders with revenue retained would rise from 48.24% to 66.39% (= 100% − 12.71% − 12.37% − 8.53%), i.e. 3,451 more orders out of 19,018 placed × AOV VND 1,057,203 = VND 3.65bn (the full gap, before fees). Conservative, closing 25% of the gap: **+VND 0.9bn**; expected, 50%: **+VND 1.8bn** per period. After the 18.5% percentage fees: +VND 0.7bn and +1.5bn.
- *Assumptions:* cancellation rate and AOV unchanged. Difficulty is high because it depends on delivery carriers and marketplace policy. *Track:* RTS and full returns on TikTok Shop by month.

**11. Reduce returns, starting with size.** Clearer size charts, size suggestions from body measurements, or exchanging sizes instead of returning.
- *Impact:* refunds on returned orders in Jan–Aug 2026 totalled VND 7.05bn; wrong size accounts for 65.7%. Cutting wrong-size returns by 10%: **+VND 0.46bn**; by 20%: **+VND 0.93bn** per period (= 7.05 × 65.7% × 20%).
- *Assumption:* the value of a returned order is the same across reasons. *Track:* wrong-size return rate by product line.

#### Products

**12. Evaluate collections on total sales together with the number of styles and sales per style,** then look at mix and timing before drawing conclusions (section 6.1).

**13. Track dead SKUs against sales speed, not as a raw count.** No group is abnormal at present apart from TẾT, which is seasonal (section 6). Raise an alert when the dead-SKU count of a product line or collection exceeds the expected count based on sales speed by more than 2 standard errors, and exclude holiday collections out of season (such as TẾT in August) to avoid clearing stock by mistake.

#### Customers

**14. Focus retention budget on new customers' second purchase, not on win-back campaigns for customers who have not bought for a while.**
- *Impact:* 6,538 customers have bought only once. According to the test in section 7.2, one-time buyers spent VND 0.747m over the next 12 months, customers who had come back 1–2 times spent VND 1.711m; a difference of VND 0.964m per customer. Conservative, 5% converted: **+VND 0.32bn per year**; expected, 10%: **+VND 0.63bn per year** (= 654 × VND 0.96m). If all were converted: VND 6.30bn per year.
- *Assumptions:* converted customers spend like the group that came back 1–2 times. The data only shows that one-time buyers rarely come back; it does not show that any programme can convert them, and there is no campaign data; a test with a control group is needed. *Track:* share of new customers making a second purchase within 90 days.

**15. Prioritise service and privileges for the top 10% of customers** (D1: VND 78.6bn, 40.9% of identified-customer revenue).
- *Sensitivity:* losing 5% of this group: **−VND 3.9bn**; losing 10% (about 270 of 2,680 customers): **−VND 7.9bn** per period, or 4.1% of identified-customer revenue. *Assumption:* lost customers spend the group average.
- Spot early the customers who will join this group with either the CLV ranking or a ranking by past purchase count: the two give almost the same order (section 7.3), so the simpler one is enough. Read the customer segment across both channels, not only the card tier (section 7.4). *Track:* D1 retention by quarter.

**16. Check every "churn risk" label with a cohort test before spending budget on that group** (section 7.2).

### 8.4 Data needed to go further

- **Store footfall and marketplace traffic:** to know whether transactions fell because fewer people came or because conversion fell.
- **Marketing and operating costs by channel:** to measure promotion effectiveness and profit by store and channel.
- **Actual channel fees charged on each order:** to replace the illustrative calculation in recommendation 9.
- **Cancellation reasons recorded in a controlled way:** to know which cancellations can be addressed.

---

## 9. Data limitations

The full mapping between each finding and the data-generation rule is in **[#8 Synthetic Data Design](synthetic-data-design.md)**.

- **No usable footfall data** (store footfall in the data is derived backwards from invoice counts, see [#8](synthetic-data-design.md)) **and no marketplace traffic:** we know transactions fell, not why.
- **No costs beyond cost of goods; cost per item barely changes over three years:** net profit and marketing effectiveness cannot be computed; gross margin is not compared over time or between groups.
- **Online revenue is recorded at the same rate of order value on every channel,** before actual fees.
- **Some fields have no pattern to analyse:** cancellation reasons are evenly spread; order time and processing time do not differ by channel; return reasons do not differ by channel or product.
- **Customer history starts in January 2024,** so early "new customers" include existing ones; online orders have no customer address.
- **Customer identity across marketplaces and stores:** in a real business, marketplaces do not share customer identities with stores, so the report does not analyse cross-channel customers even though the synthetic data links them.

---

## Appendix A — Sources

Every figure comes from the dashboard or from queries run on BigQuery between 27/10 and 01/11/2026. Code in the repo: the views and tables in `sql/`, the promotion model `models/promo_uplift.py` (section 4) and the CLV model `models/clv_model.py` (section 7.3). The report's own check queries are not included in the repo; the Query column keeps each query's internal code (TQ-1, KH-8…) for reference.

| Section | Content | Dashboard page | Query |
|---|---|---|---|
| 2 | KPIs; full years 2024–2025 | Overview · KPIs | TQ-1 |
| 2.1 | Units sold, price per item, items per transaction; revenue change | Overview · KPIs, revenue waterfall | TQ-1, TQ-2 |
| 2.2 | Revenue and transactions by month | Overview · revenue by month | TQ-3 |
| 2.3 | Province, channel, product line | Overview · three bar charts | TQ-4, TQ-5 |
| 3 | Offline KPIs; 2024 UPT; share of sales without points | Offline · KPIs | dashboard, OF-7 |
| 3.1 | Concentration, scale, rankings; AOV and UPT by store; AOV factors; YoY noise | Offline · revenue by store | OF-1, OF-4, OF-5, OF-6, OF-8 |
| 3.2 | AOV by month, weekends | Offline · by month, by weekday | OF-2 |
| 3.3 | Card tiers | Offline · revenue by card tier | OF-3 |
| 4 | Promotion days and shares; uplift; programme calendar; Black Friday UPT | Promotion effectiveness | dashboard, OF-7, KM-1 (`models/promo_uplift.py`) |
| 5 | Online KPIs; return reasons; online product mix | Online, Returns by channel | dashboard, ON-3 |
| 5.1 | Order status by channel; channel fees; return rate by value | Online · order status; Returns by channel; "channel card" tooltip | ON-1, ON-2, ON-3 |
| 6 | Product KPIs; cost per item; dead SKUs by product line and collection | Products · KPIs | dashboard, DB-1, SP-5 |
| 6.1 | Collections: YoY, number of styles, per style; peak month, mix, online share; style list across years; sold during promotions, discount | Products · collection table; Collection detail | dashboard, SP-2, DB-2 |
| 6.2 | Top 10, fluctuation by units | Products · Top 10 | SP-1, SP-3, SP-4 |
| 7 | Customer KPIs; new customers January 2024; fixed customer base simulation | Customers · KPIs | dashboard, KH-2, KH-6 |
| 7.2 | One-time / repeat; cohort test; one-time buyers in 2026; correlation of purchase count × value per purchase | Customers · one-time and repeat buyers | dashboard, KH-3, KH-4, KH-5 |
| 7.3 | Concentration by decile; CLV; purchase intensity in calibration and hold-out periods; CLV backtest | Customers · revenue concentration | dashboard, KH-1, KH-7, KH-8; CLV `models/clv_model.py` |
| 7.4 | Card tier × segment | Customers · matrix | dashboard |
| 8 | Prediction scenarios and recommendations | — | KB-1 to KB-9; DB-3, DB-4 |

**Rerun on 01/11/2026:** store-level noise (OF-8); return reasons by channel and return rate by value (ON-3); dead SKUs by group (SP-5); the promotion uplift model (KM-1: all 7 programmes, confidence intervals, dispersion 1.48 and 2.77, year p-values 0.28 and 0.36, all matching exactly); the fixed customer base simulation (KH-6); purchase intensity in the CLV calibration and hold-out periods (KH-7); the CLV backtest on the hold-out period (KH-8). The KH-8 rerun reproduced every figure of the original analysis (prediction 185,165 against 185,168; Spearman 0.8214 and 0.8340; D1/D10 lift 58.7x), and also showed that the original analysis was missing predictions for 1,193 customers because the modelling library returned empty values for this group. The figures in section 7.3 have been recomputed on all 36,940 customers: overprediction of 34.09% instead of 32.35%; Spearman 0.8077 against 0.8324 for ranking by past purchase count; the conclusions are unchanged.

**The CLV model** used for ranking (BG/NBD and Gamma-Gamma fitted on all data up to 31/08/2026, run in Python outside BigQuery; results are in the `customer_clv` table) and its checks are presented in [#5](methodology.md) section [6](methodology.md#6-clv-bgnbd-and-gamma-gamma). The correlation between two consecutive store YoY figures was also rerun: −0.66, matching the original analysis.

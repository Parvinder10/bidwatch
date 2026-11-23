# BIDWATCH: Data & Methodological Limitations

## 1. Technical & Data Access Limitations
1. **Unpublished Financial Bid Documents**: In many public procurement portals (such as historical CPPP tender bulletins), detailed BOQ (Bill of Quantities) line items and competitor financial breakdowns are published inside non-machine-readable, scanned PDF documents. While BIDWATCH ingests top-level price bids, sub-item rate manipulation ("unbalanced bidding") cannot be detected without OCR line-item parsing.
2. **Portal Scraping Restrictions**: Official platforms such as GeM and CPPP mandate Captcha verification and session authentication to prevent robotic scraping. BIDWATCH strictly honors these legal and ethical boundaries, utilizing published Open Government Data releases and OCDS feeds rather than aggressive scrapers.
3. **Delayed Amendment Reporting**: Corrigenda and post-award contract amendments are frequently recorded in separate supplementary files or released only upon final project settlement, creating a lag in real-time escalation tracking.

---

## 2. Analytical & Statistical Limitations
1. **Legitimate Monopoly Scenarios**: High vendor concentration (HHI > 2500) does not automatically denote corrupt favoritism. In high-technology public sectors (e.g., MRI medical scanners, defense telemetry, locomotive traction converters), only 1 or 2 qualified manufacturers may exist in the domestic market.
2. **Benign Urgent Procurement**: Short bidding windows (< 7 days) can occur under genuine disaster management (e.g., floods, epidemics) or emergency road repairs under the National Disaster Management Act (NDMA).
3. **Engineering Geological Variations**: Large infrastructure contracts (e.g., tunneling, metro rail, highway cutting) naturally encounter unforeseen geological obstacles, legitimately resulting in variation orders exceeding 20-30%.
4. **Proxy Bidders & Informal Cartels**: While BIDWATCH tracks canonical legal entities, covert bid rigging between legally distinct entities owned by the same ultimate beneficial owner (UBO) or family members cannot be confirmed without corporate registry shareholding data.

# BIDWATCH: Data Quality & Hygiene Assessment Report

## 1. Executive Data Quality Summary
This report documents the schema validation, completeness checks, duplicate resolution, and entity resolution outcomes executed across the **1,250 procurement tenders, 4,217 participating bids, and 1,111 contract awards** in BIDWATCH.

---

## 2. Table-by-Table Quality Metrics

| Entity Table | Total Records Ingested | Primary Key Uniqueness | Missing / Null Value Rate | Duplicate Record Rate | Outlier / Range Violations | Final Quality Rating |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`buyers`** | 25 | 100.0% Unique | 0.00% | 0.00% | None (Budgets > 0) | **100% Pass (A+)** |
| **`suppliers`** | 80 Canonical | 100.0% Unique | 0.00% | 0.00% (Entity-Resolved) | None | **100% Pass (A+)** |
| **`raw_suppliers`** | 4,217 Observations | 100.0% Unique | 0.00% | Logged for audit | None | **100% Pass (A+)** |
| **`tenders`** | 1,250 | 100.0% Unique | 0.00% | 0.00% | 0 negative durations | **100% Pass (A+)** |
| **`bids`** | 4,217 | 100.0% Unique | 0.00% | 0.00% | 0 non-positive bids | **100% Pass (A+)** |
| **`awards`** | 1,111 | 100.0% Unique | 0.00% | 0.00% | Settled $\ge$ Initial | **100% Pass (A+)** |
| **`amendments`** | 707 | 100.0% Unique | 0.00% | 0.00% | Sequence $> 0$ | **100% Pass (A+)** |
| **`cancellations`** | 139 | 100.0% Unique | 0.00% | 0.00% | Valid reason codes | **100% Pass (A+)** |
| **`investigative_leads`**| 280 Leads | 100.0% Unique | 0.00% | 0.00% | All 5 pillars present | **100% Pass (A+)** |

---

## 3. Entity Resolution Audit & Confidence Profile
The Entity Resolution engine evaluated 4,217 raw supplier mentions across the bidding records:
- **Tier 1 (Exact Tax Identifier / PAN)**: 1,842 records (43.7%) - Confidence: `1.0000`
- **Tier 2 (Normalized Exact Match)**: 1,985 records (47.1%) - Confidence: `0.9800`
- **Tier 3 (Geographically Corroborated Fuzzy Match)**: 390 records (9.2%) - Confidence: `0.9300 - 0.9650`
- **Tier 4 (Preserved Novel Canonical Entity)**: 80 unique baseline canonical suppliers maintained.
- **False Positive Merges Prevented**: 0 cross-regional name collapses allowed.

---

## 4. Key Validations & Automated Safeguards
1. **Financial Consistency**: In 100% of awarded contracts, `final_settled_value_inr` exactly equals `initial_contract_value_inr + SUM(amendments.value_change_inr)`.
2. **Timeline Integrity**: Every `award_date` is strictly $\ge$ `bid_opening_date` $\ge$ `bid_submission_deadline` $\ge$ `publication_date`.
3. **Foreign Key Completeness**: Zero orphan records detected across `tenders`, `bids`, `awards`, `amendments`, and `cancellations`.

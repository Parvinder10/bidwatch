# BIDWATCH: Power BI Integration & Modeling Architecture Guide

## 1. Overview & Export Artifacts
BIDWATCH provides native, production-grade integration with **Microsoft Power BI Desktop**. Cleaned, validated, relational datasets are exported directly to:
```
data/processed/powerbi_export/
  ├── buyers.csv
  ├── suppliers.csv
  ├── raw_suppliers.csv
  ├── tenders.csv
  ├── bids.csv
  ├── awards.csv
  ├── amendments.csv
  └── cancellations.csv
```

---

## 2. Ingestion Methods in Power BI Desktop

### Method A: Folder Ingestion (Recommended for Portability)
1. Launch **Power BI Desktop**.
2. Click **Get Data** -> **More...** -> **Folder**.
3. Enter the absolute path to your export directory:
   `C:\Users\parvk\OneDrive\Desktop\bid\data\processed\powerbi_export`
4. Click **Transform Data** (Power Query Editor).
5. For each file, click **Combine** or import each CSV as an individual table.

### Method B: Direct SQLite Database Ingestion
1. Install the official **SQLite ODBC Driver** (32-bit or 64-bit matching your Power BI version).
2. Click **Get Data** -> **ODBC**.
3. Connection String:
   `Driver={SQLite3 ODBC Driver};Database=C:\Users\parvk\OneDrive\Desktop\bid\data\processed\bidwatch.db;`
4. Select the normalized tables (`buyers`, `suppliers`, `tenders`, `bids`, `awards`, `amendments`, `cancellations`).

---

## 3. Recommended Star-Schema Data Model in Power BI

```
         +-----------------+
         |     buyers      | (Dimension)
         +-----------------+
                  | 1
                  |
                  | *
+-----------------+-----------------+
|             tenders               | (Fact / Bridge)
+-----------------+-----------------+
        | 1               | 1
        |                 |
        | *               | 1
+-------+-------+ +-------+-------+
|     bids      | |    awards     | (Fact)
+---------------+ +-------+-------+
        | *               | 1
        |                 |
        | 1               | *
+-------+-------+ +-------+-------+
|   suppliers   | |  amendments   | (Fact Detail)
+---------------+ +---------------+
```

### Table Relationships (Model View):
- `buyers[buyer_id]` 1 -> * `tenders[buyer_id]` (Single direction)
- `tenders[tender_id]` 1 -> 1 `awards[tender_id]` (Both directions)
- `tenders[tender_id]` 1 -> * `bids[tender_id]` (Single direction)
- `suppliers[supplier_id]` 1 -> * `awards[supplier_id]` (Single direction)
- `suppliers[supplier_id]` 1 -> * `bids[supplier_id]` (Single direction)
- `awards[award_id]` 1 -> * `amendments[award_id]` (Single direction)
- `tenders[tender_id]` 1 -> 1 `cancellations[tender_id]` (Single direction)

---

## 4. Key DAX Analytical Measures

Create a dedicated measure table (`_Measures`) and implement the following DAX calculations:

### 1. Total Settled Procurement Spend (₹ Cr)
```dax
Total Spend Cr = 
DIVIDE(
    SUM(awards[final_settled_value_inr]), 
    10000000, 
    0
)
```

### 2. Post-Award Value Escalation (₹ Cr)
```dax
Total Escalation Cr = 
DIVIDE(
    SUM(awards[final_settled_value_inr]) - SUM(awards[initial_contract_value_inr]),
    10000000,
    0
)
```

### 3. Escalation Percentage (%)
```dax
Escalation Pct = 
DIVIDE(
    SUM(awards[final_settled_value_inr]) - SUM(awards[initial_contract_value_inr]),
    SUM(awards[initial_contract_value_inr]),
    0
) * 100
```

### 4. Cancellation Rate (%)
```dax
Cancellation Rate Pct = 
DIVIDE(
    CALCULATE(COUNTROWS(tenders), tenders[status] = "Cancelled"),
    COUNTROWS(tenders),
    0
) * 100
```

### 5. Herfindahl-Hirschman Index (HHI Measure)
```dax
HHI Measure = 
VAR TotalDeptSpend = CALCULATE(SUM(awards[final_settled_value_inr]), ALLSELECTED(suppliers))
RETURN
IF(
    TotalDeptSpend > 0,
    SUMX(
        VALUES(suppliers[supplier_id]),
        VAR SupSpend = CALCULATE(SUM(awards[final_settled_value_inr]))
        VAR SharePct = (SupSpend / TotalDeptSpend) * 100
        RETURN SharePct ^ 2
    ),
    0
)
```

---

## 5. Recommended Power BI Dashboard Layout
1. **Page 1: Executive KPI Scorecard**:
   - Card visuals: Total Spend (₹ Cr), Total Tenders, Cancellation Rate, Total Escalation (₹ Cr).
   - Clustered Bar Chart: Total Spend by Ministry.
   - Donut Chart: Spend by Category (Works, Goods, Services).
   - Line & Clustered Column Chart: Spend & Tender Count over Time (`publication_date`).
2. **Page 2: Vendor Concentration & HHI**:
   - Gauge Visual: HHI Score with color thresholds (Green < 1500, Yellow 1500-2500, Red > 2500).
   - Matrix Visual: Department vs Supplier matrix showing % spend captured.
   - Bar Chart: Top 10 Suppliers by Total Contract Awards.
3. **Page 3: Investigative Watchlist**:
   - Table Visual: Filterable by Severity (High, Elevated, Medium) showing Tender Ref, Department, Winning Supplier, Initial Value, Final Value, Escalation %, and Audit Checklist.

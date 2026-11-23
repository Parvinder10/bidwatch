# BIDWATCH: SQL Analytics Library & Query Documentation

## 1. Overview of Analytical Query Suite
BIDWATCH implements production-grade SQL scripts written for SQLite and PostgreSQL. All queries utilize **Common Table Expressions (CTEs)**, **Window Functions** (`DENSE_RANK`, `SUM() OVER`, `LAG() OVER`), **Multi-Table Joins**, and **Mathematical Exponentiation** to derive procurement intelligence.

---

## 2. Core SQL Scripts Catalog

### Query 01: Department Procurement Spend & Budget Utilization
- **File**: [`sql/01_department_procurement_summary.sql`](file:///c:/Users/parvk/OneDrive/Desktop/bid/sql/01_department_procurement_summary.sql)
- **Analytical Concepts**: Left Joins across `buyers`, `tenders`, and `awards`; `COALESCE` aggregation; `DENSE_RANK()` window ranking.
- **Sample Query Snippet**:
```sql
WITH DeptProcurementMetrics AS (
    SELECT 
        b.buyer_id,
        b.department_name,
        b.budget_allocation_cr,
        COUNT(DISTINCT t.tender_id) AS total_tenders_published,
        COUNT(DISTINCT CASE WHEN t.status = 'Awarded' THEN t.tender_id END) AS tenders_awarded,
        COALESCE(SUM(a.final_settled_value_inr), 0) AS total_settled_awarded_inr
    FROM buyers b
    LEFT JOIN tenders t ON b.buyer_id = t.buyer_id
    LEFT JOIN awards a ON t.tender_id = a.tender_id
    GROUP BY b.buyer_id, b.department_name, b.budget_allocation_cr
)
SELECT 
    department_name,
    ROUND(total_settled_awarded_inr / 10000000.0, 2) AS total_procurement_cr,
    ROUND(((total_settled_awarded_inr / 10000000.0) / budget_allocation_cr) * 100.0, 2) AS budget_utilization_pct,
    DENSE_RANK() OVER (ORDER BY total_settled_awarded_inr DESC) AS spending_rank
FROM DeptProcurementMetrics;
```

---

### Query 02: Supplier Market Share & Cumulative Dominance (Pareto Analysis)
- **File**: [`sql/02_supplier_market_share_top_winners.sql`](file:///c:/Users/parvk/OneDrive/Desktop/bid/sql/02_supplier_market_share_top_winners.sql)
- **Analytical Concepts**: Cross Join with total market spend CTE; cumulative window sum (`SUM(...) OVER (ORDER BY ... ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`).
- **Sample Query Snippet**:
```sql
SELECT 
    sa.canonical_name,
    ROUND(sa.supplier_total_value_inr / 10000000.0, 2) AS total_won_cr,
    ROUND((sa.supplier_total_value_inr * 100.0) / tm.total_market_value_inr, 2) AS market_share_pct,
    ROUND(
        SUM(sa.supplier_total_value_inr * 100.0 / tm.total_market_value_inr) 
        OVER (ORDER BY sa.supplier_total_value_inr DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 
        2
    ) AS cumulative_market_share_pct
FROM SupplierAggregates sa
CROSS JOIN TotalMarket tm;
```

---

### Query 04: Supplier Concentration via Herfindahl-Hirschman Index (HHI)
- **File**: [`sql/04_supplier_concentration_hhi.sql`](file:///c:/Users/parvk/OneDrive/Desktop/bid/sql/04_supplier_concentration_hhi.sql)
- **Analytical Concepts**: Mathematical square exponentiation `POWER((share * 100), 2)`; department grouping; DOJ antitrust threshold segmentation.
- **Sample Query Snippet**:
```sql
-- Formal HHI calculation per Department:
HHI_Calculations AS (
    SELECT 
        d.department_name,
        ROUND(
            SUM(
                POWER((sds.supplier_dept_spend_inr * 100.0) / d.total_dept_spend_inr, 2)
            ), 2
        ) AS hhi_score
    FROM DeptTotalSpend d
    JOIN SupplierDeptShare sds ON d.buyer_id = sds.buyer_id
    GROUP BY d.department_name
)
SELECT 
    department_name,
    hhi_score,
    CASE 
        WHEN hhi_score > 2500 THEN 'HIGHLY_CONCENTRATED (Oligopoly / Capture Risk)'
        WHEN hhi_score >= 1500 THEN 'MODERATELY_CONCENTRATED'
        ELSE 'COMPETITIVE / UNCONCENTRATED'
    END AS concentration_category
FROM HHI_Calculations;
```

---

### Query 06: Contract Value Escalation & Post-Award Amendments
- **File**: [`sql/06_contract_amendment_escalation.sql`](file:///c:/Users/parvk/OneDrive/Desktop/bid/sql/06_contract_amendment_escalation.sql)
- **Analytical Concepts**: Initial vs settled contract value delta; aggregation across multiple amendment rows; cost overrun classification tiers.
- **Sample Query Snippet**:
```sql
SELECT 
    t.tender_reference_no,
    s.canonical_name AS supplier_name,
    ROUND(a.initial_contract_value_inr / 100000.0, 2) AS initial_lakhs,
    ROUND(a.final_settled_value_inr / 100000.0, 2) AS final_lakhs,
    ROUND(((a.final_settled_value_inr - a.initial_contract_value_inr) * 100.0) / a.initial_contract_value_inr, 2) AS escalation_pct,
    COUNT(amd.amendment_id) AS amendment_count
FROM awards a
JOIN tenders t ON a.tender_id = t.tender_id
JOIN suppliers s ON a.supplier_id = s.supplier_id
LEFT JOIN amendments amd ON a.award_id = amd.award_id
GROUP BY t.tender_reference_no, s.canonical_name, a.initial_contract_value_inr, a.final_settled_value_inr
HAVING COUNT(amd.amendment_id) > 0;
```

---

### Query 08: Temporal Spending Trends (MoM and YoY Growth)
- **File**: [`sql/08_time_trends_mom_yoy.sql`](file:///c:/Users/parvk/OneDrive/Desktop/bid/sql/08_time_trends_mom_yoy.sql)
- **Analytical Concepts**: Date substring extraction; `LAG(..., 1)` for prior month; `LAG(..., 12)` for prior year same-month growth rate computation.
- **Sample Query Snippet**:
```sql
SELECT 
    year_month,
    monthly_spend_inr,
    LAG(monthly_spend_inr, 1) OVER (ORDER BY year_month) AS prev_month_spend,
    LAG(monthly_spend_inr, 12) OVER (ORDER BY year_month) AS prev_year_same_month_spend,
    ROUND(((monthly_spend_inr - LAG(monthly_spend_inr, 1) OVER (ORDER BY year_month)) * 100.0) / 
          LAG(monthly_spend_inr, 1) OVER (ORDER BY year_month), 2) AS mom_growth_pct
FROM MonthlyProcurement;
```

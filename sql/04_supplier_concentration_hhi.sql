-- ==============================================================================
-- Query 04: Supplier Concentration Index (Herfindahl-Hirschman Index - HHI)
-- Uses: CTEs, Subqueries, Square Exponentiation, DOJ/Antitrust Classification
-- Purpose: Measures the degree of vendor monopoly / oligopoly within each 
--          department's procurement ecosystem using the formal HHI metric.
-- Standard Thresholds:
--   - HHI < 1500: Highly Competitive / Unconcentrated
--   - 1500 <= HHI <= 2500: Moderately Concentrated
--   - HHI > 2500: Highly Concentrated / Oligopolistic (Investigative Flag)
-- ==============================================================================

WITH DeptTotalSpend AS (
    SELECT 
        t.buyer_id,
        b.department_name,
        b.ministry,
        COUNT(DISTINCT a.award_id) AS total_contracts,
        COUNT(DISTINCT a.supplier_id) AS distinct_winning_suppliers,
        SUM(a.final_settled_value_inr) AS total_dept_spend_inr
    FROM tenders t
    JOIN awards a ON t.tender_id = a.tender_id
    JOIN buyers b ON t.buyer_id = b.buyer_id
    GROUP BY t.buyer_id, b.department_name, b.ministry
),
SupplierDeptShare AS (
    SELECT 
        t.buyer_id,
        a.supplier_id,
        SUM(a.final_settled_value_inr) AS supplier_dept_spend_inr
    FROM tenders t
    JOIN awards a ON t.tender_id = a.tender_id
    GROUP BY t.buyer_id, a.supplier_id
),
HHI_Calculations AS (
    SELECT 
        d.buyer_id,
        d.department_name,
        d.ministry,
        d.total_contracts,
        d.distinct_winning_suppliers,
        d.total_dept_spend_inr,
        -- HHI = Sum of (market_share_percentage)^2
        ROUND(
            SUM(
                POWER((sds.supplier_dept_spend_inr * 100.0) / d.total_dept_spend_inr, 2)
            ), 2
        ) AS hhi_score
    FROM DeptTotalSpend d
    JOIN SupplierDeptShare sds ON d.buyer_id = sds.buyer_id
    GROUP BY 
        d.buyer_id, 
        d.department_name, 
        d.ministry, 
        d.total_contracts, 
        d.distinct_winning_suppliers, 
        d.total_dept_spend_inr
)
SELECT 
    buyer_id,
    department_name,
    ministry,
    total_contracts,
    distinct_winning_suppliers,
    ROUND(total_dept_spend_inr / 10000000.0, 2) AS total_dept_spend_cr,
    hhi_score,
    CASE 
        WHEN hhi_score > 2500 THEN 'HIGHLY_CONCENTRATED (Oligopoly / Capture Risk)'
        WHEN hhi_score >= 1500 THEN 'MODERATELY_CONCENTRATED'
        ELSE 'COMPETITIVE / UNCONCENTRATED'
    END AS concentration_category,
    CASE 
        WHEN hhi_score > 2500 THEN 'PRIORITY_INVESTIGATION'
        WHEN hhi_score >= 1800 THEN 'ROUTINE_AUDIT'
        ELSE 'LOW_RISK'
    END AS investigative_audit_priority
FROM HHI_Calculations
ORDER BY hhi_score DESC;

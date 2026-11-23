-- ==============================================================================
-- Query 01: Total Procurement Value and Budget Utilization by Department
-- Uses: CTEs, Aggregations, Joins, Window Functions, Rounding
-- Purpose: Analyzes total spend, awarded tenders, average contract size, and 
--          effective expenditure vs allocated budget across government buyers.
-- ==============================================================================

WITH DeptProcurementMetrics AS (
    SELECT 
        b.buyer_id,
        b.department_name,
        b.ministry,
        b.state_region,
        b.budget_allocation_cr,
        COUNT(DISTINCT t.tender_id) AS total_tenders_published,
        COUNT(DISTINCT CASE WHEN t.status = 'Awarded' THEN t.tender_id END) AS tenders_awarded,
        COUNT(DISTINCT CASE WHEN t.status = 'Cancelled' THEN t.tender_id END) AS tenders_cancelled,
        COALESCE(SUM(a.initial_contract_value_inr), 0) AS total_initial_awarded_inr,
        COALESCE(SUM(a.final_settled_value_inr), 0) AS total_settled_awarded_inr,
        COALESCE(AVG(a.final_settled_value_inr), 0) AS avg_contract_value_inr
    FROM buyers b
    LEFT JOIN tenders t ON b.buyer_id = t.buyer_id
    LEFT JOIN awards a ON t.tender_id = a.tender_id
    GROUP BY b.buyer_id, b.department_name, b.ministry, b.state_region, b.budget_allocation_cr
)
SELECT 
    buyer_id,
    department_name,
    ministry,
    state_region,
    budget_allocation_cr,
    total_tenders_published,
    tenders_awarded,
    tenders_cancelled,
    ROUND(total_settled_awarded_inr / 10000000.0, 2) AS total_procurement_cr,
    ROUND(avg_contract_value_inr / 100000.0, 2) AS avg_contract_lakhs,
    ROUND(
        CASE 
            WHEN budget_allocation_cr > 0 
            THEN ((total_settled_awarded_inr / 10000000.0) / budget_allocation_cr) * 100.0 
            ELSE 0.0 
        END, 2
    ) AS budget_utilization_pct,
    DENSE_RANK() OVER (ORDER BY total_settled_awarded_inr DESC) AS spending_rank
FROM DeptProcurementMetrics
ORDER BY total_settled_awarded_inr DESC;

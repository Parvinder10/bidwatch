-- ==============================================================================
-- Query 05: Tender Cancellation Rates and Annulment Reason Distribution
-- Uses: CTEs, Conditional Aggregation, Group By, Cross Joins
-- Purpose: Identifies departments with abnormally frequent cancellations,
--          which often correlate with bid manipulation or specification engineering.
-- ==============================================================================

WITH DeptTenderStatusCounts AS (
    SELECT 
        b.buyer_id,
        b.department_name,
        b.ministry,
        COUNT(t.tender_id) AS total_tenders,
        SUM(CASE WHEN t.status = 'Awarded' THEN 1 ELSE 0 END) AS awarded_count,
        SUM(CASE WHEN t.status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_count,
        SUM(CASE WHEN t.status = 'Cancelled' THEN t.estimated_value_inr ELSE 0 END) AS cancelled_value_inr,
        SUM(t.estimated_value_inr) AS total_tender_value_inr
    FROM buyers b
    JOIN tenders t ON b.buyer_id = t.buyer_id
    GROUP BY b.buyer_id, b.department_name, b.ministry
)
SELECT 
    buyer_id,
    department_name,
    ministry,
    total_tenders,
    awarded_count,
    cancelled_count,
    ROUND((cancelled_count * 100.0) / total_tenders, 2) AS cancellation_rate_pct,
    ROUND(cancelled_value_inr / 10000000.0, 2) AS cancelled_value_cr,
    ROUND((cancelled_value_inr * 100.0) / total_tender_value_inr, 2) AS cancelled_value_share_pct,
    CASE 
        WHEN (cancelled_count * 100.0) / total_tenders >= 20.0 THEN 'CHRONIC_CANCELLATIONS (High Risk)'
        WHEN (cancelled_count * 100.0) / total_tenders >= 12.0 THEN 'ELEVATED_CANCELLATIONS'
        ELSE 'NORMAL_BASELINE'
    END AS cancellation_risk_flag
FROM DeptTenderStatusCounts
WHERE total_tenders >= 15
ORDER BY cancellation_rate_pct DESC;

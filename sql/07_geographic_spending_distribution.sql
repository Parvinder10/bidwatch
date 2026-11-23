-- ==============================================================================
-- Query 07: Geographic Spending Distribution & Interstate Procurement Inflow/Outflow
-- Uses: CTEs, Conditional Aggregation, Group By, Cross Joins
-- Purpose: Evaluates geographic procurement flows between procuring buyer states
--          and vendor domicile states, tracking local retention vs interstate spend.
-- ==============================================================================

WITH GeographicPairs AS (
    SELECT 
        b.state_region AS buyer_state,
        s.state_region AS supplier_state,
        CASE WHEN b.state_region = s.state_region THEN 1 ELSE 0 END AS is_local_award,
        COUNT(a.award_id) AS total_contracts,
        SUM(a.final_settled_value_inr) AS total_value_inr
    FROM awards a
    JOIN tenders t ON a.tender_id = t.tender_id
    JOIN buyers b ON t.buyer_id = b.buyer_id
    JOIN suppliers s ON a.supplier_id = s.supplier_id
    GROUP BY b.state_region, s.state_region, is_local_award
),
BuyerStateTotals AS (
    SELECT 
        buyer_state,
        SUM(total_contracts) AS state_total_contracts,
        SUM(total_value_inr) AS state_total_spend_inr
    FROM GeographicPairs
    GROUP BY buyer_state
)
SELECT 
    gp.buyer_state,
    gp.supplier_state,
    CASE WHEN gp.is_local_award = 1 THEN 'DOMESTIC / INTRA-STATE' ELSE 'INTER-STATE OUTFLOW' END AS flow_type,
    gp.total_contracts,
    ROUND(gp.total_value_inr / 10000000.0, 2) AS value_cr,
    ROUND((gp.total_value_inr * 100.0) / bst.state_total_spend_inr, 2) AS pct_of_buyer_state_spend
FROM GeographicPairs gp
JOIN BuyerStateTotals bst ON gp.buyer_state = bst.buyer_state
ORDER BY gp.buyer_state ASC, gp.total_value_inr DESC;

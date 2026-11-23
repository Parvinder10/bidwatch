-- ==============================================================================
-- Query 02: Supplier Market Share and Cumulative Dominance
-- Uses: CTEs, Window Functions (SUM OVER, DENSE_RANK), Partitioning, Aggregation
-- Purpose: Identifies top suppliers by awarded contract value, computes individual
--          market share percentage and running cumulative market concentration.
-- ==============================================================================

WITH TotalMarket AS (
    SELECT 
        COALESCE(SUM(final_settled_value_inr), 1.0) AS total_market_value_inr,
        COUNT(DISTINCT award_id) AS total_contracts_awarded
    FROM awards
),
SupplierAggregates AS (
    SELECT 
        s.supplier_id,
        s.canonical_name,
        s.registration_type,
        s.state_region,
        s.is_msme,
        COUNT(DISTINCT a.award_id) AS contracts_won_count,
        COUNT(DISTINCT t.buyer_id) AS distinct_buyers_served,
        SUM(a.initial_contract_value_inr) AS supplier_initial_value_inr,
        SUM(a.final_settled_value_inr) AS supplier_total_value_inr,
        AVG(a.final_settled_value_inr) AS avg_contract_size_inr
    FROM suppliers s
    JOIN awards a ON s.supplier_id = a.supplier_id
    JOIN tenders t ON a.tender_id = t.tender_id
    GROUP BY s.supplier_id, s.canonical_name, s.registration_type, s.state_region, s.is_msme
)
SELECT 
    sa.supplier_id,
    sa.canonical_name,
    sa.registration_type,
    sa.state_region,
    CASE WHEN sa.is_msme = 1 THEN 'Yes' ELSE 'No' END AS is_msme_label,
    sa.contracts_won_count,
    sa.distinct_buyers_served,
    ROUND(sa.supplier_total_value_inr / 10000000.0, 2) AS total_won_cr,
    ROUND(sa.avg_contract_size_inr / 100000.0, 2) AS avg_contract_lakhs,
    ROUND((sa.supplier_total_value_inr * 100.0) / tm.total_market_value_inr, 2) AS market_share_pct,
    ROUND(
        SUM(sa.supplier_total_value_inr * 100.0 / tm.total_market_value_inr) 
        OVER (ORDER BY sa.supplier_total_value_inr DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 
        2
    ) AS cumulative_market_share_pct,
    DENSE_RANK() OVER (ORDER BY sa.supplier_total_value_inr DESC) AS market_rank
FROM SupplierAggregates sa
CROSS JOIN TotalMarket tm
ORDER BY sa.supplier_total_value_inr DESC;

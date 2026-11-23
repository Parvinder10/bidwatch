-- ==============================================================================
-- Query 03: Repeat Supplier Awards & Relationship Entrenchment
-- Uses: CTEs, Group By with Multiple Hierarchies, Window Ranking
-- Purpose: Identifies high-frequency pairing between specific government buyers
--          and suppliers, highlighting repeat award clusters for investigative review.
-- ==============================================================================

WITH BuyerTotals AS (
    SELECT 
        b.buyer_id,
        b.department_name,
        COUNT(DISTINCT a.award_id) AS total_buyer_awards,
        SUM(a.final_settled_value_inr) AS total_buyer_spend_inr
    FROM buyers b
    JOIN tenders t ON b.buyer_id = t.buyer_id
    JOIN awards a ON t.tender_id = a.tender_id
    GROUP BY b.buyer_id, b.department_name
),
BuyerSupplierPairs AS (
    SELECT 
        b.buyer_id,
        b.department_name,
        s.supplier_id,
        s.canonical_name AS supplier_name,
        s.state_region AS supplier_region,
        b.state_region AS buyer_region,
        COUNT(DISTINCT a.award_id) AS awards_won_from_buyer,
        SUM(a.final_settled_value_inr) AS spend_captured_inr,
        MIN(a.award_date) AS first_award_date,
        MAX(a.award_date) AS latest_award_date
    FROM buyers b
    JOIN tenders t ON b.buyer_id = t.buyer_id
    JOIN awards a ON t.tender_id = a.tender_id
    JOIN suppliers s ON a.supplier_id = s.supplier_id
    GROUP BY b.buyer_id, b.department_name, s.supplier_id, s.canonical_name, s.state_region, b.state_region
)
SELECT 
    bsp.buyer_id,
    bsp.department_name,
    bsp.supplier_id,
    bsp.supplier_name,
    bsp.awards_won_from_buyer,
    bt.total_buyer_awards,
    ROUND((bsp.awards_won_from_buyer * 100.0) / bt.total_buyer_awards, 2) AS award_win_share_pct,
    ROUND(bsp.spend_captured_inr / 10000000.0, 2) AS spend_captured_cr,
    ROUND((bsp.spend_captured_inr * 100.0) / bt.total_buyer_spend_inr, 2) AS buyer_spend_share_pct,
    bsp.first_award_date,
    bsp.latest_award_date,
    CASE 
        WHEN (bsp.spend_captured_inr * 100.0) / bt.total_buyer_spend_inr >= 50.0 THEN 'CRITICAL_CONCENTRATION'
        WHEN (bsp.spend_captured_inr * 100.0) / bt.total_buyer_spend_inr >= 30.0 THEN 'ELEVATED_CONCENTRATION'
        ELSE 'STANDARD'
    END AS concentration_flag
FROM BuyerSupplierPairs bsp
JOIN BuyerTotals bt ON bsp.buyer_id = bt.buyer_id
WHERE bsp.awards_won_from_buyer >= 3
ORDER BY buyer_spend_share_pct DESC, bsp.awards_won_from_buyer DESC;

-- ==============================================================================
-- Query 09: Supplier Participation, Win Rates, and Single-Bidder Awards
-- Uses: CTEs, Conditional Aggregation, Ratio Computations
-- Purpose: Analyzes supplier bidding behavior, conversion win rates, and reveals
--          suppliers that predominantly win in single-bidder non-competitive tenders.
-- ==============================================================================

WITH TenderBidCounts AS (
    SELECT 
        tender_id,
        COUNT(bid_id) AS total_bidders_on_tender
    FROM bids
    GROUP BY tender_id
),
SupplierParticipationMetrics AS (
    SELECT 
        s.supplier_id,
        s.canonical_name,
        s.state_region,
        s.is_msme,
        COUNT(b.bid_id) AS total_bids_submitted,
        SUM(b.is_winning_bid) AS total_wins,
        SUM(CASE WHEN b.is_winning_bid = 1 AND tbc.total_bidders_on_tender = 1 THEN 1 ELSE 0 END) AS single_bidder_wins,
        SUM(CASE WHEN b.technical_qualified = 1 THEN 1 ELSE 0 END) AS tech_qualified_bids,
        SUM(CASE WHEN b.is_winning_bid = 1 THEN b.bid_amount_inr ELSE 0 END) AS total_awarded_bid_value_inr
    FROM suppliers s
    JOIN bids b ON s.supplier_id = b.supplier_id
    JOIN TenderBidCounts tbc ON b.tender_id = tbc.tender_id
    GROUP BY s.supplier_id, s.canonical_name, s.state_region, s.is_msme
)
SELECT 
    supplier_id,
    canonical_name,
    state_region,
    CASE WHEN is_msme = 1 THEN 'Yes' ELSE 'No' END AS is_msme,
    total_bids_submitted,
    total_wins,
    ROUND((total_wins * 100.0) / total_bids_submitted, 2) AS win_rate_pct,
    single_bidder_wins,
    ROUND(
        CASE 
            WHEN total_wins > 0 
            THEN (single_bidder_wins * 100.0) / total_wins 
            ELSE 0.0 
        END, 2
    ) AS single_bidder_win_share_pct,
    ROUND((tech_qualified_bids * 100.0) / total_bids_submitted, 2) AS tech_qualification_rate_pct,
    ROUND(total_awarded_bid_value_inr / 10000000.0, 2) AS total_awarded_cr,
    CASE 
        WHEN total_wins >= 5 AND (single_bidder_wins * 100.0) / total_wins >= 40.0 
            THEN 'SUSPECT_SINGLE_BIDDER_DOMINANCE'
        WHEN (total_wins * 100.0) / total_bids_submitted >= 70.0 AND total_bids_submitted >= 10 
            THEN 'ANOMALOUS_HIGH_WIN_RATE'
        ELSE 'NORMAL_COMPETITIVE_PROFILE'
    END AS participation_risk_classification
FROM SupplierParticipationMetrics
WHERE total_bids_submitted >= 5
ORDER BY total_wins DESC, win_rate_pct DESC;

-- ==============================================================================
-- Query 06: Contract Amendment Frequency & Cost Overrun Escalation
-- Uses: CTEs, Subqueries, Joins, Window Functions, Filtered Aggregations
-- Purpose: Uncovers contracts that were won on an artificially low bid and then
--          escalated substantially post-award via repeated contract amendments.
-- ==============================================================================

WITH ContractEscalationData AS (
    SELECT 
        a.award_id,
        a.tender_id,
        t.tender_reference_no,
        t.category,
        b.buyer_id,
        b.department_name,
        s.supplier_id,
        s.canonical_name AS supplier_name,
        a.award_date,
        a.initial_contract_value_inr,
        a.final_settled_value_inr,
        (a.final_settled_value_inr - a.initial_contract_value_inr) AS net_escalation_inr,
        ROUND(
            ((a.final_settled_value_inr - a.initial_contract_value_inr) * 100.0) / a.initial_contract_value_inr, 
            2
        ) AS escalation_percentage,
        COUNT(amd.amendment_id) AS amendment_count,
        COALESCE(SUM(amd.time_extension_days), 0) AS total_delay_days
    FROM awards a
    JOIN tenders t ON a.tender_id = t.tender_id
    JOIN buyers b ON t.buyer_id = b.buyer_id
    JOIN suppliers s ON a.supplier_id = s.supplier_id
    LEFT JOIN amendments amd ON a.award_id = amd.award_id
    GROUP BY 
        a.award_id, a.tender_id, t.tender_reference_no, t.category,
        b.buyer_id, b.department_name, s.supplier_id, s.canonical_name,
        a.award_date, a.initial_contract_value_inr, a.final_settled_value_inr
)
SELECT 
    award_id,
    tender_reference_no,
    category,
    department_name,
    supplier_name,
    award_date,
    ROUND(initial_contract_value_inr / 100000.0, 2) AS initial_value_lakhs,
    ROUND(final_settled_value_inr / 100000.0, 2) AS final_value_lakhs,
    ROUND(net_escalation_inr / 100000.0, 2) AS net_escalation_lakhs,
    escalation_percentage,
    amendment_count,
    total_delay_days,
    CASE 
        WHEN escalation_percentage >= 50.0 THEN 'CRITICAL_COST_OVERRUN (>50%)'
        WHEN escalation_percentage >= 25.0 THEN 'SUBSTANTIAL_COST_OVERRUN (25-50%)'
        WHEN escalation_percentage > 10.0 THEN 'MODERATE_ESCALATION (10-25%)'
        ELSE 'NORMAL_VARIATION (<=10%)'
    END AS escalation_tier,
    DENSE_RANK() OVER (ORDER BY escalation_percentage DESC) AS escalation_rank
FROM ContractEscalationData
WHERE amendment_count > 0
ORDER BY escalation_percentage DESC;

-- ==============================================================================
-- Query 08: Temporal Trends - Month-over-Month (MoM) & Year-over-Year (YoY)
-- Uses: CTEs, Date Substrings/Formatting, Window Functions (LAG, OVER), Growth Calc
-- Purpose: Uncovers seasonal procurement surges (such as March fiscal year-end spikes)
--          and long-term budgetary trends across multi-year procurement periods.
-- ==============================================================================

WITH MonthlyProcurement AS (
    SELECT 
        SUBSTR(a.award_date, 1, 7) AS year_month,
        SUBSTR(a.award_date, 1, 4) AS award_year,
        SUBSTR(a.award_date, 6, 2) AS award_month,
        COUNT(a.award_id) AS contracts_awarded,
        SUM(a.final_settled_value_inr) AS monthly_spend_inr
    FROM awards a
    GROUP BY year_month, award_year, award_month
),
MonthlyWithLags AS (
    SELECT 
        year_month,
        award_year,
        award_month,
        contracts_awarded,
        monthly_spend_inr,
        -- Prior month spend
        LAG(monthly_spend_inr, 1) OVER (ORDER BY year_month) AS prev_month_spend_inr,
        -- Prior year same month spend (lag 12 months)
        LAG(monthly_spend_inr, 12) OVER (ORDER BY year_month) AS prev_year_same_month_spend_inr
    FROM MonthlyProcurement
)
SELECT 
    year_month,
    award_year,
    award_month,
    contracts_awarded,
    ROUND(monthly_spend_inr / 10000000.0, 2) AS monthly_spend_cr,
    ROUND(prev_month_spend_inr / 10000000.0, 2) AS prev_month_spend_cr,
    ROUND(
        CASE 
            WHEN prev_month_spend_inr > 0 
            THEN ((monthly_spend_inr - prev_month_spend_inr) * 100.0) / prev_month_spend_inr 
            ELSE NULL 
        END, 2
    ) AS mom_spend_growth_pct,
    ROUND(
        CASE 
            WHEN prev_year_same_month_spend_inr > 0 
            THEN ((monthly_spend_inr - prev_year_same_month_spend_inr) * 100.0) / prev_year_same_month_spend_inr 
            ELSE NULL 
        END, 2
    ) AS yoy_spend_growth_pct
FROM MonthlyWithLags
ORDER BY year_month ASC;

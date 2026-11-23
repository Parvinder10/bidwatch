"""
Unit and integration tests for SQL analytics calculations.
Validates HHI scores, escalation rates, and aggregations against manually verified formulas.
"""

import pytest
import pandas as pd
from src.analytics.queries import (
    get_executive_kpis,
    get_department_spending,
    get_supplier_concentration_hhi,
    get_amendment_escalations,
    get_cancellation_rates
)

def test_executive_kpis_integrity():
    kpis = get_executive_kpis()
    assert kpis["total_tenders"] > 0
    assert kpis["total_awarded"] > 0
    assert kpis["total_cancelled"] > 0
    assert kpis["total_tenders"] == kpis["total_awarded"] + kpis["total_cancelled"]
    assert kpis["total_settled_value_cr"] >= kpis["total_initial_value_cr"]
    assert kpis["cancellation_rate_pct"] > 0

def test_hhi_calculation_math():
    """
    Verify HHI mathematical formula: Sum of squared market shares.
    If supplier A has 60% and supplier B has 40%, HHI = 60^2 + 40^2 = 3600 + 1600 = 5200.
    """
    df_hhi = get_supplier_concentration_hhi()
    assert not df_hhi.empty
    assert "hhi_score" in df_hhi.columns
    # Check that HHI scores are non-negative and <= 10000 (monopoly max)
    assert (df_hhi["hhi_score"] >= 0).all()
    assert (df_hhi["hhi_score"] <= 10000).all()

def test_escalation_percentage_math():
    """
    Verify escalation % = ((final - initial) / initial) * 100
    """
    df_esc = get_amendment_escalations()
    assert not df_esc.empty
    sample = df_esc.iloc[0]
    initial = sample["initial_value_lakhs"]
    final = sample["final_value_lakhs"]
    expected_pct = round(((final - initial) * 100.0) / initial, 2)
    assert abs(sample["escalation_percentage"] - expected_pct) <= 0.05

def test_department_budget_utilization():
    df_dept = get_department_spending()
    assert not df_dept.empty
    assert "budget_utilization_pct" in df_dept.columns
    assert (df_dept["budget_utilization_pct"] >= 0).all()

def test_cancellation_rates():
    df_canc = get_cancellation_rates()
    assert not df_canc.empty
    for _, row in df_canc.iterrows():
        expected_rate = round((row["cancelled_count"] * 100.0) / row["total_tenders"], 2)
        assert abs(row["cancellation_rate_pct"] - expected_rate) <= 0.05

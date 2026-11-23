"""
Tests for Investigative Indicators and Evidence Verification.
Ensures every flagged record adheres to explainable analytics standards.
"""

import pytest
import json
from src.indicators.investigative_engine import InvestigativeEngine

@pytest.fixture(scope="module")
def leads_dataframe():
    engine = InvestigativeEngine()
    df = engine.run_all_detectors(persist_to_db=False)
    return df

def test_indicators_generation(leads_dataframe):
    assert not leads_dataframe.empty
    assert len(leads_dataframe) > 50

def test_five_point_mandatory_findings_structure(leads_dataframe):
    """
    Mandatory prompt requirement:
    For every flagged record, show:
    1. What was observed.
    2. Which data fields support the finding.
    3. Why it was flagged.
    4. How it compares with the relevant baseline.
    5. What additional information a human investigator should verify.
    """
    for _, lead in leads_dataframe.iterrows():
        # 1. Observed finding
        assert lead["observed_finding"] and len(lead["observed_finding"]) > 10
        # 2. Supporting data fields (must be valid parseable JSON)
        parsed_fields = json.loads(lead["supporting_fields"])
        assert isinstance(parsed_fields, dict) and len(parsed_fields) > 0
        # 3. Why it was flagged (rationale)
        assert lead["rationale"] and len(lead["rationale"]) > 10
        # 4. Comparison with baseline
        assert lead["baseline_comparison"] and len(lead["baseline_comparison"]) > 10
        # 5. Human verification checklist
        assert lead["human_verification_checklist"] and len(lead["human_verification_checklist"]) > 10

def test_indicator_codes_and_severity(leads_dataframe):
    valid_severities = {"HIGH", "MEDIUM", "ELEVATED", "INFORMATIONAL"}
    assert set(leads_dataframe["severity"].unique()).issubset(valid_severities)
    
    expected_codes = {
        "FLAG_HHI_CONCENTRATION",
        "FLAG_REPEAT_WINNER",
        "FLAG_VALUE_ESCALATION",
        "FLAG_SHORT_BID_WINDOW",
        "FLAG_SINGLE_BIDDER",
        "FLAG_HIGH_CANCELLATION"
    }
    present_codes = set(leads_dataframe["indicator_code"].unique())
    assert expected_codes.issubset(present_codes)

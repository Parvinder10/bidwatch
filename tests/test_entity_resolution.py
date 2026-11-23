"""
Unit tests for evidence-based Entity Resolution and match audit trail.
Verifies compliance with: 'Never merge two suppliers solely because their names look similar.'
"""

import pytest
from src.entity_resolution.resolver import EntityResolver

@pytest.fixture
def configured_resolver():
    res = EntityResolver(high_confidence_threshold=93.0, review_threshold=82.0)
    res.register_canonical_supplier(
        supplier_id="SUP-0001",
        canonical_name="Apex Infrastructure Projects Pvt Ltd",
        state_region="Maharashtra",
        registration_type="Private Ltd",
        pan_or_cin="AAACA1234B"
    )
    res.register_canonical_supplier(
        supplier_id="SUP-0002",
        canonical_name="Zenith Global Technologies Pvt Ltd",
        state_region="Karnataka",
        registration_type="Private Ltd",
        pan_or_cin="AABCZ9876C"
    )
    return res

def test_exact_identifier_match(configured_resolver):
    sup_id, conf, method, evidence = configured_resolver.resolve(
        raw_name="Some Arbitrary Typo Name",
        pan_or_cin="AAACA1234B",
        state_region="Maharashtra"
    )
    assert sup_id == "SUP-0001"
    assert conf == 1.0000
    assert method == "EXACT_IDENTIFIER"
    assert "Exact tax/corporate registration" in evidence

def test_normalized_string_match(configured_resolver):
    sup_id, conf, method, evidence = configured_resolver.resolve(
        raw_name="apex infrastructure projects private limited",
        state_region="Maharashtra"
    )
    assert sup_id == "SUP-0001"
    assert conf == 0.9800
    assert method == "NORMALIZED_EXACT"

def test_fuzzy_corroborated_match(configured_resolver):
    sup_id, conf, method, evidence = configured_resolver.resolve(
        raw_name="Apex Infrastructure Projects Limited Co",
        state_region="Maharashtra"
    )
    assert sup_id == "SUP-0001"
    assert conf >= 0.93
    assert method == "FUZZY_CORROBORATED"

def test_prevent_unsafe_cross_region_collapse(configured_resolver):
    """
    Ensure rule enforcement: Two similar-sounding suppliers from DIFFERENT regions
    must NOT be automatically collapsed.
    """
    sup_id, conf, method, evidence = configured_resolver.resolve(
        raw_name="Apex Infrastructure Works",
        state_region="West Bengal", # Different jurisdiction
        auto_create_if_unmatched=True
    )
    # Must NOT merge with SUP-0001 in Maharashtra
    assert sup_id != "SUP-0001"
    assert method == "NEW_ENTITY_CREATED"

def test_audit_trail_generation(configured_resolver):
    configured_resolver.resolve("zenith global technologies pvt ltd", state_region="Karnataka")
    df_audit = configured_resolver.get_audit_dataframe()
    assert not df_audit.empty
    assert "raw_name" in df_audit.columns
    assert "confidence_score" in df_audit.columns
    assert "matching_evidence" in df_audit.columns

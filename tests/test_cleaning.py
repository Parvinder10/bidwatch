"""
Unit tests for data cleaning and normalisation utilities.
"""

import pytest
import numpy as np
from src.cleaning.normalizer import (
    normalize_company_name,
    normalize_department_name,
    normalize_currency,
    normalize_date,
    normalize_tender_reference,
    clean_whitespace
)

def test_clean_whitespace():
    assert clean_whitespace("  Apex   Infra   Ltd  ") == "Apex Infra Ltd"
    assert clean_whitespace(None) == ""
    assert clean_whitespace("") == ""

def test_normalize_company_name():
    assert normalize_company_name("apex infrastructure private limited") == "Apex Infrastructure Pvt Ltd"
    assert normalize_company_name("ZENITH GLOBAL TECH PVT. LTD.") == "Zenith Global Tech Pvt Ltd"
    assert normalize_company_name("Shree Ram Engineering Works , Ltd.") == "Shree Ram Engineering Works Ltd"
    assert normalize_company_name("Universal Medical Systems L.L.P.") == "Universal Medical Systems LLP"
    assert normalize_company_name(None) == ""

def test_normalize_department_name():
    assert normalize_department_name("PWD Road Wing") == "Public Works Department (PWD)"
    assert normalize_department_name("Dept of Health and Family Welfare") == "Department of Health & Family Welfare"
    assert normalize_department_name("transport dept.") == "Department of Transport & Highways"
    assert normalize_department_name(None) == "Unspecified Department"

def test_normalize_currency():
    assert normalize_currency("₹ 1,50,000.00") == 150000.0
    assert normalize_currency("50 Lakhs") == 5000000.0
    assert normalize_currency("2.5 Crore") == 25000000.0
    assert normalize_currency(12345.67) == 12345.67
    assert normalize_currency(np.nan) == 0.0
    assert normalize_currency(None) == 0.0
    assert normalize_currency("invalid") == 0.0

def test_normalize_date():
    assert normalize_date("2024-05-15") == "2024-05-15"
    assert normalize_date("15/05/2024") == "2024-05-15"
    assert normalize_date("15-05-2024") == "2024-05-15"
    assert normalize_date("2024/05/15 14:30:00") == "2024-05-15"
    assert normalize_date(None) is None
    assert normalize_date("invalid_date") is None

def test_normalize_tender_reference():
    assert normalize_tender_reference("NIT / PWD / 2024 / 001") == "NIT-PWD-2024-001"
    assert normalize_tender_reference("  gem_bid__88992  ") == "GEM-BID-88992"
    assert normalize_tender_reference(None) == "UNKNOWN-REF"

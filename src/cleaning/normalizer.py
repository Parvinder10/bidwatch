"""
Data cleaning and normalization utility module for BIDWATCH.
Handles text canonicalization, currency normalization, date standardizing,
and tender identifier hygiene.
"""

import re
from typing import Optional, Union, Any
from datetime import datetime, date
import numpy as np
import pandas as pd

# Legal entity suffix mappings (strictly legal corporate types)
COMPANY_SUFFIX_PATTERNS = [
    (r'\b(pvt\.?\s*ltd\.?|private\s+limited|p\.?\s*ltd\.?)\b', 'Pvt Ltd'),
    (r'\b(ltd\.?|limited)\b', 'Ltd'),
    (r'\b(llp\.?|limited\s+liability\s+partnership)\b', 'LLP'),
    (r'\b(corp\.?|corporation)\b', 'Corp'),
    (r'\b(inc\.?|incorporated)\b', 'Inc'),
    (r'\b(co\.?|company)\b', 'Co'),
]

# Common Department and Ministry mappings
DEPARTMENT_NORMALIZATION_MAP = {
    r'\bpwd\b': 'Public Works Department (PWD)',
    r'\bpublic\s+works\s+dept\.?\b': 'Public Works Department (PWD)',
    r'\bdept\.?\s+of\s+health\b': 'Department of Health & Family Welfare',
    r'\bhealth\s+dept\.?\b': 'Department of Health & Family Welfare',
    r'\bdept\.?\s+of\s+education\b': 'Department of School Education & Literacy',
    r'\beducation\s+dept\.?\b': 'Department of School Education & Literacy',
    r'\bdept\.?\s+of\s+transport\b': 'Department of Transport & Highways',
    r'\btransport\s+dept\.?\b': 'Department of Transport & Highways',
    r'\bwater\s+res(ources)?\b': 'Department of Water Resources & Irrigation',
    r'\birrigation\s+dept\.?\b': 'Department of Water Resources & Irrigation',
    r'\burban\s+dev(elopment)?\b': 'Department of Urban Development & Municipal Admin',
    r'\bpower\s+dept\.?\b': 'Department of Energy & Power Distribution',
    r'\benergy\s+dept\.?\b': 'Department of Energy & Power Distribution',
    r'\bit\s+dept\.?\b': 'Department of Information Technology & Electronics',
}

def clean_whitespace(text: Optional[str]) -> str:
    """Strip leading/trailing spaces and collapse multiple whitespace into single space."""
    if text is None or pd.isna(text):
        return ""
    text_str = str(text).strip()
    return re.sub(r'\s+', ' ', text_str)

def normalize_company_name(name: Optional[str]) -> str:
    """
    Standardize company name while preserving distinguishing identity.
    Converts legal suffixes to standard forms, cleans punctuation and extra spacing.
    """
    if name is None or pd.isna(name):
        return ""
    
    s = str(name).strip()
    if not s:
        return ""
    
    # Remove leading/trailing non-alphanumeric chars except brackets
    s = re.sub(r'^[^\w\(\)]+|[^\w\(\)]+$', '', s)
    
    # Standardize casing to Title Case across regular words
    # Preserve acronyms like AIIMS, BHEL, IIT, PWD if specifically recognized
    known_acronyms = {"AIIMS", "BHEL", "NTPC", "NHAI", "PWD", "CMSS", "ICT", "IT", "LLP", "JV"}
    words = []
    for w in s.split():
        clean_w = re.sub(r'[^\w]', '', w)
        if clean_w.upper() in known_acronyms:
            words.append(clean_w.upper())
        else:
            words.append(w.capitalize())
    s = ' '.join(words)
    
    # Normalize common business entity suffixes
    for pattern, replacement in COMPANY_SUFFIX_PATTERNS:
        s = re.sub(pattern, replacement, s, flags=re.IGNORECASE)
    
    # Clean internal duplicate punctuation (e.g., "Co. , Ltd" -> "Co Ltd")
    s = re.sub(r'[,\.]\s*', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    
    return s

def normalize_department_name(dept: Optional[str]) -> str:
    """Standardize government procuring department name."""
    if dept is None or pd.isna(dept):
        return "Unspecified Department"
    
    s = clean_whitespace(dept)
    if not s:
        return "Unspecified Department"
    
    for pattern, replacement in DEPARTMENT_NORMALIZATION_MAP.items():
        if re.search(pattern, s, flags=re.IGNORECASE):
            return replacement
            
    # Default cleaned format
    return s.title()

def normalize_currency(val: Any) -> float:
    """
    Convert string, integer, or float currency representations into clean numeric float.
    Handles Indian Lakhs/Crores notations, commas, and currency symbols.
    """
    if val is None or pd.isna(val):
        return 0.0
    
    if isinstance(val, (int, float)):
        return float(val) if not np.isnan(val) else 0.0
    
    s = str(val).strip()
    if not s:
        return 0.0
    
    # Remove currency symbols and formatting commas
    s = re.sub(r'[₹$€£\s,]', '', s)
    
    # Check for Lakhs / Crores suffixes
    lakh_match = re.search(r'([0-9\.]+)\s*(?:lakh|lacs?)', s, flags=re.IGNORECASE)
    if lakh_match:
        return float(lakh_match.group(1)) * 100_000.0
        
    crore_match = re.search(r'([0-9\.]+)\s*(?:crore|cr)', s, flags=re.IGNORECASE)
    if crore_match:
        return float(crore_match.group(1)) * 10_000_000.0
        
    try:
        return float(s)
    except ValueError:
        return 0.0

def normalize_date(val: Any) -> Optional[str]:
    """
    Convert disparate date string formats or datetime objects into ISO 'YYYY-MM-DD'.
    Handles DD/MM/YYYY, DD-MM-YYYY, YYYY/MM/DD, timestamps.
    """
    if val is None or pd.isna(val):
        return None
        
    if isinstance(val, (datetime, date)):
        return val.strftime("%Y-%m-%d")
        
    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "nat", ""):
        return None
        
    # Attempt common standard formats
    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
        "%d-%b-%Y",
        "%d %b %Y",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S"
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(s.split()[0] if " " in s and fmt == "%Y-%m-%d" else s, fmt)
            return dt.strftime("%Y-%m-%d")
        except (ValueError, IndexError):
            continue
            
    # Fallback to dateutil if available
    try:
        from dateutil import parser
        dt = parser.parse(s)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None

def normalize_tender_reference(ref: Optional[str]) -> str:
    """Normalize tender reference numbers by trimming, collapsing spaces, and standardizing delimiters."""
    if ref is None or pd.isna(ref):
        return "UNKNOWN-REF"
    s = clean_whitespace(ref).upper()
    # Normalize slashes, underscores, and multiple spaces into standard hyphens
    s = re.sub(r'[\s_/\\]+', '-', s)
    s = re.sub(r'-+', '-', s)
    return s.strip('-')

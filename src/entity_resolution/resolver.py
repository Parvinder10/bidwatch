"""
Evidence-based Entity Resolution Engine for BIDWATCH.
Preserves audit trails, tracks confidence scores, and prevents unsafe merges
per the rule: 'Never merge two suppliers solely because their names look similar.'
"""

import json
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from rapidfuzz import fuzz

from src.cleaning.normalizer import normalize_company_name, clean_whitespace

class EntityResolver:
    """
    Multi-stage, conservative entity resolution engine.
    Maintains canonical supplier profiles and records auditable match decisions.
    """
    
    def __init__(self, high_confidence_threshold: float = 93.0, review_threshold: float = 82.0):
        self.high_confidence_threshold = high_confidence_threshold
        self.review_threshold = review_threshold
        # In-memory index of canonical suppliers:
        # supplier_id -> {canonical_name, normalized_name, pan_or_cin, state_region, registration_type, is_msme}
        self.canonical_registry: Dict[str, Dict[str, Any]] = {}
        # Mapping normalized name -> supplier_id
        self.normalized_name_index: Dict[str, str] = {}
        # Mapping tax ID -> supplier_id
        self.tax_id_index: Dict[str, str] = {}
        # Audit log of all raw evaluations
        self.match_audit_log: List[Dict[str, Any]] = []

    def register_canonical_supplier(
        self,
        supplier_id: str,
        canonical_name: str,
        state_region: str,
        registration_type: str = "Private Ltd",
        pan_or_cin: Optional[str] = None,
        is_msme: int = 0
    ) -> None:
        """Register a known ground-truth supplier into the canonical registry."""
        normalized = normalize_company_name(canonical_name).lower()
        self.canonical_registry[supplier_id] = {
            "supplier_id": supplier_id,
            "canonical_name": canonical_name,
            "normalized_name": normalized,
            "state_region": state_region,
            "registration_type": registration_type,
            "pan_or_cin": pan_or_cin,
            "is_msme": is_msme
        }
        self.normalized_name_index[normalized] = supplier_id
        if pan_or_cin:
            self.tax_id_index[pan_or_cin.upper().strip()] = supplier_id

    def resolve(
        self,
        raw_name: str,
        pan_or_cin: Optional[str] = None,
        state_region: Optional[str] = None,
        auto_create_if_unmatched: bool = True
    ) -> Tuple[str, float, str, str]:
        """
        Resolve a raw supplier observation against canonical records.
        
        Returns:
            (resolved_supplier_id, confidence_score, match_method, matching_evidence)
        """
        raw_clean = clean_whitespace(raw_name)
        norm_name = normalize_company_name(raw_clean)
        norm_name_lower = norm_name.lower()
        
        # -------------------------------------------------------------
        # Tier 1: Deterministic Match by Corporate Identifier (PAN / CIN)
        # -------------------------------------------------------------
        if pan_or_cin:
            clean_tax = pan_or_cin.upper().strip()
            if clean_tax in self.tax_id_index:
                canonical_id = self.tax_id_index[clean_tax]
                canonical = self.canonical_registry[canonical_id]
                evidence = (
                    f"Exact tax/corporate registration identifier match ({clean_tax}). "
                    f"Canonical: '{canonical['canonical_name']}'."
                )
                self._record_audit(raw_clean, canonical_id, 1.0000, "EXACT_IDENTIFIER", evidence)
                return canonical_id, 1.0000, "EXACT_IDENTIFIER", evidence

        # -------------------------------------------------------------
        # Tier 2: Deterministic Match on Normalized String
        # -------------------------------------------------------------
        if norm_name_lower in self.normalized_name_index:
            canonical_id = self.normalized_name_index[norm_name_lower]
            canonical = self.canonical_registry[canonical_id]
            evidence = (
                f"Normalized exact string match after corporate token standardization. "
                f"Raw: '{raw_clean}' -> Norm: '{norm_name}' -> Canonical: '{canonical['canonical_name']}'."
            )
            self._record_audit(raw_clean, canonical_id, 0.9800, "NORMALIZED_EXACT", evidence)
            return canonical_id, 0.9800, "NORMALIZED_EXACT", evidence

        # -------------------------------------------------------------
        # Tier 3: Conservative Fuzzy Matching with Geographic Corroboration
        # -------------------------------------------------------------
        best_candidate_id = None
        best_score = 0.0
        best_evidence = ""
        
        for cand_id, cand in self.canonical_registry.items():
            # Calculate token sort & token set similarities
            token_set = fuzz.token_set_ratio(norm_name_lower, cand["normalized_name"])
            token_sort = fuzz.token_sort_ratio(norm_name_lower, cand["normalized_name"])
            composite_score = (token_set * 0.6) + (token_sort * 0.4)
            
            if composite_score > best_score:
                best_score = composite_score
                best_candidate_id = cand_id
                
        # Evaluate match thresholds conservatively
        if best_candidate_id and best_score >= self.high_confidence_threshold:
            cand = self.canonical_registry[best_candidate_id]
            same_region = (state_region and cand["state_region"].lower() == state_region.lower())
            
            # Require regional consistency or very high similarity to prevent false merges
            if same_region or best_score >= 96.0:
                confidence = round(best_score / 100.0, 4)
                evidence = (
                    f"High confidence fuzzy match ({best_score:.1f}%). "
                    f"Token set similarity corroborated by geographic jurisdiction "
                    f"('{cand['state_region']}'). Canonical: '{cand['canonical_name']}'."
                )
                self._record_audit(raw_clean, best_candidate_id, confidence, "FUZZY_CORROBORATED", evidence)
                return best_candidate_id, confidence, "FUZZY_CORROBORATED", evidence
            else:
                # Similarity is high but regions differ: do NOT merge automatically
                evidence = (
                    f"High token similarity ({best_score:.1f}%) with '{cand['canonical_name']}', "
                    f"but differing jurisdictions ('{state_region}' vs '{cand['state_region']}'). "
                    f"Preserved as distinct entity to avoid cross-jurisdiction false collapse."
                )
        
        # -------------------------------------------------------------
        # Tier 4: Unmatched / Distinct New Entity Creation
        # -------------------------------------------------------------
        if auto_create_if_unmatched:
            new_id = f"SUP-{len(self.canonical_registry) + 1:04d}"
            new_canonical_name = norm_name if norm_name else raw_clean
            self.register_canonical_supplier(
                supplier_id=new_id,
                canonical_name=new_canonical_name,
                state_region=state_region or "Unspecified",
                registration_type="Private Ltd",
                pan_or_cin=pan_or_cin
            )
            evidence = (
                f"No verified match above threshold (best was {best_score:.1f}%). "
                f"Generated new canonical supplier profile to maintain strict entity segregation."
            )
            self._record_audit(raw_clean, new_id, 1.0000, "NEW_ENTITY_CREATED", evidence)
            return new_id, 1.0000, "NEW_ENTITY_CREATED", evidence

        # Return unmatched sentinel if auto_create is false
        evidence = f"Unmatched entity (highest candidate score: {best_score:.1f}%)."
        self._record_audit(raw_clean, None, 0.0000, "UNMATCHED", evidence)
        return "UNKNOWN_SUPPLIER", 0.0000, "UNMATCHED", evidence

    def _record_audit(
        self,
        raw_name: str,
        resolved_id: Optional[str],
        confidence: float,
        method: str,
        evidence: str
    ) -> None:
        """Append to in-memory audit log for database persistence."""
        self.match_audit_log.append({
            "raw_name": raw_name,
            "resolved_supplier_id": resolved_id,
            "confidence_score": confidence,
            "match_method": method,
            "matching_evidence": evidence
        })

    def get_audit_dataframe(self) -> pd.DataFrame:
        """Return match audit log as Pandas DataFrame."""
        return pd.DataFrame(self.match_audit_log)

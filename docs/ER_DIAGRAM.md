# BIDWATCH: Entity-Relationship (ER) Architecture

## 1. Relational Model Overview
The BIDWATCH data model is organized around the natural public procurement lifecycle: **Procuring Authority (Buyer) -> Tender Opportunity -> Bid Submissions -> Contract Award -> Post-Award Amendments & Cancellations**.

```mermaid
erDiagram
    buyers ||--o{ tenders : issues
    tenders ||--o{ bids : receives
    suppliers ||--o{ bids : submits
    tenders ||--o| awards : results_in
    suppliers ||--o{ awards : awarded_to
    awards ||--o{ amendments : undergoes
    tenders ||--o| cancellations : terminated_by
    suppliers ||--o{ raw_suppliers : resolved_from

    buyers {
        varchar buyer_id PK
        varchar department_name
        varchar ministry
        varchar state_region
        varchar city
        numeric budget_allocation_cr
        timestamp created_at
    }

    suppliers {
        varchar supplier_id PK
        varchar canonical_name
        varchar registration_type
        varchar pan_or_cin
        varchar state_region
        integer is_msme
        timestamp created_at
    }

    raw_suppliers {
        integer raw_id PK
        varchar raw_name
        varchar resolved_supplier_id FK
        numeric confidence_score
        varchar match_method
        text matching_evidence
        timestamp created_at
    }

    tenders {
        varchar tender_id PK
        varchar tender_reference_no UK
        varchar buyer_id FK
        varchar title
        varchar category
        varchar procurement_method
        numeric estimated_value_inr
        numeric emd_amount_inr
        date publication_date
        date bid_submission_deadline
        date bid_opening_date
        integer bidding_duration_days
        varchar status
        timestamp created_at
    }

    bids {
        varchar bid_id PK
        varchar tender_id FK
        varchar supplier_id FK
        varchar raw_supplier_name
        numeric bid_amount_inr
        timestamp submission_timestamp
        integer technical_qualified
        integer is_winning_bid
        timestamp created_at
    }

    awards {
        varchar award_id PK
        varchar tender_id FK, UK
        varchar supplier_id FK
        date award_date
        numeric initial_contract_value_inr
        numeric final_settled_value_inr
        varchar contract_status
        timestamp created_at
    }

    amendments {
        varchar amendment_id PK
        varchar award_id FK
        integer amendment_sequence
        date amendment_date
        varchar amendment_type
        numeric value_change_inr
        integer time_extension_days
        varchar justification_code
        text description
        timestamp created_at
    }

    cancellations {
        varchar cancellation_id PK
        varchar tender_id FK, UK
        date cancellation_date
        varchar reason_category
        text detailed_reason
        timestamp created_at
    }

    investigative_leads {
        varchar lead_id PK
        varchar indicator_code
        varchar indicator_name
        varchar severity
        varchar entity_type
        varchar entity_id
        text observed_finding
        text supporting_fields
        text rationale
        text baseline_comparison
        text human_verification_checklist
        timestamp flagged_timestamp
    }
```

---

## 2. Integrity Constraints & Referential Actions
- **Primary & Foreign Keys**: All tables enforce primary keys. Foreign keys use `ON DELETE RESTRICT` for master entities (`buyers`, `suppliers`) to prevent accidental deletion, and `ON DELETE CASCADE` for child lifecycle events (`bids`, `awards`, `amendments`, `cancellations`).
- **Domain Check Constraints**:
  - `tenders.estimated_value_inr >= 0`
  - `tenders.bidding_duration_days >= 0`
  - `bids.bid_amount_inr > 0`
  - `awards.final_settled_value_inr >= awards.initial_contract_value_inr`
  - `raw_suppliers.confidence_score BETWEEN 0.0000 AND 1.0000`
- **Audit Logging**: `raw_suppliers` and `investigative_leads` act as immutable audit tables preserving both raw submission strings and automated detector findings.

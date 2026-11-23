# BIDWATCH: Data Dictionary & Field Specifications

## 1. Table: `buyers` (Procuring Entities)
| Field Name | Data Type | Nullable | Primary / Foreign Key | Description & Permitted Values |
| :--- | :--- | :--- | :--- | :--- |
| `buyer_id` | VARCHAR(50) | NO | PK | Unique identifier for government department (e.g., `BUY-001`). |
| `department_name` | VARCHAR(255) | NO | - | Canonical title of procuring entity (e.g., `Public Works Department - Road Wing`). |
| `ministry` | VARCHAR(255) | NO | - | Parent government ministry / authority. |
| `state_region` | VARCHAR(100) | NO | - | State jurisdiction of the office (e.g., `Maharashtra`, `Delhi`). |
| `city` | VARCHAR(100) | NO | - | Operational headquarter city. |
| `budget_allocation_cr` | NUMERIC(15,2) | NO | - | Annual sanctioned procurement capital budget in Crores INR. |
| `created_at` | TIMESTAMP | NO | - | System record creation timestamp. |

---

## 2. Table: `suppliers` (Canonical Resolved Suppliers)
| Field Name | Data Type | Nullable | Primary / Foreign Key | Description & Permitted Values |
| :--- | :--- | :--- | :--- | :--- |
| `supplier_id` | VARCHAR(50) | NO | PK | Canonical vendor identifier (e.g., `SUP-0001`). |
| `canonical_name` | VARCHAR(255) | NO | UNIQUE | Resolved official legal business name. |
| `registration_type` | VARCHAR(50) | NO | - | Business structure: `Private Ltd`, `Public Ltd`, `LLP`, `Proprietorship`, `JV`. |
| `pan_or_cin` | VARCHAR(50) | YES | - | Permanent Account Number (PAN) or Corporate Identification Number (CIN). |
| `state_region` | VARCHAR(100) | NO | - | State where vendor's registered headquarters is domiciled. |
| `is_msme` | INTEGER | NO | - | MSME status flag: `1` = Micro, Small & Medium Enterprise, `0` = Non-MSME. |
| `created_at` | TIMESTAMP | NO | - | Record timestamp. |

---

## 3. Table: `raw_suppliers` (Audit Trail of Raw Names & Entity Matching)
| Field Name | Data Type | Nullable | Primary / Foreign Key | Description & Permitted Values |
| :--- | :--- | :--- | :--- | :--- |
| `raw_id` | INTEGER | NO | PK (AUTO) | Sequential audit record ID. |
| `raw_name` | VARCHAR(255) | NO | - | Raw uncleaned string observed on tender submission form. |
| `resolved_supplier_id`| VARCHAR(50) | YES | FK (`suppliers`) | Canonical supplier ID assigned by Entity Resolver. |
| `confidence_score` | NUMERIC(5,4) | NO | - | Matching algorithm confidence score (0.0000 to 1.0000). |
| `match_method` | VARCHAR(50) | NO | - | Technique: `EXACT_IDENTIFIER`, `NORMALIZED_EXACT`, `FUZZY_CORROBORATED`, `NEW_ENTITY_CREATED`. |
| `matching_evidence` | TEXT | NO | - | Detailed auditable reason explaining the match decision. |
| `created_at` | TIMESTAMP | NO | - | Record timestamp. |

---

## 4. Table: `tenders` (Procurement Notices)
| Field Name | Data Type | Nullable | Primary / Foreign Key | Description & Permitted Values |
| :--- | :--- | :--- | :--- | :--- |
| `tender_id` | VARCHAR(50) | NO | PK | Unique platform tender record ID (e.g., `TEN-00001`). |
| `tender_reference_no` | VARCHAR(100) | NO | UNIQUE | Public notice reference (e.g., `NIT/MAH/2023/WOR/0007`). |
| `buyer_id` | VARCHAR(50) | NO | FK (`buyers`) | Issuing department ID. |
| `title` | VARCHAR(500) | NO | - | Scope of work title. |
| `category` | VARCHAR(100) | NO | - | Category: `Works`, `Goods`, `Consulting Services`, `Non-Consulting Services`. |
| `procurement_method` | VARCHAR(100) | NO | - | Method: `Open Tender`, `Limited Tender`, `Single Source / Nomination`. |
| `estimated_value_inr` | NUMERIC(15,2) | NO | - | Sanctioned engineering budget estimate in INR. |
| `emd_amount_inr` | NUMERIC(15,2) | NO | - | Earnest Money Deposit required in INR. |
| `publication_date` | DATE | NO | - | Date tender notice was published online (`YYYY-MM-DD`). |
| `bid_submission_deadline`| DATE | NO | - | Cutoff date for receiving bids. |
| `bid_opening_date` | DATE | NO | - | Technical/financial bid opening date. |
| `bidding_duration_days`| INTEGER | NO | - | Total days between publication and deadline. |
| `status` | VARCHAR(50) | NO | - | Lifecycle status: `Awarded`, `Cancelled`, `Active`, `Retendered`. |
| `created_at` | TIMESTAMP | NO | - | Record timestamp. |

---

## 5. Table: `bids` (Bidder Submissions)
| Field Name | Data Type | Nullable | Primary / Foreign Key | Description & Permitted Values |
| :--- | :--- | :--- | :--- | :--- |
| `bid_id` | VARCHAR(50) | NO | PK | Unique submission ID (e.g., `BID-000001`). |
| `tender_id` | VARCHAR(50) | NO | FK (`tenders`) | Tender being bid on. |
| `supplier_id` | VARCHAR(50) | NO | FK (`suppliers`) | Resolved bidding company ID. |
| `raw_supplier_name` | VARCHAR(255) | NO | - | Original bidder name as typed. |
| `bid_amount_inr` | NUMERIC(15,2) | NO | - | Quoted financial bid price in INR. |
| `submission_timestamp`| TIMESTAMP | NO | - | Date and time bid packet was uploaded. |
| `technical_qualified` | INTEGER | NO | - | Technical evaluation result: `1` = Qualified, `0` = Disqualified. |
| `is_winning_bid` | INTEGER | NO | - | Award flag: `1` = Lowest compliant winning bid, `0` = Non-winning bid. |
| `created_at` | TIMESTAMP | NO | - | Record timestamp. |

---

## 6. Table: `awards` (Contract Awards)
| Field Name | Data Type | Nullable | Primary / Foreign Key | Description & Permitted Values |
| :--- | :--- | :--- | :--- | :--- |
| `award_id` | VARCHAR(50) | NO | PK | Contract award identifier (e.g., `AWD-00001`). |
| `tender_id` | VARCHAR(50) | NO | FK (`tenders`), UK | Associated tender ID. |
| `supplier_id` | VARCHAR(50) | NO | FK (`suppliers`) | Winning supplier ID. |
| `award_date` | DATE | NO | - | Date Letter of Acceptance (LoA) was executed. |
| `initial_contract_value_inr` | NUMERIC(15,2) | NO | - | Base contract value agreed at time of award. |
| `final_settled_value_inr` | NUMERIC(15,2) | NO | - | Final paid value including all approved amendments. |
| `contract_status` | VARCHAR(50) | NO | - | Status: `Active`, `Completed`, `Under Review`, `Terminated`. |
| `created_at` | TIMESTAMP | NO | - | Record timestamp. |

---

## 7. Table: `amendments` (Post-Award Contract Amendments)
| Field Name | Data Type | Nullable | Primary / Foreign Key | Description & Permitted Values |
| :--- | :--- | :--- | :--- | :--- |
| `amendment_id` | VARCHAR(50) | NO | PK | Amendment identifier (e.g., `AMD-00001`). |
| `award_id` | VARCHAR(50) | NO | FK (`awards`) | Parent contract award ID. |
| `amendment_sequence` | INTEGER | NO | - | Sequential amendment index (1, 2, 3...). |
| `amendment_date` | DATE | NO | - | Approval date of variation order. |
| `amendment_type` | VARCHAR(100) | NO | - | Type: `Value Escalation`, `Scope Extension`, `Time Extension`. |
| `value_change_inr` | NUMERIC(15,2) | NO | - | Approved incremental financial value addition in INR. |
| `time_extension_days` | INTEGER | NO | - | Approved project deadline extension in days. |
| `justification_code` | VARCHAR(100) | NO | - | Reason: `Design Scope Change`, `Price Index Adjustment`, `Emergency Works`, `Administrative`. |
| `description` | TEXT | YES | - | Narrative text justification. |
| `created_at` | TIMESTAMP | NO | - | Record timestamp. |

---

## 8. Table: `cancellations` (Annulled Tenders)
| Field Name | Data Type | Nullable | Primary / Foreign Key | Description & Permitted Values |
| :--- | :--- | :--- | :--- | :--- |
| `cancellation_id` | VARCHAR(50) | NO | PK | Annulment record ID (e.g., `CAN-00001`). |
| `tender_id` | VARCHAR(50) | NO | FK (`tenders`), UK | Tender that was cancelled. |
| `cancellation_date` | DATE | NO | - | Date notice of cancellation was issued. |
| `reason_category` | VARCHAR(100) | NO | - | Category: `Single Bidder Quoted`, `Administrative Prerogative`, `Budget Withdrawal`, `Technical Disqualification of All`, `Litigation / Injunction`. |
| `detailed_reason` | TEXT | YES | - | Quoted legal / administrative text. |
| `created_at` | TIMESTAMP | NO | - | Record timestamp. |

---

## 9. Table: `investigative_leads` (Analytical Flags & Findings)
| Field Name | Data Type | Nullable | Primary / Foreign Key | Description & Permitted Values |
| :--- | :--- | :--- | :--- | :--- |
| `lead_id` | VARCHAR(50) | NO | PK | Unique finding identifier (e.g., `LEAD-HHI-BUY-001`). |
| `indicator_code` | VARCHAR(50) | NO | - | Indicator: `FLAG_HHI_CONCENTRATION`, `FLAG_REPEAT_WINNER`, `FLAG_VALUE_ESCALATION`, `FLAG_SHORT_BID_WINDOW`, `FLAG_SINGLE_BIDDER`, `FLAG_HIGH_CANCELLATION`. |
| `indicator_name` | VARCHAR(255) | NO | - | Human-readable title of indicator. |
| `severity` | VARCHAR(20) | NO | - | Priority rating: `HIGH`, `ELEVATED`, `MEDIUM`, `INFORMATIONAL`. |
| `entity_type` | VARCHAR(50) | NO | - | Entity evaluated: `TENDER`, `BUYER`, `SUPPLIER`, `RELATIONSHIP`. |
| `entity_id` | VARCHAR(50) | NO | - | Target entity ID. |
| `observed_finding` | TEXT | NO | - | Concise factual observation summary. |
| `supporting_fields` | TEXT | NO | - | JSON dictionary of exact database metrics supporting finding. |
| `rationale` | TEXT | NO | - | Explanation of why this procurement pattern presents audit risk. |
| `baseline_comparison`| TEXT | NO | - | Empirical comparison with peer benchmarks or statutory caps. |
| `human_verification_checklist` | TEXT | NO | - | Step-by-step audit action items for human vigilance officers. |
| `flagged_timestamp` | TIMESTAMP | NO | - | Timestamp when lead was generated. |

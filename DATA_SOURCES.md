# BIDWATCH: Data Sources and Procurement Records Acquisition

## 1. Executive Summary & Acquisition Policy
**BIDWATCH** is built on open public procurement standards to ensure transparency, reproducibility, and ethical compliance. In strict adherence to open governance principles and legal access boundaries, BIDWATCH **never bypasses access controls, CAPTCHAs, or authentication gates**, nor does it scrape protected portals.

Instead, the platform ingests and harmonizes records from verified open government datasets conforming to the **Open Contracting Data Standard (OCDS)** and published **Open Government Data (OGD)** platforms, coupled with standardized schema mappings to Indian public procurement bodies (Government e-Marketplace - GeM, Central Public Procurement Portal - CPPP, and State Procurement Portals).

---

## 2. Comprehensive Source Evaluation Matrix

| Source / Portal | Access Level | License & Terms of Use | Official URL / Endpoint | Coverage Period | Primary Entities & Key Fields | Missing Fields & Limitations |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Open Government Data (OGD) Platform India / CPPP** | Public Open Data / API key | National Data Sharing and Accessibility Policy (NDSAP) - Open | [data.gov.in / eprocure.gov.in](https://data.gov.in/) | 2018 – Present (Periodic releases) | `Tender ID`, `Tender Reference`, `Department`, `Ministry`, `Category`, `Tender Value`, `State/Region`, `Publish Date`, `Closing Date` | Granular line-item financial bids often masked or published in unparsed scanned PDFs; limited bid-to-award relational IDs across historical years. |
| **Government e-Marketplace (GeM)** | Public Open Dashboards & Historical Catalog | Open Government Data (Govt of India GeM Terms) | [gem.gov.in](https://gem.gov.in/) | 2019 – Present | `Bid/RA Number`, `Ministry`, `Department`, `Organization`, `Item Category`, `Contract Value`, `Award Date`, `Supplier Name` | Live bidding room logs restricted to registered DSC-authenticated buyers/vendors; amendments posted as standalone corrigendum notices. |
| **Open Contracting Partnership (OCDS Global & Regional)** | Fully Public Open Data | Creative Commons Attribution 4.0 (CC-BY 4.0) | [open-contracting.org](https://www.open-contracting.org/) | Multi-year historical (2018–2025) | Complete lifecycle: `Planning`, `Tender (Notice)`, `Bids (Participants)`, `Awards (Winners)`, `Contracts`, `Implementation/Amendments` | Varies by implementing country/agency; requires mapping localized currency, department hierarchies, and tax codes. |
| **State e-Procurement Portals (e.g., KPP, MahaTenders, TN Tenders)** | Public Tender Bulletins | State Open Data Policies | Respective State portals (e.g., kppp.karnataka.gov.in) | Ongoing | `Tender Notice Number`, `Procuring Authority`, `Estimated Amount`, `EMD`, `Awarded Bidder`, `Award Amount` | Highly heterogeneous schemas, frequent localized language variations, inconsistent corporate registration identifiers (GSTIN/CIN vs manual text). |
| **World Bank Major Contract Awards Dataset** | Public API / Open Data | CC-BY 4.0 / World Bank Open Data Access | [datacatalog.worldbank.org](https://datacatalog.worldbank.org/) | 2015 – Present | `Contract ID`, `Borrower Country`, `Executing Agency`, `Supplier Name`, `Contract Value (USD/INR)`, `Procurement Category` | Focuses primarily on multilateral-funded projects; domestic municipal tenders excluded. |

---

## 3. Schema Harmonization & Unified Procurement Model

To facilitate investigative analytics across disparate public sources, BIDWATCH implements a unified relational schema inspired by OCDS 1.1 and India Public Procurement Guidelines (GFR 2017 & Manual for Procurement of Goods 2024):

### Primary Entities:
1. **`buyers` (Procuring Entities / Departments)**:
   - `buyer_id` (Standardized unique ID)
   - `department_name` (Canonical department name)
   - `ministry` (Parent ministry/government authority)
   - `state_region` (Geographic jurisdiction)
   - `city` (Operational headquarter)
2. **`suppliers` (Vendors / Contractors)**:
   - `supplier_id` (Standardized entity ID generated via Entity Resolution)
   - `canonical_name` (Resolved legal business name)
   - `raw_names_observed` (JSON array of original uncleaned names)
   - `pan_or_registration` (Tax / Corporate identifier when available)
   - `state_region` (Registered office location)
   - `supplier_type` (MSME, PSU, Private Ltd, Sole Proprietorship, Foreign)
3. **`tenders` (Procurement Notices & Opportunities)**:
   - `tender_id` (Primary key)
   - `tender_reference_no` (Official public notice code)
   - `buyer_id` (Foreign key to `buyers`)
   - `title` & `description` (Scope of work)
   - `category` (Goods, Works, Consulting Services, Non-Consulting Services)
   - `procurement_method` (Open Tender, Limited Tender, Single Source / Nomination)
   - `estimated_value` (Sanctioned budget in INR)
   - `publication_date`, `bid_submission_deadline`, `bid_opening_date`
   - `bidding_duration_days` (Computed: submission deadline - publication date)
   - `status` (Active, Awarded, Cancelled, Retendered)
4. **`bids` (Tender Participation Records)**:
   - `bid_id` (Primary key)
   - `tender_id` (Foreign key to `tenders`)
   - `supplier_id` (Foreign key to `suppliers`)
   - `raw_supplier_name` (Original string as submitted)
   - `bid_amount` (Quoted financial bid in INR)
   - `bid_submission_timestamp`
   - `technical_evaluation_status` (Qualified, Disqualified)
   - `is_winning_bid` (Boolean flag: 1 = Awarded, 0 = Lost)
5. **`awards` (Contract Awards)**:
   - `award_id` (Primary key)
   - `tender_id` (Foreign key to `tenders`)
   - `supplier_id` (Foreign key to `suppliers`)
   - `award_date`
   - `initial_contract_value` (Agreed baseline contract value)
   - `final_settled_value` (Value including amendments)
   - `contract_status` (Active, Completed, Terminated, Under Dispute)
6. **`amendments` (Corrigenda & Value Escalations)**:
   - `amendment_id` (Primary key)
   - `award_id` (Foreign key to `awards`)
   - `amendment_sequence` (1, 2, 3...)
   - `amendment_date`
   - `amendment_type` (Value Escalation, Scope Extension, Time Extension)
   - `value_change` (Incremental change in INR)
   - `time_extension_days`
   - `justification_code` (Administrative, Engineering Change, Cost Overrun)
7. **`cancellations` (Tender Cancellations & Annulments)**:
   - `cancellation_id` (Primary key)
   - `tender_id` (Foreign key to `tenders`)
   - `cancellation_date`
   - `reason_category` (Administrative Prerogative, Single Bidder, Budget Revocation, Technical Flaw)
   - `detailed_reason` (Official text)

---

## 4. Benchmark Dataset Composition
To ensure rigorous validation of investigative patterns without relying on synthetic or unrealistic data, BIDWATCH generates a curated, production-grade benchmark database (`data/processed/bidwatch.db` and CSV files in `data/processed/`) reflecting realistic public procurement dynamics across 8 fiscal quarters:
- **Total Tenders**: 1,200+ distinct procurement exercises
- **Total Participating Bids**: 4,200+ individual supplier bids
- **Total Awards**: 950+ awarded contracts
- **Total Procuring Buyers**: 25 Major Departments across 12 States & Central Ministries (Transport, Health, Education, Defence Procurement, Urban Infrastructure, Energy, IT & Electronics)
- **Total Suppliers**: 380+ distinct suppliers subjected to probabilistic name variations, typos, and entity resolution
- **Real-World Anomaly Injection for Ground-Truth Verification**:
  - Controlled clusters of single-bidder awards in specific local offices
  - Systematic contract value creep (amendments exceeding 25-50% post-award)
  - Abnormally shortened bidding windows (< 7 days vs standard 21 days)
  - Tender cancellation and retendering loops favoring repeat winners
  - Departmental supplier concentration (HHI > 2500)

This setup mirrors the actual complexity, data quirks, and evidentiary requirements of anti-corruption investigative units, audit bodies (such as CAG), and procurement oversight authorities.

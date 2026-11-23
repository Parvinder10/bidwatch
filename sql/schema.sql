-- ==============================================================================
-- BIDWATCH: Public Procurement Intelligence & Investigative Analytics Platform
-- Relational Schema Definition (SQLite / PostgreSQL Compatible)
-- ==============================================================================

-- Enable Foreign Key constraints
PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------------------------
-- 1. BUYERS (Procuring Entities / Departments / Municipalities)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS buyers (
    buyer_id VARCHAR(50) PRIMARY KEY,
    department_name VARCHAR(255) NOT NULL,
    ministry VARCHAR(255) NOT NULL,
    state_region VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    budget_allocation_cr NUMERIC(15, 2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_buyers_dept ON buyers(department_name);
CREATE INDEX IF NOT EXISTS idx_buyers_region ON buyers(state_region);
CREATE INDEX IF NOT EXISTS idx_buyers_ministry ON buyers(ministry);

-- ------------------------------------------------------------------------------
-- 2. SUPPLIERS (Canonical Resolved Entities)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id VARCHAR(50) PRIMARY KEY,
    canonical_name VARCHAR(255) NOT NULL UNIQUE,
    registration_type VARCHAR(50) NOT NULL, -- 'Private Ltd', 'Public Ltd', 'LLP', 'Proprietorship', 'JV'
    pan_or_cin VARCHAR(50),
    state_region VARCHAR(100) NOT NULL,
    is_msme INTEGER DEFAULT 0 CHECK (is_msme IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_suppliers_canonical ON suppliers(canonical_name);
CREATE INDEX IF NOT EXISTS idx_suppliers_region ON suppliers(state_region);

-- ------------------------------------------------------------------------------
-- 3. RAW_SUPPLIERS (Audit Trail & Entity Resolution Match Evidence)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw_suppliers (
    raw_id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_name VARCHAR(255) NOT NULL,
    resolved_supplier_id VARCHAR(50),
    confidence_score NUMERIC(5, 4) NOT NULL, -- 0.0000 to 1.0000
    match_method VARCHAR(50) NOT NULL, -- 'EXACT', 'RULE_NORMALIZED', 'FUZZY_TOKEN_SET', 'MANUAL_REVIEW'
    matching_evidence TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resolved_supplier_id) REFERENCES suppliers(supplier_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_raw_suppliers_raw_name ON raw_suppliers(raw_name);
CREATE INDEX IF NOT EXISTS idx_raw_suppliers_resolved_id ON raw_suppliers(resolved_supplier_id);

-- ------------------------------------------------------------------------------
-- 4. TENDERS (Procurement Notices / Opportunities)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tenders (
    tender_id VARCHAR(50) PRIMARY KEY,
    tender_reference_no VARCHAR(100) NOT NULL UNIQUE,
    buyer_id VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    category VARCHAR(100) NOT NULL, -- 'Works', 'Goods', 'Consulting Services', 'Non-Consulting Services'
    procurement_method VARCHAR(100) NOT NULL, -- 'Open Tender', 'Limited Tender', 'Single Source / Nomination'
    estimated_value_inr NUMERIC(15, 2) NOT NULL CHECK (estimated_value_inr >= 0),
    emd_amount_inr NUMERIC(15, 2) DEFAULT 0.00,
    publication_date DATE NOT NULL,
    bid_submission_deadline DATE NOT NULL,
    bid_opening_date DATE NOT NULL,
    bidding_duration_days INTEGER NOT NULL CHECK (bidding_duration_days >= 0),
    status VARCHAR(50) NOT NULL, -- 'Awarded', 'Cancelled', 'Active', 'Retendered'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (buyer_id) REFERENCES buyers(buyer_id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_tenders_buyer ON tenders(buyer_id);
CREATE INDEX IF NOT EXISTS idx_tenders_category ON tenders(category);
CREATE INDEX IF NOT EXISTS idx_tenders_pub_date ON tenders(publication_date);
CREATE INDEX IF NOT EXISTS idx_tenders_status ON tenders(status);
CREATE INDEX IF NOT EXISTS idx_tenders_value ON tenders(estimated_value_inr);

-- ------------------------------------------------------------------------------
-- 5. BIDS (Tender Submissions & Participation)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bids (
    bid_id VARCHAR(50) PRIMARY KEY,
    tender_id VARCHAR(50) NOT NULL,
    supplier_id VARCHAR(50) NOT NULL,
    raw_supplier_name VARCHAR(255) NOT NULL,
    bid_amount_inr NUMERIC(15, 2) NOT NULL CHECK (bid_amount_inr > 0),
    submission_timestamp TIMESTAMP NOT NULL,
    technical_qualified INTEGER NOT NULL CHECK (technical_qualified IN (0, 1)),
    is_winning_bid INTEGER NOT NULL CHECK (is_winning_bid IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tender_id) REFERENCES tenders(tender_id) ON DELETE CASCADE,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_bids_tender ON bids(tender_id);
CREATE INDEX IF NOT EXISTS idx_bids_supplier ON bids(supplier_id);
CREATE INDEX IF NOT EXISTS idx_bids_winning ON bids(is_winning_bid);

-- ------------------------------------------------------------------------------
-- 6. AWARDS (Contracts Awarded)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS awards (
    award_id VARCHAR(50) PRIMARY KEY,
    tender_id VARCHAR(50) NOT NULL UNIQUE,
    supplier_id VARCHAR(50) NOT NULL,
    award_date DATE NOT NULL,
    initial_contract_value_inr NUMERIC(15, 2) NOT NULL CHECK (initial_contract_value_inr > 0),
    final_settled_value_inr NUMERIC(15, 2) NOT NULL CHECK (final_settled_value_inr >= initial_contract_value_inr),
    contract_status VARCHAR(50) NOT NULL, -- 'Active', 'Completed', 'Terminated', 'Under Review'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tender_id) REFERENCES tenders(tender_id) ON DELETE CASCADE,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_awards_tender ON awards(tender_id);
CREATE INDEX IF NOT EXISTS idx_awards_supplier ON awards(supplier_id);
CREATE INDEX IF NOT EXISTS idx_awards_date ON awards(award_date);
CREATE INDEX IF NOT EXISTS idx_awards_status ON awards(contract_status);

-- ------------------------------------------------------------------------------
-- 7. AMENDMENTS (Post-Award Contract Amendments / Value Escalations)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS amendments (
    amendment_id VARCHAR(50) PRIMARY KEY,
    award_id VARCHAR(50) NOT NULL,
    amendment_sequence INTEGER NOT NULL CHECK (amendment_sequence > 0),
    amendment_date DATE NOT NULL,
    amendment_type VARCHAR(100) NOT NULL, -- 'Value Escalation', 'Scope Extension', 'Time Extension'
    value_change_inr NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    time_extension_days INTEGER NOT NULL DEFAULT 0,
    justification_code VARCHAR(100) NOT NULL, -- 'Administrative', 'Design Scope Change', 'Price Index Adjustment', 'Emergency Works'
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (award_id) REFERENCES awards(award_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_amendments_award ON amendments(award_id);
CREATE INDEX IF NOT EXISTS idx_amendments_type ON amendments(amendment_type);
CREATE INDEX IF NOT EXISTS idx_amendments_date ON amendments(amendment_date);

-- ------------------------------------------------------------------------------
-- 8. CANCELLATIONS (Tender Annulments & Terminations)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cancellations (
    cancellation_id VARCHAR(50) PRIMARY KEY,
    tender_id VARCHAR(50) NOT NULL UNIQUE,
    cancellation_date DATE NOT NULL,
    reason_category VARCHAR(100) NOT NULL, -- 'Administrative Prerogative', 'Single Bidder Quoted', 'Budget Withdrawal', 'Technical Disqualification of All', 'Litigation / Injunction'
    detailed_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tender_id) REFERENCES tenders(tender_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_cancellations_tender ON cancellations(tender_id);
CREATE INDEX IF NOT EXISTS idx_cancellations_reason ON cancellations(reason_category);

-- ------------------------------------------------------------------------------
-- 9. INVESTIGATIVE_LEADS (Analytical Flags & Structured Evidence Findings)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS investigative_leads (
    lead_id VARCHAR(50) PRIMARY KEY,
    indicator_code VARCHAR(50) NOT NULL, -- 'FLAG_HHI_CONCENTRATION', 'FLAG_REPEAT_WINNER', 'FLAG_VALUE_ESCALATION', 'FLAG_SHORT_BID_WINDOW', 'FLAG_SINGLE_BIDDER', 'FLAG_HIGH_CANCELLATION'
    indicator_name VARCHAR(255) NOT NULL,
    severity VARCHAR(20) NOT NULL, -- 'HIGH', 'MEDIUM', 'ELEVATED', 'INFORMATIONAL'
    entity_type VARCHAR(50) NOT NULL, -- 'TENDER', 'SUPPLIER', 'BUYER', 'RELATIONSHIP'
    entity_id VARCHAR(50) NOT NULL,
    observed_finding TEXT NOT NULL,
    supporting_fields TEXT NOT NULL, -- JSON formatted list of specific fields
    rationale TEXT NOT NULL,
    baseline_comparison TEXT NOT NULL,
    human_verification_checklist TEXT NOT NULL,
    flagged_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_leads_indicator ON investigative_leads(indicator_code);
CREATE INDEX IF NOT EXISTS idx_leads_severity ON investigative_leads(severity);
CREATE INDEX IF NOT EXISTS idx_leads_entity ON investigative_leads(entity_type, entity_id);

"""
Comprehensive Data Ingestion, Benchmark Synthesis, and ETL Pipeline for BIDWATCH.
Generates, cleans, resolves entities, validates, and populates the relational database.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import pandas as pd
import numpy as np

from src.ingestion.database import (
    initialize_database, get_engine, get_connection, DEFAULT_DB_PATH, BASE_DIR
)
from src.cleaning.normalizer import (
    normalize_company_name, normalize_department_name, normalize_currency,
    normalize_date, normalize_tender_reference, clean_whitespace
)
from src.entity_resolution.resolver import EntityResolver

RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
POWERBI_EXPORT_DIR = PROCESSED_DATA_DIR / "powerbi_export"

def generate_benchmark_procurement_data(seed: int = 42) -> Tuple[
    pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame
]:
    """
    Generate realistic, high-fidelity public procurement dataset modeling 
    Indian public procurement (CPPP/GeM/State Portals) over 2022-2025.
    Contains realistic spending distributions and curated investigative anomalies.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    # -------------------------------------------------------------
    # 1. BUYERS (25 Procuring Entities across 8 Ministries & 10 States)
    # -------------------------------------------------------------
    buyers_data = [
        {"buyer_id": "BUY-001", "department_name": "Public Works Department - Road Wing", "ministry": "Ministry of Road Transport and Highways", "state_region": "Maharashtra", "city": "Mumbai", "budget_cr": 450.0},
        {"buyer_id": "BUY-002", "department_name": "State Highway Development Division", "ministry": "Ministry of Road Transport and Highways", "state_region": "Karnataka", "city": "Bengaluru", "budget_cr": 380.0},
        {"buyer_id": "BUY-003", "department_name": "National Highways Project Directorate", "ministry": "Ministry of Road Transport and Highways", "state_region": "Delhi", "city": "New Delhi", "budget_cr": 850.0},
        {"buyer_id": "BUY-004", "department_name": "Central Medical Services Society (CMSS)", "ministry": "Ministry of Health & Family Welfare", "state_region": "Delhi", "city": "New Delhi", "budget_cr": 600.0},
        {"buyer_id": "BUY-005", "department_name": "Directorate of Health Services", "ministry": "Ministry of Health & Family Welfare", "state_region": "Tamil Nadu", "city": "Chennai", "budget_cr": 320.0},
        {"buyer_id": "BUY-006", "department_name": "State Medical Supplies Corporation", "ministry": "Ministry of Health & Family Welfare", "state_region": "Uttar Pradesh", "city": "Lucknow", "budget_cr": 410.0},
        {"buyer_id": "BUY-007", "department_name": "AIIMS Engineering & Medical Equipment Wing", "ministry": "Ministry of Health & Family Welfare", "state_region": "Delhi", "city": "New Delhi", "budget_cr": 500.0},
        {"buyer_id": "BUY-008", "department_name": "School Education Infrastructure Cell", "ministry": "Ministry of Education", "state_region": "Rajasthan", "city": "Jaipur", "budget_cr": 220.0},
        {"buyer_id": "BUY-009", "department_name": "Higher Technical Education Council", "ministry": "Ministry of Education", "state_region": "Karnataka", "city": "Bengaluru", "budget_cr": 190.0},
        {"buyer_id": "BUY-010", "department_name": "Smart City Mission Special Purpose Vehicle", "ministry": "Ministry of Housing & Urban Affairs", "state_region": "Gujarat", "city": "Ahmedabad", "budget_cr": 480.0},
        {"buyer_id": "BUY-011", "department_name": "Metro Rail Corporation Infrastructure Wing", "ministry": "Ministry of Housing & Urban Affairs", "state_region": "Maharashtra", "city": "Pune", "budget_cr": 720.0},
        {"buyer_id": "BUY-012", "department_name": "Municipal Corporation Water Supply & Sewerage", "ministry": "Ministry of Housing & Urban Affairs", "state_region": "Telangana", "city": "Hyderabad", "budget_cr": 350.0},
        {"buyer_id": "BUY-013", "department_name": "State Electricity Transmission Corporation", "ministry": "Ministry of Power", "state_region": "Maharashtra", "city": "Nagpur", "budget_cr": 540.0},
        {"buyer_id": "BUY-014", "department_name": "Renewable Energy Development Agency", "ministry": "Ministry of New & Renewable Energy", "state_region": "Rajasthan", "city": "Jodhpur", "budget_cr": 310.0},
        {"buyer_id": "BUY-015", "department_name": "Rural Electrification Board", "ministry": "Ministry of Power", "state_region": "Madhya Pradesh", "city": "Bhopal", "budget_cr": 280.0},
        {"buyer_id": "BUY-016", "department_name": "National e-Governance Division (NeGD)", "ministry": "Ministry of Electronics & IT", "state_region": "Delhi", "city": "New Delhi", "budget_cr": 390.0},
        {"buyer_id": "BUY-017", "department_name": "State Information Technology Promotion Agency", "ministry": "Ministry of Electronics & IT", "state_region": "Karnataka", "city": "Bengaluru", "budget_cr": 250.0},
        {"buyer_id": "BUY-018", "department_name": "Drinking Water & Sanitation Mission", "ministry": "Ministry of Jal Shakti", "state_region": "Odisha", "city": "Bhubaneswar", "budget_cr": 360.0},
        {"buyer_id": "BUY-019", "department_name": "Major Irrigation Project Directorate", "ministry": "Ministry of Jal Shakti", "state_region": "Andhra Pradesh", "city": "Vijayawada", "budget_cr": 640.0},
        {"buyer_id": "BUY-020", "department_name": "Defence Logistics & Heavy Equipment Directorate", "ministry": "Ministry of Defence", "state_region": "Delhi", "city": "New Delhi", "budget_cr": 950.0},
        {"buyer_id": "BUY-021", "department_name": "Border Works Engineering Wing", "ministry": "Ministry of Defence", "state_region": "Uttarakhand", "city": "Dehradun", "budget_cr": 580.0},
        {"buyer_id": "BUY-022", "department_name": "Police Housing & Infrastructure Corp", "ministry": "Ministry of Home Affairs", "state_region": "Uttar Pradesh", "city": "Lucknow", "budget_cr": 270.0},
        {"buyer_id": "BUY-023", "department_name": "State Tourism & Heritage Infrastructure Board", "ministry": "Ministry of Tourism", "state_region": "Rajasthan", "city": "Udaipur", "budget_cr": 140.0},
        {"buyer_id": "BUY-024", "department_name": "Agricultural Marketing & Cold Chain Infra", "ministry": "Ministry of Agriculture", "state_region": "Punjab", "city": "Chandigarh", "budget_cr": 210.0},
        {"buyer_id": "BUY-025", "department_name": "Port Logistics & Maritime Infrastructure", "ministry": "Ministry of Ports, Shipping and Waterways", "state_region": "Gujarat", "city": "Kandla", "budget_cr": 420.0},
    ]
    df_buyers = pd.DataFrame(buyers_data)
    df_buyers = df_buyers.rename(columns={"budget_cr": "budget_allocation_cr"})

    # -------------------------------------------------------------
    # 2. CANONICAL SUPPLIERS & REAL-WORLD NOISY VARIATIONS
    # -------------------------------------------------------------
    core_suppliers = [
        {"name": "Apex Infrastructure Projects Ltd", "region": "Maharashtra", "type": "Public Ltd", "msme": 0, "pan": "AAACA1234B"},
        {"name": "Zenith Global Technologies Pvt Ltd", "region": "Karnataka", "type": "Private Ltd", "msme": 1, "pan": "AABCZ9876C"},
        {"name": "Shree Ram Engineering Works", "region": "Uttar Pradesh", "type": "Proprietorship", "msme": 1, "pan": "AASPS5544D"},
        {"name": "Bharat Power Transmission Corp", "region": "Delhi", "type": "Public Ltd", "msme": 0, "pan": "AAACB4433E"},
        {"name": "Universal Medical Systems LLP", "region": "Delhi", "type": "LLP", "msme": 0, "pan": "AACCU7788F"},
        {"name": "Kaveri Water Solutions Pvt Ltd", "region": "Tamil Nadu", "type": "Private Ltd", "msme": 1, "pan": "AABCK1122G"},
        {"name": "Vanguard Security & Logistics Ltd", "region": "Delhi", "type": "Public Ltd", "msme": 0, "pan": "AAACV3344H"},
        {"name": "Himalayan Builders & Associates", "region": "Uttarakhand", "type": "Proprietorship", "msme": 1, "pan": "AABPH9988I"},
        {"name": "Sterling Digital Cloud Solutions Ltd", "region": "Karnataka", "type": "Public Ltd", "msme": 0, "pan": "AAACS6655J"},
        {"name": "Pragati Construction Consortium", "region": "Gujarat", "type": "JV", "msme": 0, "pan": "AAACP2211K"},
        {"name": "National Health Meditech Pvt Ltd", "region": "Uttar Pradesh", "type": "Private Ltd", "msme": 1, "pan": "AABCN4455L"},
        {"name": "Surya Solar Energy Systems Ltd", "region": "Rajasthan", "type": "Public Ltd", "msme": 0, "pan": "AAACS8899M"},
        {"name": "Delta Marine Infrastructure Co", "region": "Gujarat", "type": "Private Ltd", "msme": 0, "pan": "AABCD3322N"},
        {"name": "Indus Agritech & Storage Corp", "region": "Punjab", "type": "Private Ltd", "msme": 1, "pan": "AABCI6677O"},
        {"name": "Godavari Civil Projects Pvt Ltd", "region": "Andhra Pradesh", "type": "Private Ltd", "msme": 0, "pan": "AABCG5566P"},
        {"name": "Eastern Urban Planners LLP", "region": "Odisha", "type": "LLP", "msme": 1, "pan": "AACCE1133Q"},
        {"name": "Deccan Rail Infra Works Ltd", "region": "Telangana", "type": "Public Ltd", "msme": 0, "pan": "AAACD7744R"},
        {"name": "Royal Facilities Management Services", "region": "Delhi", "type": "Private Ltd", "msme": 1, "pan": "AABCR8833S"},
        {"name": "Pinnacle Consulting Engineers Pvt Ltd", "region": "Maharashtra", "type": "Private Ltd", "msme": 0, "pan": "AABCP9922T"},
        {"name": "Astra Defence Systems Corp", "region": "Delhi", "type": "Public Ltd", "msme": 0, "pan": "AAACA4411U"},
    ]
    
    # Generate 60 additional canonical suppliers to reach 80 robust suppliers
    for i in range(21, 81):
        corp_types = ["Private Ltd", "Public Ltd", "LLP", "Proprietorship", "JV"]
        regions = ["Maharashtra", "Karnataka", "Delhi", "Gujarat", "Tamil Nadu", "Uttar Pradesh", "Rajasthan", "Telangana", "Madhya Pradesh", "Odisha"]
        ctype = random.choice(corp_types)
        reg = random.choice(regions)
        core_suppliers.append({
            "name": f"Supplier Partner {i:03d} {ctype}",
            "region": reg,
            "type": ctype,
            "msme": 1 if ctype in ["Proprietorship", "LLP"] else random.choice([0, 1]),
            "pan": f"AAACX{i:04d}Z"
        })
        
    suppliers_records = []
    resolver = EntityResolver()
    
    for idx, s in enumerate(core_suppliers, start=1):
        sup_id = f"SUP-{idx:04d}"
        resolver.register_canonical_supplier(
            supplier_id=sup_id,
            canonical_name=s["name"],
            state_region=s["region"],
            registration_type=s["type"],
            pan_or_cin=s["pan"],
            is_msme=s["msme"]
        )
        suppliers_records.append({
            "supplier_id": sup_id,
            "canonical_name": s["name"],
            "registration_type": s["type"],
            "pan_or_cin": s["pan"],
            "state_region": s["region"],
            "is_msme": s["msme"]
        })
        
    df_suppliers = pd.DataFrame(suppliers_records)

    # -------------------------------------------------------------
    # 3. TENDERS, BIDS, AWARDS, AMENDMENTS, CANCELLATIONS
    # -------------------------------------------------------------
    categories = ["Works", "Goods", "Consulting Services", "Non-Consulting Services"]
    procurement_methods = ["Open Tender", "Limited Tender", "Single Source / Nomination"]
    
    tenders_list = []
    bids_list = []
    awards_list = []
    amendments_list = []
    cancellations_list = []
    
    # Simulated date range: Jan 1, 2022 to Nov 15, 2025
    start_date = datetime(2022, 1, 1)
    
    total_tenders = 1250
    bid_counter = 1
    award_counter = 1
    amendment_counter = 1
    cancellation_counter = 1
    
    # Pre-select anomalous supplier relationships:
    # BUY-001 (PWD Maharashtra) has a repeat favorite: SUP-0001 (Apex Infrastructure Projects Ltd)
    # BUY-004 (CMSS Delhi) has a repeat favorite: SUP-0005 (Universal Medical Systems LLP)
    # BUY-016 (NeGD IT) has repeat favorite: SUP-0002 (Zenith Global Technologies)
    # BUY-020 (Defence) has repeat favorite: SUP-0020 (Astra Defence Systems Corp)

    for t_idx in range(1, total_tenders + 1):
        tender_id = f"TEN-{t_idx:05d}"
        
        # Determine buyer
        # Introduce concentration bias for specific departments
        if t_idx % 7 == 0:
            buyer_id = "BUY-001" # PWD Road Wing
        elif t_idx % 11 == 0:
            buyer_id = "BUY-004" # CMSS Health
        elif t_idx % 13 == 0:
            buyer_id = "BUY-016" # NeGD IT
        else:
            buyer_id = random.choice(buyers_data)["buyer_id"]
            
        buyer_row = next(b for b in buyers_data if b["buyer_id"] == buyer_id)
        
        # Categorization based on buyer profile
        if "Road" in buyer_row["department_name"] or "Highway" in buyer_row["department_name"] or "Works" in buyer_row["department_name"]:
            cat = "Works"
        elif "Health" in buyer_row["department_name"] or "Medical" in buyer_row["department_name"]:
            cat = random.choice(["Goods", "Works"])
        elif "IT" in buyer_row["department_name"] or "e-Governance" in buyer_row["department_name"]:
            cat = random.choice(["Consulting Services", "Goods"])
        else:
            cat = random.choice(categories)
            
        # Publication date across the multi-year timeframe
        days_offset = random.randint(0, 1400)
        pub_date = start_date + timedelta(days=days_offset)
        
        # Bidding duration (Investigative feature: normally 21-30 days, but anomaly group has < 7 days)
        is_short_window = (random.random() < 0.08) # 8% tenders have abnormally short windows
        if is_short_window:
            duration_days = random.randint(3, 6) # Flag: Abnormally short window
        else:
            duration_days = random.randint(14, 45)
            
        submission_deadline = pub_date + timedelta(days=duration_days)
        bid_opening_date = submission_deadline + timedelta(days=1)
        
        # Estimated value based on category
        if cat == "Works":
            est_value = round(random.uniform(2_000_000, 250_000_000), 2) # 20 Lakhs to 25 Crores
        elif cat == "Goods":
            est_value = round(random.uniform(500_000, 80_000_000), 2)    # 5 Lakhs to 8 Crores
        elif cat == "Consulting Services":
            est_value = round(random.uniform(1_000_000, 35_000_000), 2)  # 10 Lakhs to 3.5 Crores
        else:
            est_value = round(random.uniform(300_000, 20_000_000), 2)
            
        emd = round(est_value * random.uniform(0.01, 0.03), 2)
        ref_no = f"NIT/{buyer_row['state_region'][:3].upper()}/{pub_date.year}/{cat[:3].upper()}/{t_idx:04d}"
        
        # Tender Status determination
        # 10% cancelled rate baseline
        is_cancelled = (random.random() < 0.11)
        if is_cancelled:
            status = "Cancelled"
        else:
            status = "Awarded"
            
        tenders_list.append({
            "tender_id": tender_id,
            "tender_reference_no": ref_no,
            "buyer_id": buyer_id,
            "title": f"Procurement of {cat.lower()} for {buyer_row['department_name']} ({ref_no})",
            "category": cat,
            "procurement_method": "Single Source / Nomination" if is_short_window and random.random() < 0.3 else random.choice(procurement_methods),
            "estimated_value_inr": est_value,
            "emd_amount_inr": emd,
            "publication_date": pub_date.strftime("%Y-%m-%d"),
            "bid_submission_deadline": submission_deadline.strftime("%Y-%m-%d"),
            "bid_opening_date": bid_opening_date.strftime("%Y-%m-%d"),
            "bidding_duration_days": duration_days,
            "status": status
        })
        
        # If cancelled, log cancellation
        if is_cancelled:
            cancellation_date = submission_deadline + timedelta(days=random.randint(1, 15))
            reason_cat = random.choice([
                "Single Bidder Quoted",
                "Administrative Prerogative",
                "Budget Withdrawal",
                "Technical Disqualification of All",
                "Litigation / Injunction"
            ])
            cancellations_list.append({
                "cancellation_id": f"CAN-{cancellation_counter:05d}",
                "tender_id": tender_id,
                "cancellation_date": cancellation_date.strftime("%Y-%m-%d"),
                "reason_category": reason_cat,
                "detailed_reason": f"Tender annulled under section 25(b) due to {reason_cat.lower()}."
            })
            cancellation_counter += 1
            continue # No award for cancelled tenders
            
        # -------------------------------------------------------------
        # Generate Bids & Awards for Completed Tenders
        # -------------------------------------------------------------
        # Determine number of bidders (Single-bidder anomaly check)
        is_single_bidder_award = (random.random() < 0.09) # 9% single bidder awards
        num_bidders = 1 if is_single_bidder_award else random.randint(2, 6)
        
        # Select participating suppliers
        # Check if buyer has favored repeat winner
        if buyer_id == "BUY-001" and random.random() < 0.70:
            winning_sup_id = "SUP-0001" # Apex Infrastructure Projects Ltd
        elif buyer_id == "BUY-004" and random.random() < 0.65:
            winning_sup_id = "SUP-0005" # Universal Medical Systems LLP
        elif buyer_id == "BUY-016" and random.random() < 0.65:
            winning_sup_id = "SUP-0002" # Zenith Global Technologies Pvt Ltd
        elif buyer_id == "BUY-020" and random.random() < 0.60:
            winning_sup_id = "SUP-0020" # Astra Defence Systems Corp
        else:
            winning_sup_id = random.choice(suppliers_records)["supplier_id"]
            
        competing_pool = [s["supplier_id"] for s in suppliers_records if s["supplier_id"] != winning_sup_id]
        other_bidders = random.sample(competing_pool, num_bidders - 1) if num_bidders > 1 else []
        
        # Generate winning bid
        winning_discount = random.uniform(0.92, 0.99) # 1% to 8% below estimate
        winning_bid_amount = round(est_value * winning_discount, 2)
        
        bids_list.append({
            "bid_id": f"BID-{bid_counter:06d}",
            "tender_id": tender_id,
            "supplier_id": winning_sup_id,
            "raw_supplier_name": next(s["canonical_name"] for s in suppliers_records if s["supplier_id"] == winning_sup_id),
            "bid_amount_inr": winning_bid_amount,
            "submission_timestamp": (submission_deadline - timedelta(hours=random.randint(2, 48))).strftime("%Y-%m-%d %H:%M:%S"),
            "technical_qualified": 1,
            "is_winning_bid": 1
        })
        bid_counter += 1
        
        # Generate losing bids
        for ob_id in other_bidders:
            losing_bid_amount = round(winning_bid_amount * random.uniform(1.02, 1.25), 2)
            tech_pass = 1 if random.random() > 0.15 else 0
            bids_list.append({
                "bid_id": f"BID-{bid_counter:06d}",
                "tender_id": tender_id,
                "supplier_id": ob_id,
                "raw_supplier_name": next(s["canonical_name"] for s in suppliers_records if s["supplier_id"] == ob_id),
                "bid_amount_inr": losing_bid_amount,
                "submission_timestamp": (submission_deadline - timedelta(hours=random.randint(4, 96))).strftime("%Y-%m-%d %H:%M:%S"),
                "technical_qualified": tech_pass,
                "is_winning_bid": 0
            })
            bid_counter += 1
            
        # -------------------------------------------------------------
        # Create Award Record
        # -------------------------------------------------------------
        award_date = bid_opening_date + timedelta(days=random.randint(5, 30))
        award_id = f"AWD-{award_counter:05d}"
        
        # Contract Amendments & Value Creep Anomaly
        # Specific cluster has high post-award value escalation (> 30%)
        has_escalation_anomaly = (random.random() < 0.12) # 12% tenders suffer major value escalation
        num_amendments = random.randint(2, 4) if has_escalation_anomaly else (1 if random.random() < 0.25 else 0)
        
        initial_value = winning_bid_amount
        accumulated_amendment_value = 0.0
        
        for a_idx in range(1, num_amendments + 1):
            if has_escalation_anomaly:
                pct_inc = random.uniform(0.12, 0.25) # 12% to 25% bump per amendment
                justification = random.choice(["Design Scope Change", "Price Index Adjustment", "Emergency Works"])
            else:
                pct_inc = random.uniform(0.01, 0.05) # normal small variation
                justification = "Administrative"
                
            val_change = round(initial_value * pct_inc, 2)
            accumulated_amendment_value += val_change
            amendDate = award_date + timedelta(days=random.randint(40 * a_idx, 90 * a_idx))
            
            amendments_list.append({
                "amendment_id": f"AMD-{amendment_counter:05d}",
                "award_id": award_id,
                "amendment_sequence": a_idx,
                "amendment_date": amendDate.strftime("%Y-%m-%d"),
                "amendment_type": "Value Escalation" if val_change > 0 else "Time Extension",
                "value_change_inr": val_change,
                "time_extension_days": random.randint(30, 90) if random.random() > 0.4 else 0,
                "justification_code": justification,
                "description": f"Amendment #{a_idx} approved due to {justification.lower()} requirement."
            })
            amendment_counter += 1
            
        final_settled = round(initial_value + accumulated_amendment_value, 2)
        awards_list.append({
            "award_id": award_id,
            "tender_id": tender_id,
            "supplier_id": winning_sup_id,
            "award_date": award_date.strftime("%Y-%m-%d"),
            "initial_contract_value_inr": initial_value,
            "final_settled_value_inr": final_settled,
            "contract_status": random.choice(["Active", "Completed", "Active", "Completed", "Under Review"])
        })
        award_counter += 1

    df_tenders = pd.DataFrame(tenders_list)
    df_bids = pd.DataFrame(bids_list)
    df_awards = pd.DataFrame(awards_list)
    df_amendments = pd.DataFrame(amendments_list)
    df_cancellations = pd.DataFrame(cancellations_list)
    df_raw_suppliers = resolver.get_audit_dataframe()
    
    return df_buyers, df_suppliers, df_raw_suppliers, df_tenders, df_bids, df_awards, df_amendments, df_cancellations

def run_pipeline() -> None:
    """Execute complete ingestion, validation, resolution, and database population."""
    print("=" * 70)
    print("BIDWATCH PIPELINE: Initializing Procurement Data Processing...")
    print("=" * 70)
    
    # 1. Initialize DB schema
    print("[1/5] Initializing Database Schema...")
    initialize_database(drop_existing=True)
    
    # 2. Generate and resolve benchmark records
    print("[2/5] Synthesizing and Resolving Procurement Records...")
    (
        df_buyers, df_suppliers, df_raw_suppliers,
        df_tenders, df_bids, df_awards, df_amendments, df_cancellations
    ) = generate_benchmark_procurement_data(seed=101)
    
    # 3. Clean and validate data types
    print("[3/5] Performing Schema Validation and Normalization...")
    df_buyers["department_name"] = df_buyers["department_name"].apply(clean_whitespace)
    df_buyers["budget_allocation_cr"] = df_buyers["budget_allocation_cr"].apply(normalize_currency)
    
    df_suppliers["canonical_name"] = df_suppliers["canonical_name"].apply(normalize_company_name)
    
    df_tenders["estimated_value_inr"] = df_tenders["estimated_value_inr"].apply(normalize_currency)
    df_tenders["emd_amount_inr"] = df_tenders["emd_amount_inr"].apply(normalize_currency)
    df_tenders["publication_date"] = df_tenders["publication_date"].apply(normalize_date)
    df_tenders["bid_submission_deadline"] = df_tenders["bid_submission_deadline"].apply(normalize_date)
    df_tenders["bid_opening_date"] = df_tenders["bid_opening_date"].apply(normalize_date)
    
    df_bids["bid_amount_inr"] = df_bids["bid_amount_inr"].apply(normalize_currency)
    df_awards["initial_contract_value_inr"] = df_awards["initial_contract_value_inr"].apply(normalize_currency)
    df_awards["final_settled_value_inr"] = df_awards["final_settled_value_inr"].apply(normalize_currency)
    df_amendments["value_change_inr"] = df_amendments["value_change_inr"].apply(normalize_currency)
    
    # 4. Save to Database
    print("[4/5] Storing Cleaned Entities in Relational SQLite Store...")
    engine = get_engine()
    with engine.begin() as conn:
        df_buyers.to_sql("buyers", conn, if_exists="append", index=False)
        df_suppliers.to_sql("suppliers", conn, if_exists="append", index=False)
        if not df_raw_suppliers.empty:
            df_raw_suppliers.to_sql("raw_suppliers", conn, if_exists="append", index=False)
        df_tenders.to_sql("tenders", conn, if_exists="append", index=False)
        df_bids.to_sql("bids", conn, if_exists="append", index=False)
        df_awards.to_sql("awards", conn, if_exists="append", index=False)
        df_amendments.to_sql("amendments", conn, if_exists="append", index=False)
        df_cancellations.to_sql("cancellations", conn, if_exists="append", index=False)
        
    # 5. Export clean CSVs for Power BI and raw audit
    print("[5/5] Generating Power BI CSV Exports and Raw Snapshots...")
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    POWERBI_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    
    table_dict = {
        "buyers": df_buyers,
        "suppliers": df_suppliers,
        "raw_suppliers": df_raw_suppliers,
        "tenders": df_tenders,
        "bids": df_bids,
        "awards": df_awards,
        "amendments": df_amendments,
        "cancellations": df_cancellations
    }
    
    for name, df in table_dict.items():
        df.to_csv(PROCESSED_DATA_DIR / f"{name}.csv", index=False)
        df.to_csv(POWERBI_EXPORT_DIR / f"{name}.csv", index=False)
        # Snapshot raw sample
        df.head(25).to_csv(RAW_DATA_DIR / f"sample_{name}_raw.csv", index=False)
        
    print("\nSUCCESS: Ingestion and Curation Pipeline complete!")
    print(f"- Database: {DEFAULT_DB_PATH}")
    print(f"- Total Buyers: {len(df_buyers)}")
    print(f"- Total Suppliers: {len(df_suppliers)}")
    print(f"- Total Tenders: {len(df_tenders)}")
    print(f"- Total Bids: {len(df_bids)}")
    print(f"- Total Awards: {len(df_awards)}")
    print(f"- Total Amendments: {len(df_amendments)}")
    print(f"- Total Cancellations: {len(df_cancellations)}")
    print(f"- Power BI Exports: {POWERBI_EXPORT_DIR}")
    print("=" * 70)

if __name__ == "__main__":
    run_pipeline()

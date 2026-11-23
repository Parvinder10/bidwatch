"""
FastAPI Procurement Analytics REST API for BIDWATCH.
Serves live procurement intelligence, antitrust HHI concentration metrics,
supplier repeat awards, contract escalations, and investigative leads.
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import pandas as pd

from src.ingestion.database import get_engine, DEFAULT_DB_PATH
from src.analytics.queries import (
    get_executive_kpis,
    get_department_spending,
    get_supplier_market_share,
    get_repeat_supplier_awards,
    get_supplier_concentration_hhi,
    get_cancellation_rates,
    get_amendment_escalations,
    get_geographic_distribution,
    get_temporal_trends,
    get_supplier_participation
)

# Auto self-healing check
if not DEFAULT_DB_PATH.exists():
    try:
        from src.ingestion.pipeline import run_pipeline
        from src.indicators.investigative_engine import run_indicators
        run_pipeline()
        run_indicators()
    except Exception as e:
        print(f"Warning initializing database: {e}")

app = FastAPI(
    title="BIDWATCH Procurement Analytics API",
    description="REST API for public procurement intelligence, investigative indicators, and tender auditing.",
    version="1.0.0"
)

# CORS configuration
raw_cors = os.getenv("CORS_ORIGINS", "*")
origins = [o.strip() for o in raw_cors.split(",") if o.strip()]
if "*" in origins:
    allow_origins = ["*"]
else:
    allow_origins = origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    """Health and data provenance check."""
    return {
        "status": "healthy",
        "platform": "BIDWATCH Public Procurement Intelligence",
        "dataset_notice": "Benchmark / Demonstration Dataset modeled on CPPP/GeM Public Procurement Standards",
        "database": DEFAULT_DB_PATH.name,
        "database_available": DEFAULT_DB_PATH.exists(),
        "disclaimer": "Analytical findings indicate patterns requiring human verification and do not constitute accusations of wrongdoing."
    }

@app.get("/api/filters")
def get_filters():
    """Get dynamic filter options for departments, categories, and states."""
    engine = get_engine()
    with engine.connect() as conn:
        depts = [r[0] for r in conn.execute(text("SELECT DISTINCT department_name FROM buyers ORDER BY department_name")).fetchall()]
        cats = [r[0] for r in conn.execute(text("SELECT DISTINCT category FROM tenders ORDER BY category")).fetchall()]
        regions = [r[0] for r in conn.execute(text("SELECT DISTINCT state_region FROM buyers ORDER BY state_region")).fetchall()]
        min_date, max_date = conn.execute(text("SELECT MIN(publication_date), MAX(publication_date) FROM tenders")).fetchone()
    return {
        "departments": depts,
        "categories": cats,
        "regions": regions,
        "min_date": str(min_date) if min_date else None,
        "max_date": str(max_date) if max_date else None
    }

@app.get("/api/kpis")
def get_kpis(
    dept: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Retrieve executive procurement KPIs."""
    return get_executive_kpis(
        dept_filter=dept if dept != "All" else None,
        category_filter=category if category != "All" else None,
        state_filter=region if region != "All" else None,
        start_date=start_date,
        end_date=end_date
    )

@app.get("/api/departments")
def get_departments(
    dept: Optional[str] = Query(None),
    region: Optional[str] = Query(None)
):
    """Retrieve department procurement spending and budget utilization."""
    df = get_department_spending(dept_filter=dept, state_filter=region)
    return df.to_dict(orient="records")

@app.get("/api/suppliers")
def get_suppliers(top_n: int = Query(25, ge=1, le=100)):
    """Retrieve top suppliers by market share and contracts won."""
    df = get_supplier_market_share(top_n=top_n)
    return df.to_dict(orient="records")

@app.get("/api/concentration/hhi")
def get_hhi():
    """Retrieve Herfindahl-Hirschman Index (HHI) vendor concentration scores."""
    df = get_supplier_concentration_hhi()
    return df.to_dict(orient="records")

@app.get("/api/relationships/repeat-wins")
def get_repeat_wins(min_wins: int = Query(3, ge=1)):
    """Retrieve buyer-supplier repeat award pairings."""
    df = get_repeat_supplier_awards(min_wins=min_wins)
    return df.to_dict(orient="records")

@app.get("/api/escalations")
def get_escalations(min_escalation_pct: float = Query(0.0, ge=0.0)):
    """Retrieve post-award contract value escalation and amendments."""
    df = get_amendment_escalations(min_escalation_pct=min_escalation_pct)
    return df.to_dict(orient="records")

@app.get("/api/cancellations")
def get_cancellations():
    """Retrieve department cancellation rates and annulment justifications."""
    df = get_cancellation_rates()
    engine = get_engine()
    with engine.connect() as conn:
        reasons = pd.read_sql_query(text("""
            SELECT reason_category, COUNT(*) AS count_cases
            FROM cancellations
            GROUP BY reason_category
            ORDER BY count_cases DESC
        """), conn).to_dict(orient="records")
    return {
        "department_cancellations": df.to_dict(orient="records"),
        "reasons_breakdown": reasons
    }

@app.get("/api/participation")
def get_participation():
    """Retrieve supplier participation, win rates, and single-bidder conversion."""
    df = get_supplier_participation()
    return df.to_dict(orient="records")

@app.get("/api/geography")
def get_geography():
    """Retrieve interstate vs intra-state procurement flow distribution."""
    df = get_geographic_distribution()
    return df.to_dict(orient="records")

@app.get("/api/temporal-trends")
def get_trends():
    """Retrieve temporal monthly expenditure, MoM, and YoY growth rates."""
    df = get_temporal_trends()
    return df.to_dict(orient="records")

@app.get("/api/leads")
def get_leads(
    severity: Optional[str] = Query(None),
    indicator: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None)
):
    """Retrieve structured 5-point investigative leads and anomaly dossiers."""
    engine = get_engine()
    query = "SELECT * FROM investigative_leads WHERE 1=1"
    params = {}
    if severity and severity != "All":
        query += " AND severity = :sev"
        params["sev"] = severity
    if indicator and indicator != "All":
        query += " AND indicator_code = :ind"
        params["ind"] = indicator
    if entity_type and entity_type != "All":
        query += " AND entity_type = :ent"
        params["ent"] = entity_type
    query += " ORDER BY severity ASC, lead_id ASC"
    
    with engine.connect() as conn:
        df = pd.read_sql_query(text(query), conn, params=params)
        
    records = df.to_dict(orient="records")
    for r in records:
        try:
            r["supporting_fields"] = json.loads(r["supporting_fields"])
        except Exception:
            pass
    return records

@app.get("/api/tenders")
def search_tenders(
    q: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200)
):
    """Search tender notices and filter by category or status."""
    engine = get_engine()
    clauses = ["1=1"]
    params: Dict[str, Any] = {"lim": limit}
    if q:
        clauses.append("(t.tender_reference_no LIKE :q OR t.title LIKE :q OR b.department_name LIKE :q)")
        params["q"] = f"%{q}%"
    if category and category != "All":
        clauses.append("t.category = :cat")
        params["cat"] = category
    if status and status != "All":
        clauses.append("t.status = :stat")
        params["stat"] = status
        
    sql = f"""
        SELECT t.*, b.department_name, b.ministry, b.state_region AS buyer_state
        FROM tenders t
        JOIN buyers b ON t.buyer_id = b.buyer_id
        WHERE {' AND '.join(clauses)}
        ORDER BY t.publication_date DESC
        LIMIT :lim
    """
    with engine.connect() as conn:
        df = pd.read_sql_query(text(sql), conn, params=params)
    return df.to_dict(orient="records")

@app.get("/api/tenders/{ref:path}")
def get_tender_detail(ref: str):
    """Retrieve complete lifecycle audit for an individual tender record."""
    engine = get_engine()
    with engine.connect() as conn:
        tender = conn.execute(text("""
            SELECT t.*, b.department_name, b.ministry, b.state_region AS buyer_state, b.city
            FROM tenders t
            JOIN buyers b ON t.buyer_id = b.buyer_id
            WHERE t.tender_reference_no = :ref
        """), {"ref": ref}).mappings().first()
        
        if not tender:
            raise HTTPException(status_code=404, detail="Tender reference not found")
            
        bids = pd.read_sql_query(text("""
            SELECT b.bid_id, s.canonical_name AS bidder_name, b.bid_amount_inr, 
                   b.technical_qualified, b.is_winning_bid, b.submission_timestamp
            FROM bids b
            JOIN suppliers s ON b.supplier_id = s.supplier_id
            JOIN tenders t ON b.tender_id = t.tender_id
            WHERE t.tender_reference_no = :ref
            ORDER BY b.bid_amount_inr ASC
        """), conn, params={"ref": ref}).to_dict(orient="records")
        
        award = conn.execute(text("""
            SELECT a.*, s.canonical_name AS winning_supplier_name
            FROM awards a
            JOIN suppliers s ON a.supplier_id = s.supplier_id
            JOIN tenders t ON a.tender_id = t.tender_id
            WHERE t.tender_reference_no = :ref
        """), {"ref": ref}).mappings().first()
        
        amendments = pd.read_sql_query(text("""
            SELECT amd.amendment_sequence, amd.amendment_date, amd.amendment_type, 
                   amd.value_change_inr, amd.time_extension_days, amd.justification_code, amd.description
            FROM amendments amd
            JOIN awards a ON amd.award_id = a.award_id
            JOIN tenders t ON a.tender_id = t.tender_id
            WHERE t.tender_reference_no = :ref
            ORDER BY amd.amendment_sequence ASC
        """), conn, params={"ref": ref}).to_dict(orient="records")
        
        cancellation = conn.execute(text("""
            SELECT c.* 
            FROM cancellations c
            JOIN tenders t ON c.tender_id = t.tender_id
            WHERE t.tender_reference_no = :ref
        """), {"ref": ref}).mappings().first()

    return {
        "tender": dict(tender),
        "bids": bids,
        "award": dict(award) if award else None,
        "amendments": amendments,
        "cancellation": dict(cancellation) if cancellation else None
    }

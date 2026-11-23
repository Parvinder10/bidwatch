"""
Parameterized analytical query engine for BIDWATCH.
Executes analytical SQL workflows with dynamic filters and returns Pandas DataFrames.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd
from sqlalchemy import text

from src.ingestion.database import get_engine, DEFAULT_DB_PATH

SQL_DIR = Path(__file__).resolve().parent.parent.parent / "sql"

def load_sql(filename: str) -> str:
    """Read a raw SQL script file by filename."""
    file_path = SQL_DIR / filename
    if not file_path.exists():
        raise FileNotFoundError(f"SQL file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def get_executive_kpis(
    dept_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
    state_filter: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """Calculate executive high-level procurement metrics with active filters."""
    engine = get_engine()
    
    where_clauses = ["1=1"]
    params = {}
    
    if dept_filter and dept_filter != "All":
        where_clauses.append("b.department_name = :dept")
        params["dept"] = dept_filter
    if category_filter and category_filter != "All":
        where_clauses.append("t.category = :cat")
        params["cat"] = category_filter
    if state_filter and state_filter != "All":
        where_clauses.append("b.state_region = :state")
        params["state"] = state_filter
    if start_date:
        where_clauses.append("t.publication_date >= :start_date")
        params["start_date"] = start_date
    if end_date:
        where_clauses.append("t.publication_date <= :end_date")
        params["end_date"] = end_date
        
    filter_sql = " AND ".join(where_clauses)
    
    query = f"""
    SELECT 
        COUNT(DISTINCT t.tender_id) AS total_tenders,
        COUNT(DISTINCT CASE WHEN t.status = 'Awarded' THEN t.tender_id END) AS total_awarded,
        COUNT(DISTINCT CASE WHEN t.status = 'Cancelled' THEN t.tender_id END) AS total_cancelled,
        COUNT(DISTINCT a.supplier_id) AS active_suppliers,
        COUNT(DISTINCT t.buyer_id) AS active_buyers,
        COALESCE(SUM(t.estimated_value_inr), 0) AS total_estimated_value,
        COALESCE(SUM(a.initial_contract_value_inr), 0) AS total_initial_awarded,
        COALESCE(SUM(a.final_settled_value_inr), 0) AS total_settled_awarded,
        COALESCE(SUM(CASE WHEN t.status = 'Cancelled' THEN t.estimated_value_inr ELSE 0 END), 0) AS cancelled_value
    FROM tenders t
    JOIN buyers b ON t.buyer_id = b.buyer_id
    LEFT JOIN awards a ON t.tender_id = a.tender_id
    WHERE {filter_sql}
    """
    
    with engine.connect() as conn:
        res = conn.execute(text(query), params).mappings().first()
        
    if not res:
        return {}
        
    tot_tenders = res["total_tenders"] or 0
    tot_awarded = res["total_awarded"] or 0
    tot_cancelled = res["total_cancelled"] or 0
    settled_val = res["total_settled_awarded"] or 0.0
    initial_val = res["total_initial_awarded"] or 0.0
    escalation_val = settled_val - initial_val
    
    return {
        "total_tenders": tot_tenders,
        "total_awarded": tot_awarded,
        "total_cancelled": tot_cancelled,
        "cancellation_rate_pct": round((tot_cancelled * 100.0 / tot_tenders), 2) if tot_tenders > 0 else 0.0,
        "active_suppliers": res["active_suppliers"] or 0,
        "active_buyers": res["active_buyers"] or 0,
        "total_settled_value_cr": round(settled_val / 10_000_000.0, 2),
        "total_initial_value_cr": round(initial_val / 10_000_000.0, 2),
        "total_escalation_cr": round(escalation_val / 10_000_000.0, 2),
        "avg_award_value_lakhs": round((settled_val / tot_awarded) / 100_000.0, 2) if tot_awarded > 0 else 0.0
    }

def get_department_spending(
    dept_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
    state_filter: Optional[str] = None
) -> pd.DataFrame:
    """Fetch department-wise spend, budget utilization, and tender volumes."""
    engine = get_engine()
    raw_sql = load_sql("01_department_procurement_summary.sql")
    with engine.connect() as conn:
        df = pd.read_sql_query(text(raw_sql), conn)
        
    if dept_filter and dept_filter != "All":
        df = df[df["department_name"] == dept_filter]
    if state_filter and state_filter != "All":
        df = df[df["state_region"] == state_filter]
    return df

def get_supplier_market_share(top_n: int = 20) -> pd.DataFrame:
    """Fetch top suppliers by market share and contract count."""
    engine = get_engine()
    raw_sql = load_sql("02_supplier_market_share_top_winners.sql")
    with engine.connect() as conn:
        df = pd.read_sql_query(text(raw_sql), conn)
    return df.head(top_n)

def get_repeat_supplier_awards(min_wins: int = 3) -> pd.DataFrame:
    """Fetch repeat buyer-supplier pairing records."""
    engine = get_engine()
    raw_sql = load_sql("03_repeat_supplier_awards.sql")
    with engine.connect() as conn:
        df = pd.read_sql_query(text(raw_sql), conn)
    return df[df["awards_won_from_buyer"] >= min_wins]

def get_supplier_concentration_hhi() -> pd.DataFrame:
    """Fetch department Herfindahl-Hirschman Index (HHI) concentration scores."""
    engine = get_engine()
    raw_sql = load_sql("04_supplier_concentration_hhi.sql")
    with engine.connect() as conn:
        return pd.read_sql_query(text(raw_sql), conn)

def get_cancellation_rates() -> pd.DataFrame:
    """Fetch department cancellation metrics and risk categories."""
    engine = get_engine()
    raw_sql = load_sql("05_tender_cancellation_rates.sql")
    with engine.connect() as conn:
        return pd.read_sql_query(text(raw_sql), conn)

def get_amendment_escalations(min_escalation_pct: float = 0.0) -> pd.DataFrame:
    """Fetch contract amendments and cost escalation data."""
    engine = get_engine()
    raw_sql = load_sql("06_contract_amendment_escalation.sql")
    with engine.connect() as conn:
        df = pd.read_sql_query(text(raw_sql), conn)
    if min_escalation_pct > 0:
        df = df[df["escalation_percentage"] >= min_escalation_pct]
    return df

def get_geographic_distribution() -> pd.DataFrame:
    """Fetch geographic procurement flows between buyer and supplier states."""
    engine = get_engine()
    raw_sql = load_sql("07_geographic_spending_distribution.sql")
    with engine.connect() as conn:
        return pd.read_sql_query(text(raw_sql), conn)

def get_temporal_trends() -> pd.DataFrame:
    """Fetch monthly spend, contract counts, MoM and YoY trends."""
    engine = get_engine()
    raw_sql = load_sql("08_time_trends_mom_yoy.sql")
    with engine.connect() as conn:
        return pd.read_sql_query(text(raw_sql), conn)

def get_supplier_participation() -> pd.DataFrame:
    """Fetch supplier bidding volume, win rates, and single bidder metrics."""
    engine = get_engine()
    raw_sql = load_sql("09_supplier_participation_and_win_rate.sql")
    with engine.connect() as conn:
        return pd.read_sql_query(text(raw_sql), conn)

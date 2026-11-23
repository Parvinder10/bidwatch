"""
Automated Report Generation Engine for BIDWATCH.
Generates comprehensive executive audit reports, department dossiers, 
and supplier investigation reports in Markdown and Text formats.
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd
from sqlalchemy import text

from src.ingestion.database import get_engine
from src.analytics.queries import (
    get_executive_kpis,
    get_department_spending,
    get_supplier_market_share,
    get_repeat_supplier_awards,
    get_supplier_concentration_hhi,
    get_cancellation_rates,
    get_amendment_escalations
)

REPORTS_DIR = PROJECT_ROOT / "reports"

def generate_executive_summary_report() -> str:
    """Generate comprehensive executive vigilance briefing report."""
    kpis = get_executive_kpis()
    df_hhi = get_supplier_concentration_hhi()
    critical_hhi = df_hhi[df_hhi["hhi_score"] > 2500]
    df_repeat = get_repeat_supplier_awards(min_wins=3)
    critical_repeat = df_repeat[df_repeat["buyer_spend_share_pct"] >= 40.0]
    df_esc = get_amendment_escalations(min_escalation_pct=30.0)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    md = f"""# BIDWATCH: Executive Procurement Intelligence & Vigilance Briefing
**Generated At:** {timestamp}  
**Classification:** Confidential Audit & Investigative Lead Summary  

---

## 1. Macro Procurement Key Performance Indicators

- **Total Published Tenders:** {kpis.get('total_tenders', 0):,} notices
- **Total Awarded Contracts:** {kpis.get('total_awarded', 0):,} contracts
- **Total Cancelled Tenders:** {kpis.get('total_cancelled', 0):,} ({kpis.get('cancellation_rate_pct', 0.0)}% cancellation rate)
- **Total Initial Awarded Value:** ₹{kpis.get('total_initial_value_cr', 0.0):,.2f} Crores
- **Final Settled Procurement Spend:** ₹{kpis.get('total_settled_value_cr', 0.0):,.2f} Crores
- **Net Post-Award Cost Escalation:** +₹{kpis.get('total_escalation_cr', 0.0):,.2f} Crores (+{round(kpis.get('total_escalation_cr', 0.0) / max(1.0, kpis.get('total_initial_value_cr', 1.0)) * 100, 2)}% growth)
- **Active Procuring Buyers:** {kpis.get('active_buyers', 0)} departments
- **Active Participating Suppliers:** {kpis.get('active_suppliers', 0)} canonical corporate entities

---

## 2. Priority 1: High Supplier Concentration (HHI > 2500)
Departmental procurement ecosystems exhibiting oligopolistic concentration exceeding DOJ antitrust guidelines:

| Buyer ID | Department Name | Ministry | Total Contracts | HHI Score | Total Spend (₹ Cr) | Risk Priority |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
"""
    for _, row in critical_hhi.iterrows():
        md += f"| `{row['buyer_id']}` | {row['department_name']} | {row['ministry']} | {row['total_contracts']} | **{row['hhi_score']:.1f}** | ₹{row['total_dept_spend_cr']:.2f} Cr | **{row['investigative_audit_priority']}** |\n"

    md += f"""
---

## 3. Priority 2: Entrenched Buyer-Supplier Relationships
Contractors capturing >= 40% of a department's procurement budget:

| Department | Favored Supplier | Awards Won | Buyer Spend Share % | Captured Spend (₹ Cr) |
| :--- | :--- | :---: | :---: | :---: |
"""
    for _, row in critical_repeat.head(8).iterrows():
        md += f"| {row['department_name']} | **{row['supplier_name']}** | {row['awards_won_from_buyer']} | **{row['buyer_spend_share_pct']:.1f}%** | ₹{row['spend_captured_cr']:.2f} Cr |\n"

    md += f"""
---

## 4. Priority 3: Severe Post-Award Cost Overruns (> 30% Escalation)
Contracts demonstrating potential low-ball predatory bidding with subsequent expansion:

| Tender Reference | Department | Supplier | Initial (₹ L) | Final (₹ L) | Escalation % | Delay (Days) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
"""
    for _, row in df_esc.head(8).iterrows():
        md += f"| `{row['tender_reference_no']}` | {row['department_name'][:30]} | {row['supplier_name'][:25]} | ₹{row['initial_value_lakhs']:.2f} L | ₹{row['final_value_lakhs']:.2f} L | **+{row['escalation_percentage']:.1f}%** | {row['total_delay_days']} |\n"

    md += """
---

## 5. Auditor Action Items & Statutory Follow-Up
1. **Qualification Criteria Audit:** Examine whether restrictive turnover or prior-experience terms in standard bidding documents restricted competitor entry.
2. **Amendment Sanction Review:** Verify delegated financial powers of officials approving contract value extensions exceeding statutory variation caps.
3. **Single-Bidder Price Reasonableness:** Conduct market price benchmarking on single-bidder awards to detect inflated rate cards.
"""
    return md

def generate_department_audit_report(dept_name: str) -> str:
    """Generate targeted audit report for a specific procuring department."""
    engine = get_engine()
    with engine.connect() as conn:
        dept_info = conn.execute(text("""
            SELECT b.*, 
                   COUNT(DISTINCT t.tender_id) AS total_tenders,
                   COUNT(DISTINCT CASE WHEN t.status = 'Awarded' THEN t.tender_id END) AS awarded_tenders,
                   COUNT(DISTINCT CASE WHEN t.status = 'Cancelled' THEN t.tender_id END) AS cancelled_tenders,
                   COALESCE(SUM(a.initial_contract_value_inr), 0) / 10000000.0 AS initial_spend_cr,
                   COALESCE(SUM(a.final_settled_value_inr), 0) / 10000000.0 AS settled_spend_cr
            FROM buyers b
            LEFT JOIN tenders t ON b.buyer_id = t.buyer_id
            LEFT JOIN awards a ON t.tender_id = a.tender_id
            WHERE b.department_name = :dname
            GROUP BY b.buyer_id
        """), {"dname": dept_name}).mappings().first()
        
        if not dept_info:
            return f"# Department Audit Report\n\nDepartment '{dept_name}' not found."
            
        # Top suppliers for this department
        top_supp = pd.read_sql_query(text("""
            SELECT s.canonical_name, COUNT(a.award_id) AS awards_won,
                   SUM(a.final_settled_value_inr) / 10000000.0 AS spend_cr,
                   ROUND(SUM(a.final_settled_value_inr) * 100.0 / NULLIF(:tot, 0), 2) AS spend_share_pct
            FROM tenders t
            JOIN awards a ON t.tender_id = a.tender_id
            JOIN suppliers s ON a.supplier_id = s.supplier_id
            WHERE t.buyer_id = :bid
            GROUP BY s.canonical_name
            ORDER BY spend_cr DESC
        """), conn, params={"bid": dept_info["buyer_id"], "tot": dept_info["settled_spend_cr"] * 10000000.0})

    md = f"""# Procurement Integrity Audit: {dept_info['department_name']}
**Ministry:** {dept_info['ministry']}  
**Jurisdiction:** {dept_info['state_region']}, {dept_info['city']}  
**Sanctioned Budget:** ₹{dept_info['budget_allocation_cr']:.2f} Crores  

---

### Procurement Activity Overview
- **Total Published Notices:** {dept_info['total_tenders']}
- **Awarded Contracts:** {dept_info['awarded_tenders']}
- **Cancelled Tenders:** {dept_info['cancelled_tenders']} ({round(dept_info['cancelled_tenders'] * 100.0 / max(1, dept_info['total_tenders']), 1)}%)
- **Total Settled Procurement Expenditure:** ₹{dept_info['settled_spend_cr']:.2f} Crores
- **Net Cost Growth Post-Award:** +₹{dept_info['settled_spend_cr'] - dept_info['initial_spend_cr']:.2f} Crores

---

### Top Contractors by Share of Department Expenditure
| Supplier Name | Contracts Won | Spend Captured (₹ Cr) | % of Department Spend |
| :--- | :---: | :---: | :---: |
"""
    for _, row in top_supp.head(10).iterrows():
        md += f"| **{row['canonical_name']}** | {row['awards_won']} | ₹{row['spend_cr']:.2f} Cr | **{row['spend_share_pct']}%** |\n"

    md += """
---
### Specific Recommendations for Field Audit:
1. Examine if qualifying criteria in standard bidding documents disproportionately favored top suppliers.
2. Review technical evaluation scores for non-winning bidders.
"""
    return md

def save_all_reports_to_disk() -> None:
    """Generate and write standard audit reports to reports/ directory."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Executive Summary
    exec_md = generate_executive_summary_report()
    with open(REPORTS_DIR / "EXECUTIVE_INVESTIGATIVE_SUMMARY.md", "w", encoding="utf-8") as f:
        f.write(exec_md)
        
    # 2. Department Concentration Audit
    df_hhi = get_supplier_concentration_hhi()
    top_dept_name = df_hhi.iloc[0]["department_name"] if not df_hhi.empty else "Public Works Department - Road Wing"
    dept_md = generate_department_audit_report(top_dept_name)
    with open(REPORTS_DIR / "DEPARTMENT_CONCENTRATION_AUDIT.md", "w", encoding="utf-8") as f:
        f.write(dept_md)
        
    # 3. Cost Escalation Audit
    df_esc = get_amendment_escalations(min_escalation_pct=25.0)
    esc_md = f"""# BIDWATCH: Contract Cost Escalation & Corrigenda Audit
*Automated Audit of High Value Post-Award Variations*

Total Contracts with >= 25% Cost Escalation: **{len(df_esc)}**

| Tender Reference | Department | Supplier Name | Initial (₹ Lakhs) | Final (₹ Lakhs) | Escalation % | Delay (Days) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
"""
    for _, row in df_esc.head(25).iterrows():
        esc_md += f"| `{row['tender_reference_no']}` | {row['department_name']} | {row['supplier_name']} | ₹{row['initial_value_lakhs']:.2f} | ₹{row['final_value_lakhs']:.2f} | **+{row['escalation_percentage']:.1f}%** | {row['total_delay_days']} |\n"

    with open(REPORTS_DIR / "CONTRACT_ESCALATION_AUDIT.md", "w", encoding="utf-8") as f:
        f.write(esc_md)

    print(f"SUCCESS: Generated reports saved to {REPORTS_DIR}")

if __name__ == "__main__":
    save_all_reports_to_disk()

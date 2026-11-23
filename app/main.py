"""
BIDWATCH: Public Procurement Intelligence & Investigative Analytics Platform
Interactive Streamlit Analytics and Audit Dashboard.
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
from datetime import datetime, date
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import text

from src.ingestion.database import get_engine, query_df
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

# Page configuration
st.set_page_config(
    page_title="BIDWATCH | Procurement Intelligence Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for executive look and feel
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border-radius: 8px;
        padding: 16px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .lead-high {
        background-color: #FEF2F2;
        border-left: 5px solid #EF4444;
        padding: 12px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    .lead-elevated {
        background-color: #FFFBEB;
        border-left: 5px solid #F59E0B;
        padding: 12px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    .lead-medium {
        background-color: #EFF6FF;
        border-left: 5px solid #3B82F6;
        padding: 12px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# Database / Metadata Fetch Helpers
# -------------------------------------------------------------
@st.cache_data(ttl=600)
def load_filter_options():
    engine = get_engine()
    with engine.connect() as conn:
        depts = [row[0] for row in conn.execute(text("SELECT DISTINCT department_name FROM buyers ORDER BY department_name")).fetchall()]
        cats = [row[0] for row in conn.execute(text("SELECT DISTINCT category FROM tenders ORDER BY category")).fetchall()]
        regions = [row[0] for row in conn.execute(text("SELECT DISTINCT state_region FROM buyers ORDER BY state_region")).fetchall()]
        min_date, max_date = conn.execute(text("SELECT MIN(publication_date), MAX(publication_date) FROM tenders")).fetchone()
    return depts, cats, regions, min_date, max_date

depts_list, cats_list, regions_list, min_pub_date, max_pub_date = load_filter_options()

# -------------------------------------------------------------
# SIDEBAR FILTERS
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🛡️ **BIDWATCH**")
    st.caption("Public Procurement Intelligence & Investigative Analytics Platform")
    st.markdown("---")
    
    st.subheader("Interactive Filters")
    selected_dept = st.selectbox("Department / Buyer", ["All"] + depts_list)
    selected_cat = st.selectbox("Tender Category", ["All"] + cats_list)
    selected_region = st.selectbox("State / Region", ["All"] + regions_list)
    
    # Date Range
    try:
        start_d = datetime.strptime(min_pub_date, "%Y-%m-%d").date() if min_pub_date else date(2022, 1, 1)
        end_d = datetime.strptime(max_pub_date, "%Y-%m-%d").date() if max_pub_date else date(2025, 12, 31)
    except Exception:
        start_d, end_d = date(2022, 1, 1), date(2025, 12, 31)
        
    date_range = st.date_input("Publication Date Range", (start_d, end_d), min_value=start_d, max_value=end_d)
    
    start_filter = date_range[0].strftime("%Y-%m-%d") if isinstance(date_range, tuple) and len(date_range) > 0 else None
    end_filter = date_range[1].strftime("%Y-%m-%d") if isinstance(date_range, tuple) and len(date_range) > 1 else None

    st.markdown("---")
    st.info("💡 **Methodology Notice:** All flagged anomalies highlight patterns requiring human audit and do not constitute accusations of wrongdoing.")

# -------------------------------------------------------------
# NAVIGATION TABS
# -------------------------------------------------------------
tab_exec, tab_dept, tab_hhi, tab_rel, tab_esc, tab_canc, tab_geo, tab_leads, tab_drill, tab_exports = st.tabs([
    "📊 Executive Overview",
    "🏛️ Department Spend",
    "🏢 Supplier Concentration",
    "🔄 Buyer-Supplier Pairs",
    "📈 Value Escalations",
    "❌ Cancellations & Timelines",
    "🗺️ Geographic Flow",
    "🔍 Investigative Leads",
    "🎯 Record Drill-Down",
    "📥 Data Exports"
])

# =============================================================
# TAB 1: EXECUTIVE OVERVIEW
# =============================================================
with tab_exec:
    st.markdown('<div class="main-header">Procurement Executive Summary</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Macro indicators across public procurement tenders, awards, and post-award escalations.</div>', unsafe_allow_html=True)
    
    kpis = get_executive_kpis(
        dept_filter=selected_dept,
        category_filter=selected_cat,
        state_filter=selected_region,
        start_date=start_filter,
        end_date=end_filter
    )
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Tenders", f"{kpis.get('total_tenders', 0):,}")
    with col2:
        st.metric("Awarded Contracts", f"{kpis.get('total_awarded', 0):,}")
    with col3:
        st.metric("Settled Value", f"₹{kpis.get('total_settled_value_cr', 0.0):,.1f} Cr")
    with col4:
        st.metric("Post-Award Escalation", f"+₹{kpis.get('total_escalation_cr', 0.0):,.1f} Cr", 
                  delta=f"{round(kpis.get('total_escalation_cr', 0.0) / max(1.0, kpis.get('total_initial_value_cr', 1.0)) * 100, 1)}%",
                  delta_color="inverse")
    with col5:
        st.metric("Cancellation Rate", f"{kpis.get('cancellation_rate_pct', 0.0)}%",
                  delta="Normal Baseline: 11%", delta_color="off")
        
    st.markdown("---")
    
    # Visualizations row 1
    c1, c2 = st.columns([6, 4])
    
    with c1:
        st.subheader("Monthly Procurement Expenditure & Contract Trend")
        df_trends = get_temporal_trends()
        if not df_trends.empty:
            fig_trends = go.Figure()
            fig_trends.add_trace(go.Bar(
                x=df_trends["year_month"],
                y=df_trends["monthly_spend_cr"],
                name="Spend (₹ Cr)",
                marker_color="#2563EB"
            ))
            fig_trends.add_trace(go.Scatter(
                x=df_trends["year_month"],
                y=df_trends["contracts_awarded"],
                name="Contracts Count",
                yaxis="y2",
                line=dict(color="#DC2626", width=2.5)
            ))
            fig_trends.update_layout(
                yaxis=dict(title="Settled Spend (₹ Crores)"),
                yaxis2=dict(title="Contracts Count", overlaying="y", side="right"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=20, r=20, t=30, b=20),
                height=350
            )
            st.plotly_chart(fig_trends, use_container_width=True)
            
    with c2:
        st.subheader("Procurement Spend by Category")
        engine = get_engine()
        with engine.connect() as conn:
            cat_df = pd.read_sql_query(text("""
                SELECT t.category, SUM(a.final_settled_value_inr) / 10000000.0 AS spend_cr
                FROM tenders t
                JOIN awards a ON t.tender_id = a.tender_id
                GROUP BY t.category
                ORDER BY spend_cr DESC
            """), conn)
            
        fig_cat = px.pie(
            cat_df,
            names="category",
            values="spend_cr",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig_cat.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=350)
        st.plotly_chart(fig_cat, use_container_width=True)

# =============================================================
# TAB 2: DEPARTMENT PROCUREMENT
# =============================================================
with tab_dept:
    st.markdown('<div class="main-header">Department Spending & Budget Utilization</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Evaluation of procuring entities by contract expenditure and statutory budget allocation.</div>', unsafe_allow_html=True)
    
    df_dept = get_department_spending(dept_filter=selected_dept, state_filter=selected_region)
    
    dcol1, dcol2 = st.columns([7, 3])
    with dcol1:
        fig_dept = px.bar(
            df_dept.head(15),
            x="total_procurement_cr",
            y="department_name",
            orientation="h",
            color="budget_utilization_pct",
            color_continuous_scale="Viridis",
            labels={"total_procurement_cr": "Total Spend (₹ Cr)", "department_name": "Department", "budget_utilization_pct": "Budget Utilization %"},
            title="Top Procuring Departments (₹ Crores)"
        )
        fig_dept.update_layout(yaxis=dict(autorange="reversed"), height=500, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_dept, use_container_width=True)
        
    with dcol2:
        st.subheader("Department Highlights")
        top_dept = df_dept.iloc[0] if not df_dept.empty else None
        if top_dept is not None:
            st.info(f"**Top Procuring Body:** {top_dept['department_name']}\n\n"
                    f"• Ministry: {top_dept['ministry']}\n\n"
                    f"• Total Procurement: ₹{top_dept['total_procurement_cr']} Cr\n\n"
                    f"• Contracts Awarded: {top_dept['tenders_awarded']}\n\n"
                    f"• Avg Contract Size: ₹{top_dept['avg_contract_lakhs']} Lakhs\n\n"
                    f"• Budget Utilization: {top_dept['budget_utilization_pct']}%")
            
    st.dataframe(
        df_dept[["spending_rank", "department_name", "ministry", "state_region", "total_procurement_cr", "budget_allocation_cr", "budget_utilization_pct", "tenders_awarded", "tenders_cancelled"]],
        use_container_width=True,
        hide_index=True
    )

# =============================================================
# TAB 3: SUPPLIER CONCENTRATION & HHI
# =============================================================
with tab_hhi:
    st.markdown('<div class="main-header">Supplier Market Share & Concentration (HHI)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Antitrust Herfindahl-Hirschman Index (HHI) analysis to identify monopolistic and oligopolistic vendor capture.</div>', unsafe_allow_html=True)
    
    h1, h2 = st.columns([5, 5])
    
    with h1:
        st.subheader("Department Concentration Index (HHI)")
        df_hhi = get_supplier_concentration_hhi()
        fig_hhi = px.bar(
            df_hhi.head(12),
            x="hhi_score",
            y="department_name",
            orientation="h",
            color="hhi_score",
            color_continuous_scale=["#10B981", "#F59E0B", "#EF4444"],
            labels={"hhi_score": "HHI Score", "department_name": "Department"},
            title="Department HHI Concentration Scores"
        )
        fig_hhi.add_vline(x=1500, line_dash="dash", line_color="orange", annotation_text="Moderate (1500)")
        fig_hhi.add_vline(x=2500, line_dash="dash", line_color="red", annotation_text="High Oligopoly (2500)")
        fig_hhi.update_layout(yaxis=dict(autorange="reversed"), height=420)
        st.plotly_chart(fig_hhi, use_container_width=True)
        
    with h2:
        st.subheader("Top Suppliers Cumulative Market Share")
        df_supp = get_supplier_market_share(top_n=20)
        fig_pareto = go.Figure()
        fig_pareto.add_trace(go.Bar(
            x=df_supp["canonical_name"].apply(lambda x: x[:25]),
            y=df_supp["total_won_cr"],
            name="Won Spend (₹ Cr)",
            marker_color="#3B82F6"
        ))
        fig_pareto.add_trace(go.Scatter(
            x=df_supp["canonical_name"].apply(lambda x: x[:25]),
            y=df_supp["cumulative_market_share_pct"],
            name="Cumulative Share %",
            yaxis="y2",
            line=dict(color="#10B981", width=2.5)
        ))
        fig_pareto.update_layout(
            yaxis=dict(title="Awarded Value (₹ Cr)"),
            yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 105]),
            xaxis=dict(tickangle=-45),
            margin=dict(l=10, r=10, t=30, b=80),
            height=420,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_pareto, use_container_width=True)
        
    st.dataframe(
        df_supp[["market_rank", "canonical_name", "registration_type", "state_region", "is_msme_label", "contracts_won_count", "distinct_buyers_served", "total_won_cr", "market_share_pct", "cumulative_market_share_pct"]],
        use_container_width=True,
        hide_index=True
    )

# =============================================================
# TAB 4: BUYER-SUPPLIER RELATIONSHIPS
# =============================================================
with tab_rel:
    st.markdown('<div class="main-header">Buyer-Supplier Repeat Wins & Entrenchment</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Audit repeated awards won by the same contractor from the same procuring entity.</div>', unsafe_allow_html=True)
    
    df_repeat = get_repeat_supplier_awards(min_wins=3)
    
    r1, r2 = st.columns([6, 4])
    with r1:
        fig_repeat = px.scatter(
            df_repeat,
            x="awards_won_from_buyer",
            y="buyer_spend_share_pct",
            size="spend_captured_cr",
            color="concentration_flag",
            hover_name="supplier_name",
            hover_data=["department_name", "spend_captured_cr"],
            color_discrete_map={
                "CRITICAL_CONCENTRATION": "#EF4444",
                "ELEVATED_CONCENTRATION": "#F59E0B",
                "STANDARD": "#10B981"
            },
            labels={
                "awards_won_from_buyer": "Number of Awards Won",
                "buyer_spend_share_pct": "% of Department's Total Spend Captured",
                "spend_captured_cr": "Captured Spend (₹ Cr)"
            },
            title="Repeat Awards vs Share of Department Spend"
        )
        fig_repeat.update_layout(height=450)
        st.plotly_chart(fig_repeat, use_container_width=True)
        
    with r2:
        st.markdown("### ⚠️ Key Relationship Patterns")
        critical_pairs = df_repeat[df_repeat["concentration_flag"] == "CRITICAL_CONCENTRATION"]
        st.write(f"Identified **{len(critical_pairs)}** critical buyer-supplier pairings where a single contractor captures >= 50% of the department's budget.")
        for _, cp in critical_pairs.head(4).iterrows():
            st.error(f"**{cp['supplier_name']}** captures **{cp['buyer_spend_share_pct']}%** of **{cp['department_name']}** ({cp['awards_won_from_buyer']} awards, ₹{cp['spend_captured_cr']} Cr)")
            
    st.dataframe(
        df_repeat[["department_name", "supplier_name", "awards_won_from_buyer", "total_buyer_awards", "award_win_share_pct", "spend_captured_cr", "buyer_spend_share_pct", "concentration_flag"]],
        use_container_width=True,
        hide_index=True
    )

# =============================================================
# TAB 5: VALUE ESCALATIONS & AMENDMENTS
# =============================================================
with tab_esc:
    st.markdown('<div class="main-header">Contract Amendments & Value Escalations</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Post-award cost growth and timeline delays to identify potential predatory low-ball bidding.</div>', unsafe_allow_html=True)
    
    df_esc = get_amendment_escalations()
    
    e1, e2 = st.columns([6, 4])
    with e1:
        fig_esc_hist = px.histogram(
            df_esc,
            x="escalation_percentage",
            color="escalation_tier",
            nbins=30,
            labels={"escalation_percentage": "Value Escalation (%)", "count": "Contract Count"},
            title="Distribution of Contract Value Escalation (%)",
            color_discrete_map={
                "CRITICAL_COST_OVERRUN (>50%)": "#EF4444",
                "SUBSTANTIAL_COST_OVERRUN (25-50%)": "#F59E0B",
                "MODERATE_ESCALATION (10-25%)": "#3B82F6",
                "NORMAL_VARIATION (<=10%)": "#10B981"
            }
        )
        fig_esc_hist.update_layout(height=400)
        st.plotly_chart(fig_esc_hist, use_container_width=True)
        
    with e2:
        st.subheader("Escalation Tier Breakdown")
        tier_counts = df_esc["escalation_tier"].value_counts().reset_index()
        tier_counts.columns = ["Escalation Tier", "Count"]
        fig_tier_pie = px.pie(tier_counts, names="Escalation Tier", values="Count", hole=0.4)
        fig_tier_pie.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=350)
        st.plotly_chart(fig_tier_pie, use_container_width=True)
        
    st.dataframe(
        df_esc[["escalation_rank", "tender_reference_no", "department_name", "supplier_name", "initial_value_lakhs", "final_value_lakhs", "net_escalation_lakhs", "escalation_percentage", "amendment_count", "total_delay_days", "escalation_tier"]],
        use_container_width=True,
        hide_index=True
    )

# =============================================================
# TAB 6: CANCELLATIONS & TIMELINES
# =============================================================
with tab_canc:
    st.markdown('<div class="main-header">Tender Cancellations & Timeline Hygiene</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Scrutiny of annulment patterns and compressed bidding duration windows.</div>', unsafe_allow_html=True)
    
    df_canc = get_cancellation_rates()
    
    ca1, ca2 = st.columns([6, 4])
    with ca1:
        fig_canc = px.bar(
            df_canc.head(10),
            x="cancellation_rate_pct",
            y="department_name",
            orientation="h",
            color="cancellation_risk_flag",
            labels={"cancellation_rate_pct": "Cancellation Rate (%)", "department_name": "Department"},
            title="Department Cancellation Rates vs Baseline (11%)",
            color_discrete_map={
                "CHRONIC_CANCELLATIONS (High Risk)": "#EF4444",
                "ELEVATED_CANCELLATIONS": "#F59E0B",
                "NORMAL_BASELINE": "#10B981"
            }
        )
        fig_canc.add_vline(x=11.1, line_dash="dash", line_color="gray", annotation_text="Benchmark (11%)")
        fig_canc.update_layout(yaxis=dict(autorange="reversed"), height=400)
        st.plotly_chart(fig_canc, use_container_width=True)
        
    with ca2:
        st.subheader("Cancellation Reasons")
        engine = get_engine()
        with engine.connect() as conn:
            canc_reasons = pd.read_sql_query(text("""
                SELECT reason_category, COUNT(*) AS count_cases
                FROM cancellations
                GROUP BY reason_category
                ORDER BY count_cases DESC
            """), conn)
            
        fig_reasons = px.pie(
            canc_reasons,
            names="reason_category",
            values="count_cases",
            hole=0.4,
            title="Annulment Justification Breakdown"
        )
        fig_reasons.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=350)
        st.plotly_chart(fig_reasons, use_container_width=True)
        
    st.dataframe(
        df_canc[["department_name", "ministry", "total_tenders", "awarded_count", "cancelled_count", "cancellation_rate_pct", "cancelled_value_cr", "cancellation_risk_flag"]],
        use_container_width=True,
        hide_index=True
    )

# =============================================================
# TAB 7: GEOGRAPHIC PROCUREMENT FLOW
# =============================================================
with tab_geo:
    st.markdown('<div class="main-header">Geographic Spending & Interstate Flows</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Cross-state procurement flows between buyer jurisdiction and vendor headquarters.</div>', unsafe_allow_html=True)
    
    df_geo = get_geographic_distribution()
    
    g1, g2 = st.columns([6, 4])
    with g1:
        # Pivot table for heatmap
        pivot_geo = df_geo.pivot_table(index="buyer_state", columns="supplier_state", values="value_cr", aggfunc="sum", fill_value=0)
        fig_geo = px.imshow(
            pivot_geo,
            labels=dict(x="Supplier State", y="Buyer State", color="Spend (₹ Cr)"),
            x=pivot_geo.columns,
            y=pivot_geo.index,
            aspect="auto",
            color_continuous_scale="Blues",
            title="Inter-State Procurement Flow Matrix (₹ Crores)"
        )
        fig_geo.update_layout(height=450)
        st.plotly_chart(fig_geo, use_container_width=True)
        
    with g2:
        st.subheader("Local vs Interstate Distribution")
        flow_summary = df_geo.groupby("flow_type")["value_cr"].sum().reset_index()
        fig_flow_pie = px.pie(
            flow_summary,
            names="flow_type",
            values="value_cr",
            hole=0.4,
            color="flow_type",
            color_discrete_map={"DOMESTIC / INTRA-STATE": "#2563EB", "INTER-STATE OUTFLOW": "#F59E0B"}
        )
        fig_flow_pie.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_flow_pie, use_container_width=True)
        
    st.dataframe(
        df_geo[["buyer_state", "supplier_state", "flow_type", "total_contracts", "value_cr", "pct_of_buyer_state_spend"]],
        use_container_width=True,
        hide_index=True
    )

# =============================================================
# TAB 8: INVESTIGATIVE LEADS DOSSIER
# =============================================================
with tab_leads:
    st.markdown('<div class="main-header">Investigative Leads & Anomaly Dossiers</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Explainable indicators flagged by statistical baselines and procurement compliance rules.</div>', unsafe_allow_html=True)
    
    engine = get_engine()
    with engine.connect() as conn:
        df_all_leads = pd.read_sql_query(text("SELECT * FROM investigative_leads ORDER BY severity ASC, lead_id ASC"), conn)
        
    lcol1, lcol2, lcol3 = st.columns(3)
    with lcol1:
        sel_ind = st.selectbox("Indicator Type", ["All"] + sorted(df_all_leads["indicator_code"].unique().tolist()))
    with lcol2:
        sel_sev = st.selectbox("Severity", ["All", "HIGH", "ELEVATED", "MEDIUM"])
    with lcol3:
        sel_ent = st.selectbox("Entity Type", ["All"] + sorted(df_all_leads["entity_type"].unique().tolist()))
        
    filtered_leads = df_all_leads.copy()
    if sel_ind != "All":
        filtered_leads = filtered_leads[filtered_leads["indicator_code"] == sel_ind]
    if sel_sev != "All":
        filtered_leads = filtered_leads[filtered_leads["severity"] == sel_sev]
    if sel_ent != "All":
        filtered_leads = filtered_leads[filtered_leads["entity_type"] == sel_ent]
        
    st.write(f"Showing **{len(filtered_leads)}** investigative leads matching active filters.")
    
    # Display leads as expandable audit dossiers
    for idx, row in filtered_leads.head(30).iterrows():
        sev_class = "lead-high" if row["severity"] == "HIGH" else ("lead-elevated" if row["severity"] == "ELEVATED" else "lead-medium")
        badge = "🔴 HIGH" if row["severity"] == "HIGH" else ("🟠 ELEVATED" if row["severity"] == "ELEVATED" else "🔵 MEDIUM")
        
        with st.expander(f"{badge} | [{row['indicator_code']}] {row['entity_id']} - {row['indicator_name']}", expanded=(idx < 2)):
            st.markdown(f"""
            <div class="{sev_class}">
                <strong>Observed Finding:</strong><br>{row['observed_finding']}
            </div>
            """, unsafe_allow_html=True)
            
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                st.markdown("**1. Supporting Data Fields:**")
                st.code(json.dumps(json.loads(row['supporting_fields']), indent=2), language="json")
                
                st.markdown("**2. Why It Was Flagged (Rationale):**")
                st.info(row['rationale'])
                
            with c_f2:
                st.markdown("**3. Comparison With Baseline:**")
                st.warning(row['baseline_comparison'])
                
                st.markdown("**4. Human Verification Checklist:**")
                st.markdown(row['human_verification_checklist'])

# =============================================================
# TAB 9: RECORD DRILL-DOWN / RECORD INSPECTOR
# =============================================================
with tab_drill:
    st.markdown('<div class="main-header">Procurement Record Deep-Dive Inspector</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Drill down into individual tender notices, bidding sheets, awards, and amendment histories.</div>', unsafe_allow_html=True)
    
    engine = get_engine()
    with engine.connect() as conn:
        all_refs = [r[0] for r in conn.execute(text("SELECT tender_reference_no FROM tenders ORDER BY tender_reference_no")).fetchall()]
        
    selected_ref = st.selectbox("Search / Select Tender Reference Number", all_refs)
    
    if selected_ref:
        with engine.connect() as conn:
            tender_info = conn.execute(text("""
                SELECT t.*, b.department_name, b.ministry, b.state_region AS buyer_state
                FROM tenders t
                JOIN buyers b ON t.buyer_id = b.buyer_id
                WHERE t.tender_reference_no = :ref
            """), {"ref": selected_ref}).mappings().first()
            
            bids_df = pd.read_sql_query(text("""
                SELECT b.bid_id, s.canonical_name AS bidder_name, b.bid_amount_inr, 
                       b.technical_qualified, b.is_winning_bid, b.submission_timestamp
                FROM bids b
                JOIN suppliers s ON b.supplier_id = s.supplier_id
                JOIN tenders t ON b.tender_id = t.tender_id
                WHERE t.tender_reference_no = :ref
                ORDER BY b.bid_amount_inr ASC
            """), conn, params={"ref": selected_ref})
            
            award_info = conn.execute(text("""
                SELECT a.*, s.canonical_name AS winning_supplier_name
                FROM awards a
                JOIN suppliers s ON a.supplier_id = s.supplier_id
                JOIN tenders t ON a.tender_id = t.tender_id
                WHERE t.tender_reference_no = :ref
            """), {"ref": selected_ref}).mappings().first()
            
            amendments_df = pd.read_sql_query(text("""
                SELECT amd.amendment_sequence, amd.amendment_date, amd.amendment_type, 
                       amd.value_change_inr, amd.time_extension_days, amd.justification_code, amd.description
                FROM amendments amd
                JOIN awards a ON amd.award_id = a.award_id
                JOIN tenders t ON a.tender_id = t.tender_id
                WHERE t.tender_reference_no = :ref
                ORDER BY amd.amendment_sequence ASC
            """), conn, params={"ref": selected_ref})
            
        st.markdown(f"### 📋 Tender Profile: `{tender_info['tender_reference_no']}`")
        tc1, tc2, tc3, tc4 = st.columns(4)
        with tc1:
            st.write(f"**Department:** {tender_info['department_name']}")
            st.write(f"**Ministry:** {tender_info['ministry']}")
        with tc2:
            st.write(f"**Category:** {tender_info['category']}")
            st.write(f"**Method:** {tender_info['procurement_method']}")
        with tc3:
            st.write(f"**Estimated Value:** ₹{tender_info['estimated_value_inr']/100000:.2f} Lakhs")
            st.write(f"**Bidding Window:** {tender_info['bidding_duration_days']} days")
        with tc4:
            st.write(f"**Published:** {tender_info['publication_date']}")
            st.write(f"**Status:** `{tender_info['status']}`")
            
        st.markdown("#### 1. Participating Bids & Financial Evaluation")
        if not bids_df.empty:
            bids_df["bid_amount_lakhs"] = bids_df["bid_amount_inr"] / 100000.0
            st.dataframe(bids_df[["bidder_name", "bid_amount_lakhs", "technical_qualified", "is_winning_bid", "submission_timestamp"]], use_container_width=True, hide_index=True)
        else:
            st.info("No bid records found for this tender (e.g. cancelled before receipt).")
            
        if award_info:
            st.markdown("#### 2. Award Information")
            aw1, aw2, aw3 = st.columns(3)
            with aw1:
                st.write(f"**Winning Supplier:** {award_info['winning_supplier_name']}")
                st.write(f"**Award Date:** {award_info['award_date']}")
            with aw2:
                st.write(f"**Initial Contract Value:** ₹{award_info['initial_contract_value_inr']/100000:.2f} Lakhs")
                st.write(f"**Final Settled Value:** ₹{award_info['final_settled_value_inr']/100000:.2f} Lakhs")
            with aw3:
                net_change = award_info['final_settled_value_inr'] - award_info['initial_contract_value_inr']
                pct_change = (net_change * 100.0 / award_info['initial_contract_value_inr']) if award_info['initial_contract_value_inr'] > 0 else 0
                st.write(f"**Net Escalation:** ₹{net_change/100000:.2f} Lakhs (+{pct_change:.1f}%)")
                st.write(f"**Contract Status:** {award_info['contract_status']}")
                
        if not amendments_df.empty:
            st.markdown("#### 3. Post-Award Corrigenda & Amendments")
            amendments_df["value_change_lakhs"] = amendments_df["value_change_inr"] / 100000.0
            st.dataframe(amendments_df[["amendment_sequence", "amendment_date", "amendment_type", "value_change_lakhs", "time_extension_days", "justification_code", "description"]], use_container_width=True, hide_index=True)

# =============================================================
# TAB 10: DATA EXPORTS & REPORTS
# =============================================================
with tab_exports:
    st.markdown('<div class="main-header">Data Exports & Power BI Integration</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Download clean, relational datasets in CSV format for offline reporting and Power BI dashboards.</div>', unsafe_allow_html=True)
    
    st.write("All tables are pre-processed and synchronized with `data/processed/powerbi_export/`.")
    
    ex_col1, ex_col2 = st.columns(2)
    with ex_col1:
        st.subheader("Analytical Summary Exports")
        
        # 1. Leads
        csv_leads = df_all_leads.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Investigative Leads (CSV)", csv_leads, "bidwatch_investigative_leads.csv", "text/csv")
        
        # 2. HHI Department Index
        csv_hhi = get_supplier_concentration_hhi().to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Supplier Concentration HHI (CSV)", csv_hhi, "bidwatch_hhi_concentration.csv", "text/csv")
        
        # 3. Repeat Awards
        csv_repeat = get_repeat_supplier_awards(min_wins=1).to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Repeat Awards Summary (CSV)", csv_repeat, "bidwatch_repeat_awards.csv", "text/csv")
        
    with ex_col2:
        st.subheader("Relational Database Tables")
        engine = get_engine()
        with engine.connect() as conn:
            tenders_csv = pd.read_sql_query(text("SELECT * FROM tenders"), conn).to_csv(index=False).encode('utf-8')
            awards_csv = pd.read_sql_query(text("SELECT * FROM awards"), conn).to_csv(index=False).encode('utf-8')
            amendments_csv = pd.read_sql_query(text("SELECT * FROM amendments"), conn).to_csv(index=False).encode('utf-8')
            
        st.download_button("📥 Download Clean Tenders Table (CSV)", tenders_csv, "tenders.csv", "text/csv")
        st.download_button("📥 Download Clean Awards Table (CSV)", awards_csv, "awards.csv", "text/csv")
        st.download_button("📥 Download Clean Amendments Table (CSV)", amendments_csv, "amendments.csv", "text/csv")
        
    st.markdown("---")
    st.markdown("### 📊 Power BI Connection Instructions")
    st.markdown("""
    To connect Power BI Desktop to BIDWATCH:
    1. **Method A (Direct SQLite ODBC Connection):** Open Power BI -> Get Data -> ODBC -> select SQLite3 DSN or direct connection string pointing to `data/processed/bidwatch.db`.
    2. **Method B (CSV Folder Ingestion):** Open Power BI -> Get Data -> Folder -> select the `data/processed/powerbi_export/` directory. All 8 normalized tables will load with predefined foreign keys.
    3. Refer to [`docs/POWER_BI_GUIDE.md`](file:///c:/Users/parvk/OneDrive/Desktop/bid/docs/POWER_BI_GUIDE.md) for full Star-Schema data model setup, DAX measures, and dashboard layouts.
    """)

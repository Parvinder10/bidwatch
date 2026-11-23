# BIDWATCH: Analytical Methodology & Anomaly Indicator Framework

## 1. Principles of Explainable Procurement Analytics
BIDWATCH rejects uninterpretable "black-box" anomaly scores. In public procurement audits, actionable oversight requires **substantive explainability**:
- An auditor cannot subpoena files or initiate a vigilance inquiry based solely on an unexplained decimal score.
- Every indicator in BIDWATCH is grounded in **statutory procurement rules** (GFR 2017, CVC Manual 2021) and **established antitrust economic metrics** (e.g., DOJ Herfindahl-Hirschman Index).

---

## 2. Quantitative Indicators & Baseline Specifications

| Indicator Code | Analytical Concept | Statistical Formula / Threshold | Reference Empirical Baseline | Statutory / Legal Context |
| :--- | :--- | :--- | :--- | :--- |
| **`FLAG_HHI_CONCENTRATION`** | Departmental Supplier Monopoly / Oligopoly | $HHI = \sum_{i=1}^n s_i^2 > 2,500$ (where $s_i$ is % share of department spend) | Competitive public markets maintain $HHI < 1,500$. | US DOJ / Antitrust & Competition Commission of India (CCI) standards. |
| **`FLAG_REPEAT_WINNER`** | Supplier-Buyer Entrenchment | Supplier wins $\ge 4$ awards AND captures $\ge 35\%$ of department's awards or spend. | Standard distributed supplier participation averages $< 15\%$ share. | CVC Vigilance Manual: Incumbency bias & subjective technical disqualification of rivals. |
| **`FLAG_VALUE_ESCALATION`** | Post-Award Contract Value Creep | Net Escalation $> 30\%$ via amendments, OR total escalation $> ₹1\text{ Cr}$. | Routine contract variation orders baseline is $\le 10\% - 15\%$. | GFR 2017 Rule 173 (iv) & CVC guidelines on predatory low-ball pricing. |
| **`FLAG_SHORT_BID_WINDOW`** | Compressed Bidding Duration | Tender notice duration $\le 6$ calendar days for tenders $\ge ₹50\text{ Lakhs}$. | Statutory National Competitive Bidding baseline requires $21$ to $30$ days ($14$ days expedited). | Rule 161 (iv) of GFR 2017 & CPPP Guidelines on fair notice. |
| **`FLAG_SINGLE_BIDDER`** | Single-Bidder Open Tender Award | Open competitive tender completed with exactly $1$ bidder and awarded without retender. | Open competitive tenders average $3.4$ participating bids across categories. | CVC Office Order No. 4/3/07 on single-offer tenders in open bidding. |
| **`FLAG_HIGH_CANCELLATION`** | Chronic Departmental Annulments | Department cancellation rate $\ge 18\%$ across a minimum sample of $15$ tenders. | Benchmark platform cancellation rate averages $11.1\%$. | Public Procurement Manual on defective estimation & specification tailoring. |

---

## 3. The 5-Point Mandatory Evidentiary Package
Whenever a record crosses an indicator threshold, BIDWATCH constructs an immutable 5-point evidence structure:
1. **Observed Finding**: Clear factual description of the observed data point.
2. **Supporting Data Fields**: Exact JSON dictionary of raw and aggregated attributes from database tables.
3. **Rationale**: Objective explanation of the procurement governance or antitrust risk associated with this pattern.
4. **Baseline Comparison**: Specific numerical deviation against normal peer baselines or statutory limits.
5. **Human Verification Checklist**: Concrete procedural action steps for human auditors (e.g., examining pre-bid conference minutes, tender committee conflict-of-interest declarations, or variation order approvals).

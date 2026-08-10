# Life KPI & Founder Growth System — Feature Specification
**Module Owner:** Agent 9 (Founder Growth, Evidence, and Content Layer)  
**Status:** Approved & Implemented  
**Reference Docs:** [PRD/TRD](../../Tajs_Second_Brain_PRD_TRD.md), [Database Schema](../../database_schema.md), [API Contracts](../../api_contracts.md)

---

## 1. Executive Summary & Purpose
The Life KPI System tracks Taj’s quantitative and qualitative progress as a founder, operator, network builder, and continuous learner. Designed to eliminate vanity metrics and illusory trends, the system ensures that every metric measured is verifiable, historical check-ins remain immutable, and progress evaluations reflect actual performance.

---

## 2. KPI Categories & Customization
The framework organizes growth around four approved foundational categories (while supporting custom founder-defined metrics without hardcoded constraints):
1. **Founder KPIs:** Measures venture execution metrics (e.g., Projects Completed, Validated Users Acquired, Active Partnerships, Revenue Milestones).
2. **Network KPIs:** Measures relationship deepening (e.g., Meaningful CRM Connections, Active Mentor Engagements, Investor Dialogues).
3. **Learning KPIs:** Measures knowledge intake and capability building (e.g., Books Synthesized, Specialized Courses Completed, Technical Skills Mastered).
4. **Venture KPIs:** Venture-specific operational performance goals linked directly to active projects or ventures.

---

## 3. Historical Integrity & Non-Destructive Corrections
- **Immutable Check-ins:** Periodic check-ins are recorded as separate time-series entities in `public.kpi_entries` (with `kpi_id`, `recording_date`, `recorded_value`, and supporting evidence).
- **Target Changes:** Editing a KPI definition's target value, unit of measurement, or assessment period **never** rewrites historical check-in entries.
- **Unit Alterations:** If a user changes a KPI's unit (e.g., changing "monthly recurring users" to "annual active accounts"), the system flags a methodological break in the historical trend analysis to prevent invalid comparison.
- **Auditability:** Correcting an erroneous entry preserves audit logs in `public.audit_logs` rather than silently overwriting past values.

---

## 4. Progress & Trend Calculation Rules
### 4.1 Deterministic Progress Formulas
Progress calculation depends strictly on the KPI's defined directionality:
- **Higher Is Better (e.g., Revenue, Users, Connections):**  
  `progress_percentage = min(100, (current_value / target_value) * 100)` (when target > 0). Actual values above target are retained in full (e.g., 140% achievement displayed alongside bounded visualizations).
- **Lower Is Better (e.g., Churn Rate, Execution Bug Count, Incident Burn Rate):**  
  `progress_percentage = target_value == 0 ? (current_value == 0 ? 100 : 0) : max(0, min(100, (target_value / current_value) * 100))` or custom approved inverse formula where drop below target indicates success.
- **Milestone / Observational:** Tracks boolean completion or qualitative state without forced percentage scaling.
- **Missing Data:** Missing time-series check-ins are **never** treated as zeros; they are visibly flagged as `Missing Data` or `Insufficient Points`.

### 4.2 Deterministic Trend Engine
Rather than relying on AI guesswork, trends are calculated via deterministic windowed math over consecutive check-in periods:
- **Increasing:** Current period average > previous period average by $\ge 5\%$.
- **Decreasing:** Current period average < previous period average by $\ge 5\%$.
- **Stable:** Variance within $\pm 5\%$.
- **Insufficient Data:** Fewer than 2 historical entries exist in the selected timeframe.

---

## 5. UI & Dashboard Integration
- **Dashboard Widget:** Lightweight integration with Agent 5’s founder dashboard showing featured KPI value badges, deterministic trend arrows, and last-updated timestamps without loading heavy historical arrays.
- **Accessible Visualization:** Recharts-driven time-series line charts and period comparison bar charts must always be accompanied by high-contrast accessible text equivalents and table views.

# Structured Investor Briefing & Traction Update Prompt
**Prompt Version:** 1.0.0  
**Target Model:** Gemini 1.5 Pro (`gemini-1.5-pro`)  
**Module:** AI Content Engine (`/api/v1/content/generate`)

---

## 1. Purpose
Generate formal, highly disciplined investor updates and advisor briefings covering Executive Summary, Product Deliverables, User Metrics, Strategic Partnerships, Financial Revenue/Burn, Challenges, and Key Strategic Asks.

---

## 2. Input Schema (JSON)
```json
{
  "content_type": "investor_update",
  "venture_name": "Justor AI",
  "period_label": "July 2026 Monthly Update",
  "source_records": [
    { "id": "UUID", "type": "kpi_entry | achievement | decision | interaction", "metric": "string", "value": "numeric", "date": "YYYY-MM-DD" }
  ]
}
```

---

## 3. Strict Financial & Traction Guardrails (Zero Tolerance for Hallucinations)
1. **NO INVENTED TRACTION OR METRICS:** Under NO circumstances may the model estimate, extrapolate, or hallucinate active users, ARR, MRR, churn rates, engagement coefficients, or cash runway.
2. **OMISSION OVER FABRICATION:** If source records contain zero financial or quantitative user metrics, explicitly substitute the appropriate section with:  
   `[Section Omitted: No quantified KPI check-in records selected for this reporting period]`.
3. **NO CONVERTING QUALITATIVE TO QUANTITATIVE:** Do not interpret a mentor's positive remark ("this app feels hugely popular") as numerical evidence of widespread user adoption.

---

## 4. Required Output Schema (JSON)
```json
{
  "title": "Justor AI — July 2026 Investor Update & Progress Report",
  "body": "### Executive Summary\nFocused July on core infrastructure and automated agent workflows...\n\n### Product & Execution Progress\n- Successfully deployed Retro-Futuristic Terminal architecture...\n\n### Traction & KPI Metrics\n- Meaningful Founder CRM Connections: 24 (+15% MoM, verified via KPI #88)\n- [Revenue Section Omitted: Pre-revenue research & architectural phase]\n\n### Key Asks\n- Seeking warm introductions to senior AI engineers specialized in custom MCP integrations.",
  "unsupported_metric_warnings_emitted": 0,
  "citations": [
    { "source_id": "UUID", "metric_validated": "24 meaningful CRM connections logged in KPI entries" }
  ]
}
```

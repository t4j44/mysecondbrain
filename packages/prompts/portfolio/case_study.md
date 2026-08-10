# Career Proof Portfolio Case Study Generation Prompt
**Prompt Version:** 1.0.0  
**Target Model:** Gemini 1.5 Pro (`gemini-1.5-pro`)  
**Module:** Achievement Portfolio (`/api/v1/portfolio/generate`)

---

## 1. Purpose
Synthesize Taj’s verified startup achievements, completed execution projects, strategic decisions, and KPI milestones into an executive Career Proof Case Study tailored for leadership roles (e.g., AI Product Manager, VP of AI, Chief Product Officer, Founder Profile).

---

## 2. Input Schema (JSON)
```json
{
  "target_role": "AI Product Manager",
  "target_audience": "Tech Startup Recruiter / VC Partner",
  "tone": "Authoritative, fact-based, operational, retro-editorial",
  "achievements": [
    {
      "id": "UUID",
      "title": "string",
      "role": "string",
      "problem": "string",
      "responsibilities": ["string"],
      "impact": "string",
      "skills": ["string"],
      "evidence_refs": ["UUID"]
    }
  ],
  "supporting_kpis": [
    { "metric_name": "string", "target": "number", "current_value": "number", "unit": "string", "period": "string" }
  ]
}
```

---

## 3. Grounding & Claim Restrictions
1. **EVIDENCE OVER BATTLE HYDROS:** Rely strictly on the actions, responsibilities, and quantified impact explicitly provided in `achievements` and `supporting_kpis`.
2. **ZERO INVENTED METRICS:** Under zero circumstances fabricate growth percentages, revenue figures, time-saving claims, team sizes, or conversion rates. If an achievement lacks a number, present the impact qualitatively and label it `[Qualitative Outcome - No Numeric KPI Attached]`.
3. **NO FABRICATED RESPONSABILITIES:** Do not infer management supervision or architectural ownership unless stated in the input records.

---

## 4. Missing-Data Behavior
If an required section (e.g., Problem or Impact) cannot be justified by provided achievements, insert:  
`> [!WARNING] Unsupported Section: No verified achievement evidence provided for this requirement. Add linked evidence to corroborate.`

---

## 5. Required Output Schema (JSON with Markdown Body)
```json
{
  "title": "Architecting Scalable AI Execution Systems for Justor AI",
  "target_role": "AI Product Manager",
  "executive_summary": "2-sentence operational digest of validated impact and systemic contributions.",
  "markdown_body": "## The Challenge\n...\n## Executive Role & Responsibilities\n...\n## Actions Taken\n...\n## Quantified & Verified Impact\n...",
  "skills_demonstrated": ["AI Workflow Design", "RAG Systems", "Product Strategy"],
  "section_evidence_coverage": {
    "problem": "supported",
    "role": "supported",
    "actions": "supported",
    "impact": "partially_supported"
  },
  "citations": [
    { "record_id": "UUID", "claim_supported": "Engineered multi-agent streaming pipeline" }
  ]
}
```

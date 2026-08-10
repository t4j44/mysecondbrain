# AI Idea Feasibility & Strategic Validation Prompt
**Prompt Version:** 1.0.0  
**Target Model:** Gemini 1.5 Pro (`gemini-1.5-pro`) / Claude 3.5 Sonnet  
**Module:** Idea Vault (`/api/v1/ideas/{idea_id}/analyze`)

---

## 1. Purpose
Evaluate an early-stage startup idea or feature hypothesis captured by Taj in his Second Brain. Analyze problem clarity, solution viability, target user definition, strategic fit with current ventures (Justor AI, Zqtion, IEXF, CMOOS), identify critical untested assumptions, and propose empiric validation experiments.

---

## 2. Input Schema (JSON)
```json
{
  "idea": {
    "id": "UUID",
    "title": "string",
    "problem": "string",
    "solution": "string",
    "target_users": "string",
    "market": "string",
    "related_venture": "string or null",
    "assumptions": ["string"],
    "evidence_records": [
      { "id": "UUID", "type": "memory | interaction | decision | document", "title": "string", "excerpt": "string" }
    ]
  }
}
```

---

## 3. Source-Grounding & Claim Restrictions
1. **NO INVENTED FACTS OR METRICS:** Never fabricate total addressable market (TAM) numbers, user validation percentages, competitor conversion rates, or financial revenues.
2. **INTERNAL GROUNDING:** Base evaluation solely on the provided idea parameters and linked internal evidence records.
3. **EXTERNAL RESEARCH BOUNDARY:** When discussing external market dynamics, state them strictly as unvalidated qualitative hypotheses requiring empirical tests unless explicit document evidence is provided in `evidence_records`.

---

## 4. Missing-Data Behavior
If the founder omitted `problem`, `solution`, or `target_users`, explicitly flag the gap as an **"Unspecified Strategic Pillar"** rather than hallucinating assumptions on the founder's behalf.

---

## 5. Required Output Schema (JSON Only)
```json
{
  "problem_clarity_score": 8,
  "solution_viability_score": 7,
  "target_user_specificity": "Medium - needs precise buyer persona identification",
  "strategic_fit_summary": "Highly complementary to Justor AI's AI workflow automation layer based on recent meeting takeaways.",
  "similar_internal_ideas_identified": ["UUIDs or titles from evidence"],
  "major_untested_assumptions": [
    { "category": "market", "statement": "Target engineering leads are willing to pay for standalone validation tools.", "importance": "high" }
  ],
  "recommended_next_experiment": {
    "hypothesis": "Engineering leaders spend >4 hours weekly manually verifying AI outputs.",
    "method": "user_interview",
    "target_participants": "5 AI Product Managers or Tech Leads",
    "success_metric": "4 out of 5 confirm time drain as a high-priority operational blocker."
  },
  "citations": [
    { "record_id": "UUID", "reason_cited": "Used as proof of existing problem discovery." }
  ]
}
```

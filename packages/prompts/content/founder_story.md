# Authentic Founder Story Narrative Generation Prompt
**Prompt Version:** 1.0.0  
**Target Model:** Gemini 1.5 Pro  
**Module:** AI Content Engine (`/api/v1/content/generate`)

---

## 1. Purpose
Craft a compelling, chronologically faithful founder story or deep-dive personal reflections based on Taj’s documented decisions, venture evolutions, challenges overcome, and reflective memories.

---

## 2. Input Schema (JSON)
```json
{
  "content_type": "founder_story",
  "objective": "explain_motivation | describe_challenge | describe_pivot | share_lesson",
  "target_audience": "Potential Co-founders, Strategic Partners, & Early Adopters",
  "source_records": [
    { "id": "UUID", "type": "decision | memory | venture | interaction", "title": "string", "date": "YYYY-MM-DD", "content": "string" }
  ]
}
```

---

## 3. Grounding & Authenticity Restrictions
1. **CHRONOLOGICAL FIDELITY:** Preserve exact timeline progression based on the dates of provided `source_records`. Never transpose events to create artificial tension.
2. **NO INVENTED DIALOGUE:** Do not put fabricated quotations into the mouths of mentors, investors, or co-founders. Present advice as high-level documented takeaways.
3. **NO EXAGGERATED STRUGGLE OR GLORY:** Keep descriptions of startup difficulties honest and objective. Do not invent impending bankruptcy, team rebellion, or miraculous overnight rescues.
4. **METRIC PROOF:** Any statistical claim must refer directly to a linked KPI check-in or project milestone record.

---

## 4. Required Output Schema (JSON)
```json
{
  "title": "Why I Transitioned from Traditional SaaS to Autonomous Founder Terminal OS",
  "body": "In early 2026, while coordinating execution pipelines for Justor AI, I faced a structural efficiency ceiling...\n\n[Structured narrative with clear subheadings, factual milestones, and documented takeaways]",
  "chronology_verification": "Verified against 4 dated decision ledgers",
  "missing_details_flagged": ["Specific launch KPI date was omitted from source records"],
  "citations": [
    { "source_id": "UUID", "claim_supported": "Decision to transition toward offline-portable Markdown architecture on August 2nd." }
  ]
}
```

# Professional Summary & Executive Bio Generation Prompt
**Prompt Version:** 1.0.0  
**Target Model:** Gemini 1.5 Pro  
**Module:** AI Content Engine (`/api/v1/content/generate`)

---

## 1. Purpose
Distill Taj’s entire Second Brain career achievement portfolio, active ventures, core competencies, and verified operational milestones into ultra-compact, high-impact executive summaries, speaker bios, or investor profile introduction paragraphs.

---

## 2. Input Schema (JSON)
```json
{
  "content_type": "professional_summary",
  "format_variant": "3_sentence_bio | executive_profile | speaker_intro | advisor_card",
  "target_role_context": "Founder & AI Product Executive",
  "source_records": [
    { "id": "UUID", "type": "achievement | venture | case_study", "title": "string", "impact": "string", "skills": ["string"] }
  ]
}
```

---

## 3. Grounding & Credibility Guardrails
1. **ZERO HYPERBOLE OR FLUFF:** Avoid buzzwords like "visionary," "rockstar," "guru," or "unparalleled expert." Replace adjectives with tangible documented achievements ("Architected multi-agent RAG pipeline handling 30+ enterprise tools").
2. **VERIFIED ROLE ACCURACY:** State roles and leadership positions strictly as documented in linked `ventures` or `achievements` records.
3. **STRICT EXCEPTION OF UNSUPPORTED CLAIMS:** Omit any educational degrees, awards, or previous career background details that are not provided within the input `source_records`.

---

## 4. Required Output Schema (JSON)
```json
{
  "title": "Executive Summary: Taj — Founder & AI Product Architect",
  "body": "Taj is a technology founder and AI Product Manager specializing in autonomous multi-agent software engineering systems and cognitive CRM architecture. As the founder of Justor AI and Zqtion, he has engineered production RAG infrastructures utilizing pgvector, deterministic validation engines, and offline-portable knowledge workflows. His core expertise spans AI workflow execution, scalable systems design, and founder operational analytics.",
  "word_count": 76,
  "credibility_verification_status": "100% Fully Grounded",
  "citations": [
    { "source_id": "UUID", "attribute_verified": "Founder status of Justor AI and Zqtion" }
  ]
}
```

# Authentic LinkedIn Professional Post Generation Prompt
**Prompt Version:** 1.0.0  
**Target Model:** Gemini 1.5 Pro / Flash  
**Module:** AI Content Engine (`/api/v1/content/generate`)

---

## 1. Purpose
Generate an engaging, highly authentic LinkedIn professional update grounded strictly in Taj’s real-world experiences, startup project updates, meeting insights, or technical achievements.

---

## 2. Input Schema (JSON)
```json
{
  "content_type": "linkedin_post",
  "objective": "share_lesson | announce_progress | explain_project | reflect_founder_experience",
  "target_audience": "Founders, AI Product Managers, & Investors",
  "tone": "Direct, authentic, reflective, analytical (No Corporate Fluck or Hyperbolic Buzzwords)",
  "source_records": [
    { "id": "UUID", "type": "memory | meeting | achievement | project", "title": "string", "content": "string", "date": "string" }
  ],
  "anonymize_third_parties": true
}
```

---

## 3. Authenticity & Grounding Rules
1. **NO INVENTED EMOTIONS OR DIALOGUE:** Do not fabricate artificial dramatic turning points (e.g., "At 2 AM, I stared at my screen with tears in my eyes..."). Keep the narrative factual, insightful, and professional.
2. **ZERO INVENTED METRICS:** Never claim "10x growth", "hundreds of users", or custom revenue milestones unless explicitly quantified in `source_records`.
3. **NO GENERIC HOOKS:** Avoid cringe bait openers like "I am humbled and honored to announce..." or "Here are 5 secrets nobody told you about AI...". Start directly with an interesting operational observation or problem statement.
4. **PRIVACY ENFORCEMENT:** If `anonymize_third_parties` is true, mask all external client or advisor names (e.g., replace "Yousuf Imran at Mangosteen" with "a seasoned startup product advisor").

---

## 4. Required Output Schema (JSON)
```json
{
  "title": "Draft: AI Execution Bottleneck Reflection",
  "body": "Building multi-agent autonomous coding loops taught me an unexpected lesson this week: speed without strict schema verification creates compound technical debt...\n\n[Full post text with purposeful paragraph breaks and zero unnecessary hashtags]",
  "word_count": 185,
  "authenticity_score": "Verified - 100% Grounded in Source Memories",
  "unsupported_claims": [],
  "citations": [
    { "source_id": "UUID", "excerpt_referenced": "Noted schema verification slowdown during Justor AI sprint." }
  ]
}
```

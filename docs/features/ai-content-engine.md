# AI Content Engine — Feature Specification
**Module Owner:** Agent 9 (Founder Growth, Evidence, and Content Layer)  
**Status:** Approved & Implemented  
**Reference Docs:** [PRD/TRD](../../Tajs_Second_Brain_PRD_TRD.md), [Database Schema](../../database_schema.md), [API Contracts](../../api_contracts.md)

---

## 1. Executive Summary & Authenticity Mandate
The AI Content Engine translates Taj’s real-world founder journey—decisions, pivots, meetings, technical breakthroughs, and reflective memories—into engaging, high-credibility professional outputs (LinkedIn posts, founder stories, project updates, investor newsletters, articles, and weekly reflections).
**Authenticity is absolute:** The system is explicitly programmed to reject generic motivational hype, fabricated emotional turns, invented dialogue, and exaggerated traction numbers. Every claim must trace directly back to real experiences stored within Taj's Second Brain.

---

## 2. Explicit User Approval & Zero Auto-Publishing Rule
- **Never Auto-Publish:** Under zero circumstances does the engine directly publish content to external platforms or mark drafts as public without explicit, intentional user initiation and approval.
- **Draft Buffer:** Every AI-generated output is created with `status = 'draft'`.
- **Status Progression:** `draft` -> `review` (checking evidence and privacy) -> `approved` (user explicit sign-off) -> `published` (manually recorded URL or future external publishing API trigger) -> `archived`.

---

## 3. Pre-Generation Privacy Review & Source Filtering
Before sending selected source records to external AI providers (Google Gemini / Claude / OpenAI):
1. **Automated Privacy Check:** The system scans selected memories, meeting notes, CRM interactions, and venture plans for sensitive contact details (phone numbers, private emails), NDA project terms, or private personal reflections.
2. **Review Modal:** The UI forces an explicit **Evidence Preview & Privacy Review**, allowing the user to deselect confidential items or request anonymized phrasing before initiating LLM generation.

---

## 4. Authenticity & Claim Validation Engine
Prior to returning a generated draft to the editor, an internal validation pass inspects output text for numerical figures, dates, proper nouns, and operational assertions:
- **Claim-to-Source Matcher:** Compares generated figures against selected source excerpts.
- **Unsupported Claim Flags:** Any metric or milestone appearing in the generated draft that cannot be verified against linked sources is highlighted in red/amber in the UI as an `[Unsupported AI Claim - Verify or Remove]`.
- **Conflict Detection:** Identifies contradictions between generated narrative and historical KPI entries or decision dates.

---

## 5. Version History & Section Regeneration (`content_versions`)
- **Immutable Revision Snapshots:** Modifying content bodies or regenerating specific paragraphs generates an immutable row in `public.content_versions` with timestamp, AI provider metadata, prompt version, and change notes.
- **Section Regeneration:** Using `POST /api/v1/content/{content_id}/regenerate-section`, the user can highlight a specific paragraph or section (e.g., "Executive Summary" or "Lessons Learned") and instruct the AI to expand, condense, or adjust tone without overwriting surrounding user-authored text or breaking existing citations.
- **Rollback Capabilities:** Instant restoration of previous versions preserves current version trail without destructive overwrites.

---

## 6. Supported Content Types & Objectives
1. **LinkedIn Post:** Share real lessons, project milestones, or founder reflections with authoritative first-person perspective.
2. **Founder Story:** Chronological narratives of overcoming technical or operational hurdles without invented drama.
3. **Project Update:** Clear, fact-based status summaries highlighting completed tasks, upcoming work, and honest blockers.
4. **Investor Update:** Structured briefings covering Product, Users, Partnerships, Revenue, Challenges, and Key Asks (omitting unsupported numerical traction).
5. **Article & Long-Form Thought Leadership:** Outlines and deep dives grounded in research and technical execution logs.
6. **Weekly Reflection:** Non-judgmental syntheses of weekly task wins, relationship nurturing, and KPI trajectory.

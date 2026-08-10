# Idea Vault & Strategic Validation System — Feature Specification
**Module Owner:** Agent 9 (Founder Growth, Evidence, and Content Layer)  
**Status:** Approved & Implemented  
**Reference Docs:** [PRD/TRD](../../Tajs_Second_Brain_PRD_TRD.md), [Database Schema](../../database_schema.md), [API Contracts](../../api_contracts.md)

---

## 1. Executive Summary & Core Purpose
The Idea Vault is Taj’s structured repository for early-stage startup ideation, problem-solution hypotheses, risk assessment, and empirical validation. Unlike standard note-taking tools, the Idea Vault systematically guides an initial flash of intuition through structured experimentation, evidence linking, and AI-assisted feasibility analysis before converting validated concepts into actionable execution projects.

---

## 2. Core Product Principles & Ownership
- **Strict User Ownership:** Every idea, assumption, validation experiment, and linked evidence record strictly belongs to `auth.uid() == user_id` via Row Level Security (RLS).
- **Evidence Before Claims:** AI analysis and feasibility scores rely on internal evidence linked from CRM people, meeting transcripts, decisions, and memories.
- **No Invented Market Metrics:** Neither the UI nor the AI backend may invent market revenue, user adoption percentages, or competitor traction. Unsupported assertions are explicitly marked as `needs_evidence` or unverified assumptions.

---

## 3. Idea Lifecycle & Approved Statuses
An idea moves through a controlled state machine governed by backend rules:
1. `captured`: Initial rough concept; allows quick capture with minimal mandatory fields.
2. `exploring`: Founder is fleshing out problem statement, proposed solution, and target users.
3. `validating`: Active testing of core assumptions via structured validation experiments.
4. `prioritized`: Idea demonstrated strong problem-solution viability and is scheduled for execution.
5. `building`: Idea is being converted or executed in tandem with a venture.
6. `paused`: Temporarily shelved due to strategic priorities or resource constraints.
7. `rejected`: Deemed unfeasible or out of focus; mandatory retention of rejection rationale.
8. `completed`: Successfully validated and transitioned (note: distinct from a completed execution project).
9. `archived`: Soft-deleted from active list views (`status = 'archived'`).

*Note:* Status transitions must never rely on color alone in the UI; text badges and accessible iconography are mandatory.

---

## 4. Structured Assumptions & Validation Tracking
Instead of unstructured text, ideas support structured assumptions across approved categories:
- **Categories:** `problem`, `user`, `market`, `solution`, `distribution`, `revenue`, `technical`, `regulatory`, `operational`.
- **Assumption Attributes:** Statement, Category, Importance (`low`, `medium`, `high`, `critical`), Evidence Status (`untested`, `supported`, `invalidated`), Validation Method, Result, and Notes.

### Validation Experiments (`/ideas/[ideaId]/validation`)
Each experiment records:
- Validation Question & Hypothesis
- Method (`user_interview`, `landing_page_test`, `prototype_test`, `market_research`, `pricing_test`, `technical_feasibility`, `competitor_review`)
- Target Participants, Start/End Dates, Observable Result, Linked Evidence, and Next Action.

---

## 5. AI Idea Analysis (`POST /api/v1/ideas/{idea_id}/analyze`)
- **Execution:** Uses Agent 8's AI provider abstraction (defaulting to `gemini-1.5-pro`) and hybrid RAG retrieval.
- **Analysis Scope:** Evaluates Problem clarity, Solution clarity, Target-user specificity, Strategic fit with existing ventures (e.g., Justor AI, Zqtion), Execution requirements, and Validation gaps.
- **Grounding Rules:** Labels all analysis clearly as AI-generated; cites linked internal records; stores historical analysis summaries separately without modifying user-authored fields.
- **Rate Limit:** Throttled to 30 requests/minute per user.

---

## 6. Idea-to-Project Conversion Transaction
When an idea is ready for execution, `POST /api/v1/ideas/{idea_id}/convert-to-project` triggers an atomic database transaction:
1. Verifies ownership of both the source idea and target venture.
2. Creates a new record in `public.projects` initialized with selected start/target dates, initial tasks, and scope description.
3. Sets `ideas.status = 'converted'` and records conversion timestamps and target project linkages.
4. **Historical Integrity:** The source idea is *never* deleted; its revision history and validation experiments remain linked to the new project for audit ability and reflective reviews.

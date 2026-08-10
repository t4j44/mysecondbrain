# Achievement Portfolio & Career Proof System — Feature Specification
**Module Owner:** Agent 9 (Founder Growth, Evidence, and Content Layer)  
**Status:** Approved & Implemented  
**Reference Docs:** [PRD/TRD](../../Tajs_Second_Brain_PRD_TRD.md), [Database Schema](../../database_schema.md), [API Contracts](../../api_contracts.md)

---

## 1. Executive Summary
The Achievement Portfolio turns Taj’s daily startup operations, completed tasks, executive decisions, and verified KPI milestones into undeniable professional credibility. It replaces generic resumes and self-congratulatory claims with verifiable Career Proof Case Studies tailored for executive roles (AI Product Manager, Chief Product Officer, Founder/Executive, Venture Partner).

---

## 2. Core Principle: Evidence Before Claims
Every achievement captured in `public.achievements` and compiled into `public.portfolio_case_studies` must be grounded in underlying system records:
- **Supported Evidence Types:** Completed Projects (`projects`), Tasks (`tasks`), Decisions (`decisions`), Uploaded Documents (`documents`), Meeting Transcripts (`meetings`), Reflective Memories (`memories`), KPI check-in logs (`kpi_entries`), CRM Collaborators (`people`), and user-supplied external URLs or certificates.
- **No Invented Impact:** Neither the user interface nor AI generation tools may fabricate impact numbers (e.g., "reduced latency by 65%" or "generated $100k ARR") unless explicit numerical evidence exists in linked KPI entries or documents.

---

## 3. Verification Statuses
Each achievement and case study claim carries an audited verification state:
1. `self_reported`: Authored by the user without internal Second Brain record links or external URLs. Valid for personal notes but highlighted in case studies as lacking citations.
2. `supported`: Linked to genuine internal records (e.g., meeting logs, project completion timestamps, decisions) confirming operational execution.
3. `verified`: Linked to quantitative KPI entries, external validated URLs, or cryptographic document checksums confirming real-world outcomes.
4. `needs_evidence`: AI or user-flagged claim that asserts specific metrics or milestones without supporting documentation attached.

*Note:* AI confidence or fluent phrasing **never** grants verified status. Verification is strictly derived from verified source link analysis.

---

## 4. AI Case Study Generation (`POST /api/v1/portfolio/generate`)
- **Inputs:** Target Role (e.g., "AI Product Manager"), Audience ("Investor / Recruiter"), Selected Achievement UUIDs, Linked Projects/Decisions, Tone, and Length.
- **AI Engine Responsibilities:** Synthesizes structured STAR/Case architecture: Title, Executive Summary, Problem, Context, Role & Responsibilities, Actions Taken, Quantified/Qualitative Impact, Demonstrated Skills, and Cited Sources.
- **Evidence Coverage Analysis:** Each generated section is automatically evaluated by deterministic link checkers:
  - `supported`: All assertions map to linked achievements/evidence.
  - `partially_supported`: Contains descriptive context without direct quantitative proof.
  - `unsupported`: Emits a visible yellow warning flag requiring user review or manual evidence attachment.
- **Mandatory User Review:** All generated case studies begin in `draft` state and require explicit founder editing and approval before archiving or presentation export.

---

## 5. Portability & Markdown Export Compatibility
Working cleanly with Agent 7 (Knowledge Export & Portability), portfolio case studies and achievements export directly to Obsidian-compatible Markdown files with rich YAML frontmatter containing stable source IDs, citation hyper-references (`file://` or app URI schemes), and verification timestamps.

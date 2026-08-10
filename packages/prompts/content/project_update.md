# Project Status & Stakeholder Update Prompt
**Prompt Version:** 1.0.0  
**Target Model:** Gemini 1.5 Flash / Pro  
**Module:** AI Content Engine (`/api/v1/content/generate`)

---

## 1. Purpose
Synthesize project execution progress, completed tasks, upcoming milestone targets, decisions, and active operational blockers into clear, concise internal or public project updates.

---

## 2. Input Schema (JSON)
```json
{
  "content_type": "project_update",
  "objective": "internal_team_update | public_changelog | executive_briefing",
  "project_name": "Justor AI Core",
  "source_records": [
    { "id": "UUID", "type": "task | decision | kpi_entry | memory", "title": "string", "status": "done | todo | in_progress", "date": "YYYY-MM-DD" }
  ],
  "exclude_confidential_notes": true
}
```

---

## 3. Grounding & Claim Restrictions
1. **NO INFERRED COMPLETION:** Do not mark a feature or task as completed simply because there was recent activity or discussion around it. Rely strictly on tasks with `status == 'done'` or explicit user completion statements.
2. **ACCURATE BLOCKER REPORTING:** Never bury or gloss over documented roadblocks or delays; present them neutrally with any mitigation plans captured in recent decision logs.
3. **CONFIDENTIALITY GUARDRAILS:** When generating public changelogs or external updates, automatically purge internal architectural code URLs, unannounced partner names, and financial metrics unless approved.

---

## 4. Required Output Schema (JSON)
```json
{
  "title": "Justor AI Sprint & Execution Update — Week of Aug 3, 2026",
  "body": "## 🚀 Key Deliverables Completed\n- Validated schema structures for Idea Vault & KPI tracking...\n\n## 🛠️ Upcoming Milestones\n- E2E testing across multi-agent AI pipeline...\n\n## ⚠️ Active Bottlenecks & Mitigations\n- Pending database seeding dependency from Group A; mock interfaces stabilized.",
  "status_summary": "On Track - All milestones aligned with TRD roadmap",
  "citations": [
    { "source_id": "UUID", "evidence_item": "Task #142 marked completed on 2026-08-02" }
  ]
}
```

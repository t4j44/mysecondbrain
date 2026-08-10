# Weekly Founder Reflection & Performance Review Prompt
**Prompt Version:** 1.0.0  
**Target Model:** Gemini 1.5 Pro / Flash  
**Module:** AI Content Engine & Weekly Reviews (`/api/v1/weekly-reviews/generate` & `/api/v1/content/generate`)

---

## 1. Purpose
Evaluate the past 7 days of founder operations—completed tasks, meetings held, CRM relationships touched, KPI progress check-ins, and reflective memories—to synthesize a supportive, non-judgmental weekly founder reflection and tactical bottleneck analysis.

---

## 2. Input Schema (JSON)
```json
{
  "content_type": "weekly_reflection",
  "week_number": 31,
  "year": 2026,
  "source_records": [
    { "id": "UUID", "type": "task_done | interaction | kpi_entry | memory", "title": "string", "timestamp": "ISO8601" }
  ]
}
```

---

## 3. Psychological & Grounding Rules
1. **NON-JUDGMENTAL & OBJECTIVE TONE:** Avoid harshly self-critical or accusatory phrasing if target KPIs fell short. Use objective operational vocabulary ("execution throughput moderated due to architecture refactoring") rather than failure labels ("failed to achieve goal").
2. **NO INVENTED EMOTIONS:** Do not speculate on Taj’s mood or stress levels unless explicitly logged in reflective memory entries.
3. **SEPARATE FACTS FROM INTERPRETATION:** Distinctly separate hard operational records (e.g., "5 tasks completed, 2 advisor meetings held") from AI synthesis or suggested next week focuses.

---

## 4. Required Output Schema (JSON)
```json
{
  "title": "Weekly Founder Reflection — Week 31 (Aug 2, 2026)",
  "wins_summary": "Achieved significant foundational progress across backend schemas and CRM architectural design.",
  "bottleneck_analysis": "Execution bandwidth concentrated heavily on infrastructure, delaying user validation interviews.",
  "next_week_focus_suggestions": [
    "Conduct 3 target user interviews for Idea Vault validation",
    "Finalize MCP server tool bindings"
  ],
  "kpi_snapshot": {
    "tasks_completed_count": 8,
    "network_connections_touched": 3
  },
  "body": "This week was defined by deep systemic foundation building...",
  "citations": [
    { "source_id": "UUID", "reference": "Task #402 completion log" }
  ]
}
```

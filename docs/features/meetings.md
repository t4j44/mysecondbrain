# Meeting Records & Notes — Feature Specification
**Module Owner:** Agent 6 (Network Intelligence CRM, Meetings, and Memory Agent)  
**Status:** In Progress / Blocked by Foundation  
**Reference Docs:** [PRD/TRD](../../Tajs_Second_Brain_PRD_TRD.md), [Database Schema](../../database_schema.md), [API Contracts](../../api_contracts.md)

---

## 1. Executive Summary & Core Purpose
Meetings represents the formal scheduler and structured notes engine of Taj's Second Brain. It supports logging calendar appointments, startup pitches, and team reviews. The system preserves raw founder notes independently from AI-generated summaries, mapping participants directly to the CRM directory to establish interaction histories.

---

## 2. Route Structures & Views
- `/meetings` — Grid of past and upcoming meetings with search and filter controls.
- `/meetings/new` — Meeting entry form (title, date/time, duration, location, participants, description).
- `/meetings/[meetingId]` — Deep-dive meeting cockpit presenting raw notes, participants list, AI transcripts (where uploaded), summaries, and action items.
- `/meetings/[meetingId]/edit` — Editor for meeting details and notes.
- `/upcoming-meetings` — Quick view of upcoming meetings.

---

## 3. Participant Mapping & Integrity
- **CRM Integration**: Adding meeting participants searches the existing `people` table. 
- **Nested Workflow**: If a participant does not exist, the form offers a "Quick Add Person" link. This opens a drawer allowing the user to create the contact card without losing their current meeting form state.
- **Safety**: Deleting a participant from a meeting removes them from `meeting_participants` but does *not* delete their profile from the CRM.

---

## 4. Structured Notes & AI Action Conversions
- **Preservation of Raw Input**: Raw text inputs logged by Taj are stored in the database unchanged. AI summary generation (owned by Agent 8) writes to distinct fields (`ai_summary`, `action_items`) to avoid overwriting Taj's original notes.
- **Explicit Conversion Prompts**: Handlers are provided to manually convert action items into task objects or capture specific decisions. These triggers require explicit user confirmation.

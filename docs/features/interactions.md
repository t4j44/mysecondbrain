# Interactions Timeline & Log — Feature Specification
**Module Owner:** Agent 6 (Network Intelligence CRM, Meetings, and Memory Agent)  
**Status:** In Progress / Blocked by Foundation  
**Reference Docs:** [PRD/TRD](../../Tajs_Second_Brain_PRD_TRD.md), [Database Schema](../../database_schema.md), [API Contracts](../../api_contracts.md)

---

## 1. Executive Summary & Core Purpose
The Interactions journal records every meaningful exchange Taj has across channels (meetings, phone calls, email notes, instant chats, or events). Each interaction entry maintains a summary, key takeaways, next actions, and connections to people, ventures, or projects. This forms the chronological narrative that feeds both the CRM timeline views and the downstream AI retrieval context.

---

## 2. Route Structures & Views
- `/interactions` — Chronological history of all interactions with keyword search.
- `/interactions/new` — Form to log a new exchange. Supports pre-selecting the active person, venture, or project when opened contextually.
- `/interactions/[interactionId]` — Deep view of notes, takeaways, participants, and linked records.
- `/interactions/[interactionId]/edit` — Form to modify summaries or update follow-up schedules.

---

## 3. Timeline Layout & Ordering
- **Chronological Density**: Timelines display in descending chronological order (most recent first) by default. Pagination is enforced to prevent loading massive note trees on page mount.
- **Visual connectors**: Styled with thin, retro-terminal borders, keeping layout integrity clean and readable even on narrow screens or without visual graphics.
- **Linked Actions**: Includes quick action toggles: "Create follow-up task", "Add to person timeline", and "Capture as memory".

---

## 4. Task Integration (Follow-Ups)
- When logging next actions inside an interaction, the UI displays a checkbox to "Create corresponding follow-up task".
- Checking this option prompts the user with a pre-filled title ("Follow up: [Contact Name] regarding [Topic]") and due date.
- The task is registered via the backend in the `public.tasks` table, establishing a clean trace that keeps both task and CRM systems synchronized without creating duplicate/redundant structures.

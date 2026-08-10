# Network Intelligence CRM — Feature Specification
**Module Owner:** Agent 6 (Network Intelligence CRM, Meetings, and Memory Agent)  
**Status:** In Progress / Blocked by Foundation  
**Reference Docs:** [PRD/TRD](../../Tajs_Second_Brain_PRD_TRD.md), [Database Schema](../../database_schema.md), [API Contracts](../../api_contracts.md)

---

## 1. Executive Summary & Core Purpose
The Network Intelligence CRM is the relationship tracking center for Taj’s Second Brain. It manages individual contact profiles (mentors, investors, peers, collaborators), mapping their roles, locations, industries, and social links. The core purpose is to preserve high-fidelity context for every connection without turning the system into a heavy sales pipeline. 

It provides:
- Quick visual access to relationship strength and contact categories.
- Automatic calculation of days since last interaction to help identify contacts that need attention.
- Duplicate detection warning mechanisms to flag overlapping contacts.

---

## 2. Route Structures & Views
The CRM implements the following routes:
- `/people` — Main directory of active contacts.
- `/people/new` — Secure form to create a new person record.
- `/people/[personId]` — Rich individual relationship profile detailing identity, timeline, and memories.
- `/people/[personId]/edit` — Form to modify existing attributes.
- `/people/follow-ups` — Dashboard dedicated to managing overdue or scheduled action items.
- `/people/recent` — View of contacts sorted chronologically by latest interaction date.

---

## 3. UI/UX Components & Visual Style
Adhering to the **Retro-Futuristic Founder Terminal** design system:
- **Timeline Cards**: Monospaced dates, clean typography details, and text indicators for interaction type (e.g. `[Call]`, `[Meeting]`, `[Email Note]`).
- **Relationship Strength Badge**: Non-color-only tags (e.g. `Strength: High (4/5)`) to satisfy accessibility.
- **Empty States**: Encouraging prompts ("No people saved yet. Add important founders, mentors, investors, or collaborators to start.") to guide next actions.
- **Responsive Layout**: Two-column layout on desktop (profile identity & metrics left, interaction timeline right), collapsing gracefully into a single-column stacked view on mobile.

---

## 4. Duplicate Person Detection
To maintain database integrity, the interface and backend cooperate on duplicate warnings:
- **Signals**: Exact match on email/phone, or close string matching (Jaro-Winkler/Trigram) on Name paired with similar Company or Location.
- **Workflow**:
  1. On typing names or emails, a client-side query triggers a non-blocking background check.
  2. If duplicate candidates are identified, a warning banner lists candidate profiles with non-sensitive fields (e.g., "Yousuf Imran, Mangosteen Studio").
  3. The user can opt to view the existing profile or continue creating the new record. Auto-merges are strictly forbidden to prevent database corruption.

---

## 5. Security & Privacy Safeguards
- **JWT Verification Scope**: The backend validates user ownership (`auth.uid() == user_id`) on all SQL queries. Client-supplied ownership IDs are ignored.
- **Information Masking**: Sensitive contact fields (phone numbers, private emails) are hidden by default behind an "Expand to View" action, preventing visual leaks during presentations or screen-sharing.
- **Zero Ingestion Leakage**: Plaintext contact details or raw personal logs are excluded from server exception traces and diagnostic files.

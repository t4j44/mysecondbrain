# Organization Management — Feature Specification
**Module Owner:** Agent 6 (Network Intelligence CRM, Meetings, and Memory Agent)  
**Status:** In Progress / Blocked by Foundation  
**Reference Docs:** [PRD/TRD](../../Tajs_Second_Brain_PRD_TRD.md), [Database Schema](../../database_schema.md), [API Contracts](../../api_contracts.md)

---

## 1. Executive Summary & Core Purpose
Organizations are directory containers representing company partners, venture capital firms, startup accelerators, or institutions that Taj interacts with. Every organization in the system is completely private to the authenticated user. Individual people profiles can link to a primary organization, allowing Taj to view groups of contacts associated with specific enterprise entities.

---

## 2. Route Structures & Views
The Organizations module implements:
- `/organizations` — List of all organizations filtered by industry or location, with search indexing on name.
- `/organizations/new` — Secure form to register a new firm.
- `/organizations/[organizationId]` — Profile view showing the company info, list of associated people (linked via `people.organization_id`), and aggregate interaction history.
- `/organizations/[organizationId]/edit` — Form to update details.

---

## 3. Data Integrity & Archival Rules
- **No Cascade Deletion**: Deleting or archiving an organization will *never* delete the associated people records. The backend triggers a set-null operation on `people.organization_id` (or leaves it linked to an archived organization) to prevent accidental data loss.
- **Private Entity Scope**: Duplicate organizations are allowed across different accounts (e.g. User A and User B can both have their own private "Google" organization), but are isolated via RLS policies.
- **Website Sanitization**: Input fields for websites are validated to prevent cross-site scripting (XSS) or malformed URLs, defaulting to safe protocol prepending (e.g. prepending `https://` if missing).

# Reflective Memory System — Feature Specification
**Module Owner:** Agent 6 (Network Intelligence CRM, Meetings, and Memory Agent)  
**Status:** In Progress / Blocked by Foundation  
**Reference Docs:** [PRD/TRD](../../Tajs_Second_Brain_PRD_TRD.md), [Database Schema](../../database_schema.md), [API Contracts](../../api_contracts.md)

---

## 1. Executive Summary & Core Purpose
The Memory module acts as Taj's private reflection log and long-term knowledge repository. It captures lessons learned, observations, and decisions, organizing them with tags and connections to people, projects, and ventures. These records serve as the primary source of truth for semantic vector indexing, allowing future AI retrieval interfaces to answer strategy questions based on Taj's historical journey.

---

## 2. Route Structures & Views
- `/memories` — Card-based grid browser showing memories with category/tag filters and query search.
- `/memories/new` — Full editor for logging strategy notes and reflections.
- `/memories/[memoryId]` — Detail page showing title, full text body, tags, and all linked associations.
- `/memories/[memoryId]/edit` — Form to edit content and manage relationships.

---

## 3. Approved Memory Types
To preserve catalog consistency, memories utilize the following categorization check constraints:
- `reflection` — Personal reflections on founder growth.
- `lesson` — Key tactical startup or operational insights.
- `win` / `failure` — Milestones and outcomes analyzed for growth.
- `observation` — High-level notes on people, markets, or technologies.
- `decision_context` — In-depth reasoning backing venture moves.

---

## 4. Multi-Record Linking Workflow
- **Bi-directional Reference UI**: Users can search and link memories to other entities (e.g. associating a reflection with a Person, a Venture, a Project, or a Meeting).
- **Searchable Selectors**: To prevent performance lag, lists of options are loaded asynchronously via search queries rather than dump-loading the entire directory into memory on mount.
- **Unlinking Integrity**: Removing a connection updates the junction record or foreign keys without destroying the underlying contact or project.
- **Vector Reindexing Trigger**: Modifying the memory body text triggers a backend job to regenerate embeddings asynchronously, marking the index state as processing until updated.

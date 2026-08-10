# Venture Management Feature Specification

## Purpose
Venture Management enables the founder to initialize and supervise high-level startup initiatives (e.g. Justor AI, Zqtion, IEXF, CMOOS) that containerize nested project milestones and operational tasks.

---

## Routes
* **`/ventures`**: Grid listing active and archived ventures with search.
* **`/ventures/new`**: Initializer form to register a new venture.
* **`/ventures/[id]`**: Workspace details, active projects progress, and pending tasks.
* **`/ventures/[id]/edit`**: Configuration panel for renaming, pausing, exiting, or archiving.

---

## Technical Features

### 1. Unique Slug Validation
When creating a venture, the initializer validates that the lowercase slug identifier is completely unique. Auto-slug generation translates titles on input (e.g. `Justor AI` -> `justor-ai`).

### 2. Status States
Supports four core lifecycle statuses matching the database schema CHECK constraints:
* `active`
* `paused`
* `exited`
* `archived` (hidden from default view)

### 3. Cascaded Archiving
Archiving a venture triggers a soft-archival pass. The database updates `status = 'archived'` and applies `deleted_at = NOW()`, propagating down to all linked projects and tasks.

### 4. Interactive Workspace
The detail page displays metrics aggregating project counts and active task lists. Clicking a project card redirects the user directly to the project's detail route.

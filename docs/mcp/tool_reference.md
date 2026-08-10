# MCP Server Tool & Resource Reference Guide

## 1. Exploratory Intelligence Tools (Read-Only)

### `search_people`
* **Description**: Query contacts, executive mentors, and companies across Taj's CRM network.
* **Arguments**:
  * `query` (string, optional): Keyword search matching names, roles, companies, locations, or note snippets.
  * `limit` (int, default 20): Maximum records to return.
* **Required Scope**: `mcp:people:read`
* **Source Grounding**: Returns citations with pattern `mcp://people/{person_id}`.

### `search_memory`
* **Description**: Query internal second brain thoughts, notes, and founder reflections.
* **Arguments**:
  * `query` (string, optional): Text matching title and memory content bodies.
  * `category` (string, optional): Filter by operational category (e.g., `strategy`, `architecture`).
  * `limit` (int, default 20): Maximum records to retrieve.
* **Required Scope**: `mcp:memory:read`
* **Source Grounding**: Returns citations with pattern `mcp://memory/{memory_id}`.

### `get_projects`
* **Description**: Retrieve founder ventures, initiatives, and milestone statuses.
* **Arguments**:
  * `status` (string, optional): Filter by lifecycle state (e.g., `in_progress`, `completed`).
  * `limit` (int, default 20): Maximum records to return.
* **Required Scope**: `mcp:projects:read`

### `get_tasks`
* **Description**: Query actionable execution TODO items across strategic workflows.
* **Arguments**:
  * `status` (string, optional): Task completion state (e.g., `pending`, `in_progress`).
  * `limit` (int, default 20): Maximum records to return.
* **Required Scope**: `mcp:tasks:read`

### `get_calendar`
* **Description**: Fetch executive meetings, participant lists, and calendar schedules.
* **Arguments**:
  * `start_date` / `end_date` (string, optional): ISO 8601 boundary timestamps.
  * `limit` (int, default 20): Maximum calendar items.
* **Required Scope**: `mcp:calendar:read`

### `get_relationship_history`
* **Description**: Retrieve chronological interaction logs and shared takeaways with a specific individual.
* **Arguments**:
  * `person_id` (string, required): Target contact UUID.
  * `limit` (int, default 20): Maximum interaction entries.
* **Required Scope**: `mcp:relationship_history:read`

---

## 2. Generative Content & Workflow Drafting Tools

> [!IMPORTANT]
> All drafting tools operate strictly in non-destructive mode. They synthesize underlying founder data into high-quality textual structures containing verifiable citation hyperlinks and explicitly require human acceptance before any external publishing occurs.

### `generate_linkedin_post`
* **Description**: Synthesizes recent project milestones and founder reflections into a thought-leadership draft.
* **Arguments**:
  * `topic` (string, required): Strategic focus or engineering takeaway theme.
  * `style_tone` (string, default `"executive"`): Narrative voice style.
* **Required Scope**: `mcp:content:draft`

### `generate_case_study`
* **Description**: Formulates an executive STAR case study demonstrating technical excellence and career achievements.
* **Arguments**:
  * `project_name` (string, required): Name of target project or venture to profile.
  * `target_role` (string, default `"Executive / Technical Leader"`): Tailored position positioning.
* **Required Scope**: `mcp:case_study:draft`

### `generate_weekly_review`
* **Description**: Compiles weekly completed tasks, meeting agendas, and personal reflections into an executive retrospective report.
* **Arguments**:
  * `week_starting` (string, optional): ISO date representing the start of the audit window.
* **Required Scope**: `mcp:weekly_review:draft`

---

## 3. Resource URI Templates

| URI Scheme & Template | Target Handler | Required Capability Scope | Output Structure |
| :--- | :--- | :--- | :--- |
| `mcp://people/{person_id}` | `read_person_resource` | `mcp:people:read` | JSON document of CRM contact & company ties. |
| `mcp://memory/{memory_id}` | `read_memory_resource` | `mcp:memory:read` | JSON document of captured note & tags. |
| `mcp://projects/active` | `list_active_projects_resource` | `mcp:projects:read` | List of active initiatives and progress metrics. |
| `mcp://tasks/pending` | `list_pending_tasks_resource` | `mcp:tasks:read` | Ordered list of urgent founder TODO items. |
| `mcp://portfolio/case-studies`| `list_case_studies_resource` | `mcp:projects:read` | Verified career proof case study summaries. |
| `mcp://calendar/today` | `read_today_calendar_resource` | `mcp:calendar:read` | Today's scheduled executive meetings. |

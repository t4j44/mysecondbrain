# Task Management Feature Specification

## Purpose
Task Management implements the linear operational task flows for day-to-day execution, supporting deadlines, tags, priority weights, and venture/project contexts.

---

## Routes
* **`/tasks`**: Master task board incorporating sub-views, search query filters, and details editors.
* **`/tasks/today`**: Focused view showing tasks due today or overdue.
* **`/tasks/upcoming`**: Timeline view grouping tasks by chronological deadlines.
* **`/tasks/completed`**: History log of done tasks.

---

## Technical Features

### 1. View Filtering
* **Today Focus:** Filtered strictly for incomplete tasks where `due_date <= current_date` or priority is `urgent`.
* **Upcoming Sprint:** Chronologically ordered list of tasks due in future dates.
* **Completed Log:** List of resolved tasks, preserving done states.

### 2. Optimistic UI Updates & Rollback
Quick-completion clicks instantly update task checkboxes and cross-line titles locally. The app initiates the background request:
`PATCH /api/v1/tasks/{id}/status`
If the mock API triggers a save failure, the UI rolls back to the previous checkbox state immediately and prints an error message.

### 3. Detail Editor Drawer
Clicking a task opens a Dialog modal allowing modification of all parameters:
* Title & Description
* Status (`todo`, `in_progress`, `done`, `cancelled`)
* Priority (`low`, `medium`, `high`, `urgent`)
* Due Date
* Linked Venture & Project dropdowns

### 4. Delete & Archiving
Soft-deletes tasks by updating their status to `'archived'` and applying `deleted_at = NOW()`, preserving historical records in database audit trails.

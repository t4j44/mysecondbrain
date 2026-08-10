# Project Management Feature Specification

## Purpose
Project Management defines the execution layer residing inside or independent of ventures. It organizes tasks into structured pipelines and displays completeness progress.

---

## Routes
* **`/projects`**: Searchable grid index of projects filtered by status.
* **`/projects/new`**: Creator form to initialize a project with an optional venture link.
* **`/projects/[id]`**: Detail workspace displaying project specs, progress, and task checklists.
* **`/projects/[id]/edit`**: Editor panel to update description, linked venture, status, or progress.

---

## Technical Features

### 1. Progress Calculation Modes
* **Derived Progress:** Project progress dynamically updates in the mock database when tasks are added, completed, or deleted. The progress calculation evaluates:
  $$\text{Progress} = \left( \frac{\text{Completed Tasks}}{\text{Total Tasks}} \right) \times 100$$
* **Manual Override:** The edit project page allows manual progress override matching custom progress indicators.

### 2. Venture Linking dropdown
Checks for active ventures to populate links. Supports independent project workspaces where no venture parent is linked.

### 3. Contextual Redirects
Creating a project under a specific venture preset links the ID automatically via URL parameters (e.g. `/projects/new?ventureId=v-1`).

### 4. Interactive Checklist
Task toggles on the detail page automatically trigger local updates, recalculating project completeness percentages and refreshing the progress bar on screen without page reloads.

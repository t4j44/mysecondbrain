# Founder Dashboard Feature Specification

## Purpose
The Founder Dashboard serves as the central command center for Tajul Islam (Founder) to supervise day-to-day operations and reflect on AI-driven guidance. It aggregates his master mission, focus tasks, upcoming meetings, key performance indicator (KPI) highlights, recent memories, and executive advisor recommendations.

---

## Routes
* **`/dashboard`**: The dashboard route rendering layout panels.

---

## Technical Components

### 1. `FounderDashboard` (`src/app/dashboard/page.tsx`)
Aggregator container which triggers mock data fetching on mount and binds a listener to the custom `second-brain-data-updated` event to reactive-refresh panels when mutations occur.

### 2. `MissionCard` (`src/components/dashboard/MissionCard.tsx`)
* **Purpose:** Highlights Taj's current high-level guiding mission.
* **Interactions:** Allows inline editing with Save/Cancel buttons. Editing writes back to the mock user profile directly.

### 3. `TodayFocusPanel` (`src/components/dashboard/TodayFocusPanel.tsx`)
* **Purpose:** Displays up to 3 priority tasks that are due today or overdue.
* **Interactions:** Direct checkbox status toggle triggers optimistic completeness transitions. Quick defer buttons allow rescheduling overdue tasks with a single click.

### 4. `TaskSummaryCard` (`src/components/dashboard/DashboardWidgets.tsx`)
* **Purpose:** Highlights core metrics counts (Today, Overdue, Upcoming, Completed).
* **Interactions:** Links each card dynamically to `/tasks` pre-configured with SWR query filters.

### 5. `ActiveVenturesPanel` & `ProjectPulsePanel` (`src/components/dashboard/DashboardVentureProjectWidgets.tsx`)
* **Purpose:** Lists active ventures (along with linked project and task counts) and active projects (including status and execution progress bars).

### 6. `AIInsightPanel` (`src/components/dashboard/DashboardWidgets.tsx`)
* **Purpose:** Displays advisory insights, recommended actions, and a manual refresh trigger.

---

## Visual Design & Theme
Adheres strictly to the **Retro-Futuristic Founder Terminal** design standard:
* **Background:** Deep purple (`#12081d`)
* **Panels:** Dark black console boxes (`#0a0510`)
* **Typography:** Cream text (`#f7f4ea`), mono indicators (`#00ff9d`)
* **Borders:** Thin solid boundaries with subtle glow on hover

export type VentureStatus = 'active' | 'paused' | 'exited' | 'archived';
export type ProjectStatus = 'planning' | 'in_progress' | 'completed' | 'on_hold' | 'archived';
export type TaskStatus = 'todo' | 'in_progress' | 'done' | 'cancelled' | 'archived';
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface Venture {
  id: string;
  name: string;
  slug: string;
  vision?: string | null;
  mission?: string | null;
  status: VentureStatus;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
  // UI metrics (derived)
  project_count?: number;
  open_task_count?: number;
}

export interface Project {
  id: string;
  venture_id?: string | null;
  name: string;
  description?: string | null;
  status: ProjectStatus;
  target_date?: string | null;
  progress: number; // 0 - 100
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
  // UI metrics (derived)
  open_task_count?: number;
  blocked_task_count?: number;
}

export interface Task {
  id: string;
  venture_id?: string | null;
  project_id?: string | null;
  person_id?: string | null;
  title: string;
  description?: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  due_date?: string | null;
  completed_at?: string | null;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
  // UI helpers
  gcal_event_id?: string | null;
}

export interface DashboardSummary {
  current_mission_venture?: Venture | null;
  today_focus_tasks: Task[];
  calendar_events_today: Array<{
    id: string;
    title: string;
    time: string;
    duration?: number;
    source?: string;
  }>;
  active_projects_count: number;
  kpi_highlights: Array<{
    metric_name: string;
    current_value: number;
    target_value: number;
    unit: string;
  }>;
  recent_memory_stream: Array<{
    id: string;
    title: string;
    category?: string;
    created_at: string;
  }>;
  relationship_follow_ups: Array<{
    id: string;
    name: string;
    role?: string;
    follow_up_date: string;
    next_action?: string;
    overdue: boolean;
  }>;
}

export interface AIInsights {
  ai_insight: string;
  recommended_actions: string[];
}

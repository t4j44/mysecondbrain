/** Domain types aligned with FastAPI founder.py / network.py response schemas */

export interface ListResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface Venture {
  id: string;
  user_id: string;
  name: string;
  slug: string;
  vision?: string | null;
  mission?: string | null;
  description?: string | null;
  status: string;
  priority: string;
  start_date?: string | null;
  target_date?: string | null;
  metadata_payload?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  archived_at?: string | null;
}

export interface Project {
  id: string;
  user_id: string;
  venture_id?: string | null;
  name: string;
  description?: string | null;
  status: string;
  priority: string;
  progress: number;
  start_date?: string | null;
  target_date?: string | null;
  completion_date?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: string;
  user_id: string;
  venture_id?: string | null;
  project_id?: string | null;
  person_id?: string | null;
  title: string;
  description?: string | null;
  status: string;
  priority: string;
  start_date?: string | null;
  due_date?: string | null;
  completion_date?: string | null;
  estimated_effort?: string | null;
  tags: string[];
  calendar_sync_metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Person {
  id: string;
  user_id: string;
  name: string;
  role?: string | null;
  company?: string | null;
  industry?: string | null;
  location?: string | null;
  email?: string | null;
  phone?: string | null;
  linkedin_url?: string | null;
  relationship_type: string;
  last_interaction_at?: string | null;
  notes?: string | null;
  tags: string[];
  follow_up_date?: string | null;
  metadata_payload?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  archived_at?: string | null;
}

export type TaskStatusFilter = 'all' | 'todo' | 'in_progress' | 'done';

export type VentureCreateInput = Pick<Venture, 'name'> & {
  description?: string;
  priority?: string;
  status?: string;
  vision?: string;
};

export type ProjectCreateInput = Pick<Project, 'name'> & {
  venture_id?: string;
  description?: string;
  priority?: string;
  status?: string;
};

export type TaskCreateInput = Pick<Task, 'title'> & {
  venture_id?: string;
  project_id?: string;
  priority?: string;
  status?: string;
  due_date?: string;
};

export type PersonCreateInput = Pick<Person, 'name' | 'relationship_type'> & {
  role?: string;
  company?: string;
  email?: string;
  phone?: string;
  linkedin_url?: string;
  notes?: string;
  tags?: string[];
};

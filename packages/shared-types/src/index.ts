/**
 * Master Shared TypeScript Contracts - Taj's Second Brain
 * Synchronized with database_schema.md & api_contracts.md
 */

// ============================================================================
// API WRAPPER & ERROR CONTRACTS
// ============================================================================

export interface ApiMeta {
  timestamp?: string;
  request_id?: string;
}

export interface ApiResponse<T = any> {
  data: T;
  meta?: ApiMeta;
}

export interface ApiPagination {
  limit: number;
  next_cursor?: string | null;
  has_more: boolean;
}

export interface ApiPaginatedResponse<T = any> {
  data: T[];
  pagination: ApiPagination;
  meta?: ApiMeta;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  details?: unknown;
  request_id?: string;
}

export interface ApiErrorResponse {
  error: ApiErrorDetail;
}

// ============================================================================
// DOMAIN STATUS & TYPE CONSTRAINTS
// ============================================================================

export type TaskStatus = 'todo' | 'in_progress' | 'done' | 'cancelled' | 'archived';
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';
export type ProjectStatus = 'planning' | 'in_progress' | 'completed' | 'on_hold' | 'archived';
export type VentureStatus = 'active' | 'paused' | 'exited' | 'archived';
export type IdeaStatus = 'draft' | 'validating' | 'executing' | 'converted' | 'archived';
export type RelationshipType = 'mentor' | 'investor' | 'peer' | 'collaborator' | 'lead' | 'client' | 'contact';
export type InteractionType = 'meeting' | 'call' | 'email' | 'chat' | 'event' | 'note';
export type ContentStatus = 'draft' | 'review' | 'published' | 'archived';
export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'retried';
export type DocStatus = 'pending' | 'processing' | 'completed' | 'failed';
export type AuthorType = 'user' | 'ai_assistant' | 'system' | 'tool';

// ============================================================================
// CORE ENTITY SCHEMAS
// ============================================================================

export interface UserSettings {
  theme?: 'dark' | 'light' | 'system';
  timezone?: string;
  [key: string]: unknown;
}

export interface Profile {
  id: string;
  email: string;
  full_name?: string | null;
  avatar_url?: string | null;
  bio?: string | null;
  settings: UserSettings;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
}

export interface Venture {
  id: string;
  user_id: string;
  name: string;
  slug: string;
  vision?: string | null;
  mission?: string | null;
  status: VentureStatus;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
}

export interface Project {
  id: string;
  user_id: string;
  venture_id?: string | null;
  name: string;
  description?: string | null;
  status: ProjectStatus;
  target_date?: string | null;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
}

export interface Task {
  id: string;
  user_id: string;
  venture_id?: string | null;
  project_id?: string | null;
  person_id?: string | null;
  title: string;
  description?: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  due_date?: string | null;
  completed_at?: string | null;
  gcal_event_id?: string | null;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
}

export interface Person {
  id: string;
  user_id: string;
  organization_id?: string | null;
  name: string;
  role?: string | null;
  company?: string | null;
  industry?: string | null;
  location?: string | null;
  email?: string | null;
  phone?: string | null;
  linkedin_url?: string | null;
  relationship_type: RelationshipType;
  last_interaction_at?: string | null;
  notes?: string | null;
  tags: string[];
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
}

export interface Organization {
  id: string;
  user_id: string;
  name: string;
  domain?: string | null;
  industry?: string | null;
  location?: string | null;
  website_url?: string | null;
  description?: string | null;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
}

export interface Memory {
  id: string;
  user_id: string;
  title: string;
  content: string;
  category?: string | null;
  tags: string[];
  linked_venture_id?: string | null;
  linked_person_id?: string | null;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
}

export interface Meeting {
  id: string;
  user_id: string;
  venture_id?: string | null;
  title: string;
  meeting_date: string;
  duration_minutes?: number | null;
  location?: string | null;
  recording_url?: string | null;
  transcript_text?: string | null;
  ai_summary?: string | null;
  action_items: string[];
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
}

export interface Idea {
  id: string;
  user_id: string;
  venture_id?: string | null;
  title: string;
  problem?: string | null;
  solution?: string | null;
  market?: string | null;
  potential_score?: number | null;
  ai_validation_summary?: string | null;
  status: IdeaStatus;
  next_steps?: string | null;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
}

export interface KpiDefinition {
  id: string;
  user_id: string;
  category: 'founder' | 'network' | 'learning' | 'venture';
  metric_name: string;
  target_value: number;
  current_value: number;
  unit: string;
  period: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
}

export type VerificationStatus = 'verified' | 'supported' | 'needs_evidence' | 'self_reported' | string;
export type ContentType = 'linkedin_post' | 'founder_story' | 'case_study' | 'article' | 'update' | string;

export interface CreateIdeaRequest {
  title: string;
  problem?: string;
  solution?: string;
  market?: string;
  [key: string]: any;
}

export type AssumptionCategory = 'problem' | 'solution' | 'market' | 'execution' | string;

export interface IdeaAIAnalysisResult {
  feasibility_score?: number;
  market_size_summary?: string;
  key_assumptions?: Array<{ category: AssumptionCategory; description: string; risk_level: string; [key: string]: any }>;
  competitors?: string[];
  recommendations?: string[];
  [key: string]: any;
}

export interface PortfolioCaseStudy {
  id: string;
  title: string;
  summary?: string;
  content?: string;
  status?: 'draft' | 'approved' | 'published' | string;
  is_public?: boolean;
  is_ai_generated?: boolean;
  ai_provider?: string;
  ai_model?: string;
  created_at?: string;
  updated_at?: string;
  [key: string]: any;
}

export interface Achievement {
  id: string;
  user_id: string;
  venture_id?: string | null;
  project_id?: string | null;
  title: string;
  role: string;
  problem?: string | null;
  responsibilities: string[];
  impact: string;
  skills: string[];
  achievement_date: string;
  verification_status?: VerificationStatus;
  visibility?: string;
  evidence?: Array<{ id: string; achievement_id: string; source_id: string; source_type: string; source_title: string; source_date: string; created_at: string; [key: string]: any }>;
  related_people_ids?: string[];
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
}

export interface ContentItem {
  id: string;
  user_id: string;
  venture_id?: string | null;
  title: string;
  content_type: ContentType;
  current_body: string;
  status: ContentStatus;
  published_url?: string | null;
  cited_record_ids: string[];
  claim_validation_results?: Array<{ status: string; claim_text: string; reason: string; [key: string]: any }>;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
}


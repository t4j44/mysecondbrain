/**
 * AI Content Engine Shared Domain Types & API Contracts
 * Module Owner: Agent 9
 * Enforces zero auto-publishing & strict fact-grounding.
 */

export type ContentType =
  | 'linkedin_post'
  | 'founder_story'
  | 'project_update'
  | 'case_study'
  | 'article'
  | 'weekly_reflection'
  | 'investor_update'
  | 'professional_summary'
  | 'update'; // compatibility with db constraint

export type ContentStatus = 'draft' | 'review' | 'approved' | 'published' | 'archived';

export interface ContentSourceRef {
  id: string;
  type: 'venture' | 'project' | 'task' | 'person' | 'interaction' | 'meeting' | 'memory' | 'idea' | 'decision' | 'achievement' | 'kpi_entry' | 'weekly_review';
  title: string;
  date: string;
  excerpt?: string;
  is_user_authored?: boolean;
}

export interface ContentCitation {
  source_id: string;
  source_title: string;
  source_type: string;
  claim_supported: string;
}

export interface ClaimValidationResult {
  claim_text: string;
  status: 'supported' | 'unsupported_metric' | 'potential_conflict';
  reason?: string;
  source_reference?: string;
}

export interface ContentVersion {
  id: string;
  user_id: string;
  content_id: string;
  version_number: number;
  body_snapshot: string;
  title_snapshot: string;
  change_summary?: string | null;
  created_by: 'user' | 'ai_assistant';
  provider?: string | null;
  model?: string | null;
  prompt_version?: string | null;
  created_at: string;
}

export interface ContentItem {
  id: string;
  user_id: string;
  venture_id?: string | null;
  title: string;
  content_type: ContentType;
  objective?: string | null;
  target_audience?: string | null;
  current_body: string;
  status: ContentStatus;
  published_url?: string | null;
  published_date?: string | null;
  cited_record_ids: string[];
  cited_sources?: ContentCitation[];
  claim_validation_results?: ClaimValidationResult[];
  latest_version_number: number;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
}

export interface GenerateContentRequest {
  content_type: ContentType;
  topic?: string;
  objective?: string;
  target_audience?: string;
  source_record_ids: string[];
  tone?: string;
  length?: 'short' | 'medium' | 'long';
  anonymize_third_parties?: boolean;
}

export interface CreateContentRequest {
  title: string;
  content_type: ContentType;
  current_body: string;
  venture_id?: string;
  objective?: string;
  target_audience?: string;
  status?: ContentStatus;
  cited_record_ids?: string[];
}

export interface UpdateContentRequest extends Partial<CreateContentRequest> {
  published_url?: string;
  published_date?: string;
  change_note?: string; // For creating an explicit version entry
}

export interface RegenerateSectionRequest {
  section_id_or_title: string;
  current_section_text: string;
  instruction: string;
  source_record_ids?: string[];
  tone?: string;
  length?: 'condense' | 'expand' | 'maintain';
}

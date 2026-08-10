/**
 * Idea Vault Shared Domain Types & API Contracts
 * Module Owner: Agent 9
 * Strict adherence to database schema & RLS user isolation rules.
 */

export type IdeaStatus =
  | 'captured'
  | 'exploring'
  | 'validating'
  | 'prioritized'
  | 'building'
  | 'paused'
  | 'rejected'
  | 'completed'
  | 'archived'
  // Also compatibility with simple DB check constraint if needed: 'draft' | 'validating' | 'executing' | 'converted' | 'archived'
  | 'draft'
  | 'executing'
  | 'converted';

export type AssumptionCategory =
  | 'problem'
  | 'user'
  | 'market'
  | 'solution'
  | 'distribution'
  | 'revenue'
  | 'technical'
  | 'regulatory'
  | 'operational';

export type AssumptionImportance = 'low' | 'medium' | 'high' | 'critical';
export type AssumptionEvidenceStatus = 'untested' | 'supported' | 'invalidated';

export interface StructuredAssumption {
  id: string;
  statement: string;
  category: AssumptionCategory;
  importance: AssumptionImportance;
  evidence_status: AssumptionEvidenceStatus;
  validation_method?: string;
  result?: string;
  notes?: string;
}

export type ValidationMethod =
  | 'user_interview'
  | 'landing_page_test'
  | 'prototype_test'
  | 'market_research'
  | 'pricing_test'
  | 'technical_feasibility'
  | 'competitor_review';

export interface ValidationExperiment {
  id: string;
  idea_id: string;
  validation_question: string;
  hypothesis: string;
  method: ValidationMethod;
  target_participants?: string;
  start_date: string;
  end_date?: string;
  result?: string;
  evidence_refs: string[]; // array of UUIDs
  conclusion?: string;
  next_action?: string;
}

export interface IdeaEvidenceLink {
  record_id: string;
  record_type: 'memory' | 'meeting' | 'person' | 'document' | 'project' | 'venture' | 'decision' | 'validation_note';
  title: string;
  date_recorded: string;
  excerpt?: string;
}

export interface IdeaAIAnalysisResult {
  problem_clarity_score: number;
  solution_viability_score: number;
  target_user_specificity: string;
  strategic_fit_summary: string;
  similar_internal_ideas: Array<{ id: string; title: string; similarity_reason: string; status: IdeaStatus }>;
  major_untested_assumptions: StructuredAssumption[];
  recommended_next_experiment?: Partial<ValidationExperiment>;
  generated_at: string;
  provider: string;
  model: string;
  prompt_version: string;
  citations: Array<{ record_id: string; reason_cited: string }>;
}

export interface Idea {
  id: string;
  user_id: string;
  venture_id?: string | null;
  title: string;
  problem?: string | null;
  solution?: string | null;
  target_users?: string | null;
  market?: string | null;
  potential_score?: number | null; // 1 to 10
  ai_validation_summary?: string | null;
  ai_analysis?: IdeaAIAnalysisResult | null;
  status: IdeaStatus;
  next_steps?: string | null;
  assumptions: StructuredAssumption[];
  experiments: ValidationExperiment[];
  evidence_links: IdeaEvidenceLink[];
  tags: string[];
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
}

export interface CreateIdeaRequest {
  title: string;
  problem?: string;
  solution?: string;
  target_users?: string;
  market?: string;
  venture_id?: string;
  potential_score?: number;
  status?: IdeaStatus;
  assumptions?: StructuredAssumption[];
  next_steps?: string;
  tags?: string[];
  evidence_links?: IdeaEvidenceLink[];
}

export interface UpdateIdeaRequest extends Partial<CreateIdeaRequest> {
  ai_validation_summary?: string;
}

export interface ConvertIdeaToProjectRequest {
  name?: string;
  venture_id?: string;
  description?: string;
  target_date?: string;
  initial_tasks?: Array<{ title: string; priority: 'low' | 'medium' | 'high' | 'urgent' }>;
}

export interface ConvertIdeaToProjectResponse {
  data: {
    new_project_id: string;
    source_idea_id: string;
    idea_status: IdeaStatus;
    converted_at: string;
  };
}

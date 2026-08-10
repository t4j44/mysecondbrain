/**
 * Achievement Portfolio Shared Domain Types & API Contracts
 * Module Owner: Agent 9
 * Strict adherence to evidence-before-claims principles.
 */

export type VerificationStatus = 'self_reported' | 'supported' | 'verified' | 'needs_evidence';

export interface AchievementEvidence {
  id: string;
  achievement_id: string;
  source_id: string;
  source_type: 'project' | 'task' | 'decision' | 'document' | 'meeting' | 'memory' | 'kpi_entry' | 'person' | 'external_url' | 'file';
  source_title: string;
  source_date: string;
  external_url?: string | null;
  notes?: string | null;
  created_at: string;
}

export interface Achievement {
  id: string;
  user_id: string;
  venture_id?: string | null;
  project_id?: string | null;
  title: string;
  role: string;
  description?: string | null;
  problem?: string | null;
  context?: string | null;
  responsibilities: string[];
  actions?: string[];
  impact: string; // Quantitative or explicit qualitative outcome
  skills: string[];
  achievement_date: string; // YYYY-MM-DD
  verification_status: VerificationStatus;
  visibility: 'private' | 'portfolio_ready' | 'public';
  evidence: AchievementEvidence[];
  related_people_ids: string[];
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
}

export interface CreateAchievementRequest {
  title: string;
  role?: string;
  description?: string;
  problem?: string;
  context?: string;
  responsibilities?: string[];
  actions?: string[];
  impact: string;
  skills?: string[];
  achievement_date?: string;
  venture_id?: string;
  project_id?: string;
  visibility?: 'private' | 'portfolio_ready' | 'public';
  evidence_items?: Array<Omit<AchievementEvidence, 'id' | 'achievement_id' | 'created_at'>>;
  related_people_ids?: string[];
}

export interface UpdateAchievementRequest extends Partial<CreateAchievementRequest> {
  verification_status?: VerificationStatus;
}

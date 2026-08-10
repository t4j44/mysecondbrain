/**
 * Portfolio Case Studies Shared Domain Types & API Contracts
 * Module Owner: Agent 9
 */

import { VerificationStatus } from '../achievements';

export type EvidenceCoverageState = 'supported' | 'partially_supported' | 'unsupported';

export interface SectionEvidenceCoverage {
  problem: EvidenceCoverageState;
  role: EvidenceCoverageState;
  responsibilities: EvidenceCoverageState;
  actions: EvidenceCoverageState;
  impact: EvidenceCoverageState;
  skills: EvidenceCoverageState;
}

export interface CaseStudyCitation {
  record_id: string;
  record_type: 'achievement' | 'project' | 'decision' | 'document' | 'kpi_entry';
  claim_supported: string;
  url_or_path: string;
}

export interface PortfolioCaseStudy {
  id: string;
  user_id: string;
  title: string;
  target_role: string; // e.g., 'AI Product Manager', 'Chief Product Officer', 'Founder Profile'
  target_audience?: string | null;
  venture_id?: string | null;
  project_id?: string | null;
  executive_summary: string;
  full_markdown_case: string;
  linked_achievement_ids: string[];
  section_coverage?: SectionEvidenceCoverage;
  citations: CaseStudyCitation[];
  status: 'draft' | 'approved' | 'archived';
  is_public: boolean;
  is_ai_generated: boolean;
  ai_provider?: string | null;
  ai_model?: string | null;
  prompt_version?: string | null;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
}

export interface GenerateCaseStudyRequest {
  target_role: string;
  target_audience?: string;
  selected_achievement_ids: string[];
  selected_project_ids?: string[];
  selected_decision_ids?: string[];
  selected_document_ids?: string[];
  selected_kpi_entry_ids?: string[];
  length?: 'compact' | 'standard' | 'in_depth';
  tone?: string;
}

export interface CreateManualCaseStudyRequest {
  title: string;
  target_role: string;
  target_audience?: string;
  executive_summary: string;
  full_markdown_case: string;
  linked_achievement_ids?: string[];
  venture_id?: string;
  project_id?: string;
  is_public?: boolean;
}

export interface UpdateCaseStudyRequest extends Partial<CreateManualCaseStudyRequest> {
  status?: 'draft' | 'approved' | 'archived';
  is_public?: boolean;
}

/**
 * Life KPI System Shared Domain Types & API Contracts
 * Module Owner: Agent 9
 * Enforces historical integrity and non-vanity calculations.
 */

export type KPICategory = 'founder' | 'network' | 'learning' | 'venture' | string; // allows custom founder KPI definitions
export type KPIPeriod = 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
export type KPIDirection = 'higher_is_better' | 'lower_is_better' | 'milestone';
export type KPITrend = 'increasing' | 'decreasing' | 'stable' | 'insufficient_data';

export interface KPIEvidenceRef {
  record_id: string;
  record_type: 'document' | 'achievement' | 'project' | 'task' | 'interaction';
  title: string;
  url_or_path?: string;
  date_attached: string;
}

export interface KPIEntry {
  id: string;
  user_id: string;
  kpi_id: string;
  recorded_value: number;
  text_value?: string; // for milestone or observational entries
  notes?: string | null;
  recording_date: string; // YYYY-MM-DD
  evidence_refs?: KPIEvidenceRef[];
  created_at: string;
}

export interface KPIDefinition {
  id: string;
  user_id: string;
  category: KPICategory;
  metric_name: string;
  description?: string | null;
  target_value: number;
  current_value: number;
  unit: string;
  period: KPIPeriod;
  direction?: KPIDirection;
  related_venture_id?: string | null;
  related_project_id?: string | null;
  is_active: boolean;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
  
  // Calculated UI attributes
  calculated_progress?: number; // 0 to 100+
  calculated_trend?: KPITrend;
  latest_entries?: KPIEntry[];
}

export interface CreateKPIRequest {
  category: KPICategory;
  metric_name: string;
  description?: string;
  target_value?: number;
  unit?: string;
  period?: KPIPeriod;
  direction?: KPIDirection;
  related_venture_id?: string;
  related_project_id?: string;
  is_active?: boolean;
  notes?: string;
}

export interface UpdateKPIRequest extends Partial<CreateKPIRequest> {
  current_value?: number;
}

export interface CreateKPIEntryRequest {
  recorded_value: number;
  text_value?: string;
  notes?: string;
  recording_date?: string;
  evidence_refs?: KPIEvidenceRef[];
}

export interface KPIDashboardSummary {
  featured_kpis: Array<{
    id: string;
    metric_name: string;
    current_value: number;
    target_value: number;
    unit: string;
    progress_percentage: number;
    trend: KPITrend;
    category: KPICategory;
    last_updated: string;
    is_missing_data: boolean;
  }>;
  total_kpis_tracked: number;
}

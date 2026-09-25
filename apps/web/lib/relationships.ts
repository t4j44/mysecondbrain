export type Evidence = {id: string; kind: string; title: string; uri: string};
export type Recency = {label: string; days_since: number | null; interaction_count: number; explanation: string; rule: string};
export type Followup = {key: string; person_id: string; name: string; why_now: string; context: string; suggested_action: string; evidence: Evidence; due_at: string | null; commitment_id: string | null; recency: Recency};
export type Related = Evidence & {reason: string; evidence: Evidence};
export type Profile = {
  person: Evidence & {name: string; role: string | null; company: string | null; notes: string | null; email: string | null; phone: string | null; linkedin_url: string | null; where_met: string | null; when_met: string | null; industry: string | null; location: string | null; relationship_type: string};
  first_interaction: string | null; last_interaction: string | null; recency: Recency;
  timeline: (Evidence & {date: string; summary: string | null; location: string | null; topics: string[]})[];
  topics: string[]; affiliations: (Evidence & {role: string | null; current: boolean; started_at: string | null; ended_at: string | null})[];
  related: Related[]; commitments: (Evidence & {direction: string; status: string; due_at: string | null})[];
  tasks: (Evidence & {status: string; due_at: string | null})[]; brief: {text: string; evidence: Evidence}[];
  followups: Followup[]; limits: string;
};
export type HomeData = {
  activation: {counts: Record<string, number>; targets: Record<string, number>; activated: boolean; first_activated_at: string | null; successful_actions_last_7_days: number; definition: string; success_definition: string};
  followups: Followup[];
  meetings: (Evidence & {date: string; people: Evidence[]})[];
  projects: (Evidence & {people: {person_id: string; name: string; reason: string; evidence: Evidence}[]})[];
  recent_activity: (Evidence & {date: string; summary: string | null; person_id: string; name: string})[];
  opportunities: {person_id: string; name: string; reason: string; evidence: Evidence; basis: string}[];
  limits: string;
};
export function displayDate(value: string | null) {
  return value ? new Date(value).toLocaleString(undefined, {dateStyle: 'medium', timeStyle: 'short'}) : 'Not recorded';
}

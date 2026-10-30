import { api } from '@/lib/api/browser-client';
import type { Meeting, MeetingList, MeetingUsage, SpeakerMapping, UploadAuthorization } from './types';

/** Domain contract shared by adapters; no Next.js API route required. */
export class MeetingApiClient {
  list(params: Record<string, string | number | undefined> = {}) { return api.get<MeetingList>('/meetings', { params }); }
  get(id: string) { return api.get<Meeting>(`/meetings/${id}`); }
  usage() { return api.get<MeetingUsage>('/meetings/usage'); }
  create(requestId: string, title: string, nonSensitive = false) { return api.post<Meeting>('/meetings/captures', { request_id: requestId, title, meeting_date: new Date().toISOString(), timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || null, recording_permission: true, provider_terms_accepted: true, non_sensitive_recording: nonSensitive }); }
  authorize(id: string, mime: string) { return api.post<UploadAuthorization>(`/meetings/${id}/upload-authorization`, { mime_type: mime }); }
  finalize(id: string) { return api.post<Meeting>(`/meetings/${id}/finalize-upload`, undefined, { timeoutMs: 180000 }); }
  retry(id: string) { return api.post<Meeting>(`/meetings/${id}/retry`); }
  map(id: string, speaker: string, mapping: SpeakerMapping, reviewToken: string) { return api.post<Meeting>(`/meetings/${id}/speakers`, { speaker, ...mapping, confirmed: true, expected_review_token: reviewToken }); }
  confirm(id: string, selections: string[] | undefined, reviewToken: string) { return api.post<Record<string, unknown>>(`/meetings/${id}/confirm`, { confirmed: true, selections: selections ?? null, expected_review_token: reviewToken }); }
  remove(id: string) { return api.delete(`/meetings/${id}`); }
}
export const meetingApi = new MeetingApiClient();

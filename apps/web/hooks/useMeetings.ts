import { useCallback, useEffect, useState } from 'react';
import { meetingApi } from '@/lib/meetings/api';
import { api } from '@/lib/api/browser-client';
import type { Meeting } from '@/lib/meetings/types';
export type { Meeting } from '@/lib/meetings/types';
export interface UseMeetingsParams { venture_id?: string; limit?: number; offset?: number; sort_by?: string; sort_order?: 'asc' | 'desc' }
export function useMeetings(params: UseMeetingsParams = {}) {
  const [meetings, setMeetings] = useState<Meeting[]>([]); const [total, setTotal] = useState(0); const [loading, setLoading] = useState(true); const [error, setError] = useState<string | null>(null);
  const { venture_id, limit, offset, sort_by, sort_order } = params;
  const refetch = useCallback(async () => { try { const result = await meetingApi.list({ venture_id, limit, offset, sort_by, sort_order }); setMeetings(result.items); setTotal(result.total); setError(null); } catch { setError("Couldn't load meetings. Retry."); } finally { setLoading(false); } }, [venture_id, limit, offset, sort_by, sort_order]);
  useEffect(() => { void refetch(); }, [refetch]);
  const processing = meetings.some(m => ['uploaded', 'transcribing', 'extracting'].includes(m.capture?.state || ''));
  useEffect(() => { if (!processing) return; const interval = setInterval(() => { if (!document.hidden) void refetch(); }, 5000); return () => clearInterval(interval); }, [refetch, processing]);
  const createMeeting = async (data: Partial<Meeting>) => { const value = await api.post<Meeting>('/meetings', data); await refetch(); return value; };
  const updateMeeting = async (id: string, data: Partial<Meeting>) => { const value = await api.patch<Meeting>(`/meetings/${id}`, data); await refetch(); return value; };
  return { meetings, total, loading, error, refetch, createMeeting, updateMeeting };
}

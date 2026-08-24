import { createClient } from '@/lib/supabase/client';
import { useState, useEffect, useCallback } from 'react';

export interface Meeting {
  id: string;
  user_id: string;
  venture_id?: string;
  title: string;
  meeting_date: string;
  duration_minutes?: number;
  location?: string;
  recording_url?: string;
  transcript_text?: string;
  ai_summary?: string;
  action_items: string[];
  participant_person_ids: string[];
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface UseMeetingsParams {
  venture_id?: string;
  limit?: number;
  offset?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export function useMeetings(params: UseMeetingsParams = {}) {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMeetings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const queryParams = new URLSearchParams();
      if (params.venture_id) queryParams.append('venture_id', params.venture_id);
      if (params.limit) queryParams.append('limit', String(params.limit));
      if (params.offset) queryParams.append('offset', String(params.offset));
      if (params.sort_by) queryParams.append('sort_by', params.sort_by);
      if (params.sort_order) queryParams.append('sort_order', params.sort_order);

      const { data: { session } } = await createClient().auth.getSession();
      const token = session?.access_token;
      const response = await fetch(`/api/v1/meetings?${queryParams.toString()}`, {
        headers: {
          Authorization: `Bearer ${token || ''}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch meetings: ${response.statusText}`);
      }

      const result = await response.json();
      setMeetings(result.data);
      setTotal(result.pagination?.total || result.data.length);
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, [params.venture_id, params.limit, params.offset, params.sort_by, params.sort_order]);

  useEffect(() => {
    fetchMeetings();
  }, [fetchMeetings]);

  const createMeeting = async (data: Partial<Meeting> & { participant_person_ids?: string[] }) => {
    setError(null);
    try {
      const { data: { session } } = await createClient().auth.getSession();
      const token = session?.access_token;
      const response = await fetch('/api/v1/meetings', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token || ''}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`Failed to create meeting: ${response.statusText}`);
      }

      const result = await response.json();
      setMeetings((prev) => [result.data, ...prev]);
      return result.data;
    } catch (err: any) {
      setError(err.message || 'Failed to create meeting');
      throw err;
    }
  };

  const updateMeeting = async (id: string, data: Partial<Meeting>) => {
    setError(null);
    try {
      const { data: { session } } = await createClient().auth.getSession();
      const token = session?.access_token;
      const response = await fetch(`/api/v1/meetings/${id}`, {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${token || ''}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`Failed to update meeting: ${response.statusText}`);
      }

      const result = await response.json();
      setMeetings((prev) => prev.map((m) => (m.id === id ? result.data : m)));
      return result.data;
    } catch (err: any) {
      setError(err.message || 'Failed to update meeting');
      throw err;
    }
  };

  return { meetings, total, loading, error, refetch: fetchMeetings, createMeeting, updateMeeting };
}


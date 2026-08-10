import { useState, useEffect, useCallback } from 'react';

export interface Memory {
  id: string;
  user_id: string;
  title: string;
  content: string;
  category?: 'reflection' | 'lesson' | 'win' | 'failure' | 'observation' | 'decision_context' | 'quote';
  tags: string[];
  linked_venture_id?: string;
  linked_person_id?: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface UseMemoriesParams {
  category?: string;
  tag?: string;
  linked_venture_id?: string;
  linked_person_id?: string;
  limit?: number;
  offset?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export function useMemories(params: UseMemoriesParams = {}) {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMemories = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const queryParams = new URLSearchParams();
      if (params.category) queryParams.append('category', params.category);
      if (params.tag) queryParams.append('tag', params.tag);
      if (params.linked_venture_id) queryParams.append('linked_venture_id', params.linked_venture_id);
      if (params.linked_person_id) queryParams.append('linked_person_id', params.linked_person_id);
      if (params.limit) queryParams.append('limit', String(params.limit));
      if (params.offset) queryParams.append('offset', String(params.offset));
      if (params.sort_by) queryParams.append('sort_by', params.sort_by);
      if (params.sort_order) queryParams.append('sort_order', params.sort_order);

      const token = localStorage.getItem('supabase_session_token');
      const response = await fetch(`/api/v1/memories?${queryParams.toString()}`, {
        headers: {
          Authorization: `Bearer ${token || ''}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch memories: ${response.statusText}`);
      }

      const result = await response.json();
      setMemories(result.data);
      setTotal(result.pagination?.total || result.data.length);
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, [
    params.category,
    params.tag,
    params.linked_venture_id,
    params.linked_person_id,
    params.limit,
    params.offset,
    params.sort_by,
    params.sort_order,
  ]);

  useEffect(() => {
    fetchMemories();
  }, [fetchMemories]);

  const createMemory = async (data: Partial<Memory>) => {
    setError(null);
    try {
      const token = localStorage.getItem('supabase_session_token');
      const response = await fetch('/api/v1/memories', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token || ''}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`Failed to create memory: ${response.statusText}`);
      }

      const result = await response.json();
      setMemories((prev) => [result.data, ...prev]);
      return result.data;
    } catch (err: any) {
      setError(err.message || 'Failed to create memory');
      throw err;
    }
  };

  const updateMemory = async (id: string, data: Partial<Memory>) => {
    setError(null);
    try {
      const token = localStorage.getItem('supabase_session_token');
      const response = await fetch(`/api/v1/memories/${id}`, {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${token || ''}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`Failed to update memory: ${response.statusText}`);
      }

      const result = await response.json();
      setMemories((prev) => prev.map((m) => (m.id === id ? result.data : m)));
      return result.data;
    } catch (err: any) {
      setError(err.message || 'Failed to update memory');
      throw err;
    }
  };

  return { memories, total, loading, error, refetch: fetchMemories, createMemory, updateMemory };
}

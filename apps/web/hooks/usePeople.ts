import { useState, useEffect, useCallback } from 'react';

export interface Person {
  id: string;
  name: string;
  organization_id?: string;
  role?: string;
  company?: string;
  industry?: string;
  location?: string;
  email?: string;
  phone?: string;
  linkedin_url?: string;
  relationship_type: 'mentor' | 'investor' | 'peer' | 'collaborator' | 'lead' | 'client' | 'contact';
  last_interaction_at?: string;
  notes?: string;
  tags: string[];
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface UsePeopleParams {
  q?: string;
  relationship_type?: string;
  tag?: string;
  limit?: number;
  offset?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export function usePeople(params: UsePeopleParams = {}) {
  const [people, setPeople] = useState<Person[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPeople = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const queryParams = new URLSearchParams();
      if (params.q) queryParams.append('q', params.q);
      if (params.relationship_type) queryParams.append('relationship_type', params.relationship_type);
      if (params.tag) queryParams.append('tag', params.tag);
      if (params.limit) queryParams.append('limit', String(params.limit));
      if (params.offset) queryParams.append('offset', String(params.offset));
      if (params.sort_by) queryParams.append('sort_by', params.sort_by);
      if (params.sort_order) queryParams.append('sort_order', params.sort_order);

      const token = localStorage.getItem('supabase_session_token');
      const response = await fetch(`/api/v1/people?${queryParams.toString()}`, {
        headers: {
          Authorization: `Bearer ${token || ''}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch people: ${response.statusText}`);
      }

      const result = await response.json();
      setPeople(result.data);
      setTotal(result.pagination?.total || result.data.length);
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, [params.q, params.relationship_type, params.tag, params.limit, params.offset, params.sort_by, params.sort_order]);

  useEffect(() => {
    fetchPeople();
  }, [fetchPeople]);

  const createPerson = async (data: Partial<Person>) => {
    setError(null);
    try {
      const token = localStorage.getItem('supabase_session_token');
      const response = await fetch('/api/v1/people', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token || ''}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`Creation failed: ${response.statusText}`);
      }

      const result = await response.json();
      setPeople((prev) => [result.data, ...prev]);
      return result.data;
    } catch (err: any) {
      setError(err.message || 'Failed to create person');
      throw err;
    }
  };

  const updatePerson = async (id: string, data: Partial<Person>) => {
    setError(null);
    try {
      const token = localStorage.getItem('supabase_session_token');
      const response = await fetch(`/api/v1/people/${id}`, {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${token || ''}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`Update failed: ${response.statusText}`);
      }

      const result = await response.json();
      setPeople((prev) => prev.map((p) => (p.id === id ? result.data : p)));
      return result.data;
    } catch (err: any) {
      setError(err.message || 'Failed to update person');
      throw err;
    }
  };

  return { people, total, loading, error, refetch: fetchPeople, createPerson, updatePerson };
}

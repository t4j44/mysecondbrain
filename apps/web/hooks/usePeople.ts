'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api/browser-client';
import { ApiError } from '@/lib/api/errors';
import { toApiError } from '@/lib/api/format-error';
import type { ListResponse, Person, PersonCreateInput } from '@/lib/api/domains';

export type { Person, PersonCreateInput };

export function usePeople() {
  const [people, setPeople] = useState<Person[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<ListResponse<Person>>('/people', { params: { limit: 100 } });
      setPeople(res.items ?? []);
      setTotal(res.total ?? 0);
    } catch (err) {
      setError(toApiError(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refetch();
  }, [refetch]);

  const createPerson = async (data: PersonCreateInput) => {
    setError(null);
    try {
      const created = await api.post<Person>('/people', data);
      setPeople((prev) => [created, ...prev]);
      setTotal((t) => t + 1);
      return created;
    } catch (err) {
      const apiErr = toApiError(err);
      setError(apiErr);
      throw apiErr;
    }
  };

  const updatePerson = async (id: string, data: Partial<Person>) => {
    setError(null);
    try {
      const updated = await api.patch<Person>(`/people/${id}`, data);
      setPeople((prev) => prev.map((p) => (p.id === id ? updated : p)));
      return updated;
    } catch (err) {
      const apiErr = toApiError(err);
      setError(apiErr);
      throw apiErr;
    }
  };

  const deletePerson = async (id: string) => {
    setError(null);
    try {
      await api.delete(`/people/${id}`);
      setPeople((prev) => prev.filter((p) => p.id !== id));
      setTotal((t) => Math.max(0, t - 1));
    } catch (err) {
      const apiErr = toApiError(err);
      setError(apiErr);
      throw apiErr;
    }
  };

  const getPerson = async (id: string) => {
    setError(null);
    try {
      return await api.get<Person>(`/people/${id}`);
    } catch (err) {
      const apiErr = toApiError(err);
      setError(apiErr);
      throw apiErr;
    }
  };

  return {
    people,
    total,
    loading,
    error,
    refetch,
    createPerson,
    updatePerson,
    deletePerson,
    getPerson,
  };
}

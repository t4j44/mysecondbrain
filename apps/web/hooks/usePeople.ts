'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '@/lib/api/browser-client';
import { ApiError } from '@/lib/api/errors';
import { toApiError } from '@/lib/api/format-error';
import type { ListResponse, Person, PersonCreateInput } from '@/lib/api/domains';

export type { Person, PersonCreateInput };

type PeopleOptions = {
  search?: string;
  tag?: string;
  pageSize?: number;
};

export function usePeople({ search = '', tag = 'all', pageSize = 100 }: PeopleOptions = {}) {
  const [people, setPeople] = useState<Person[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const requestVersion = useRef(0);

  const params = useCallback((offset: number) => ({
    limit: pageSize,
    offset,
    ...(search.trim() ? { q: search.trim() } : {}),
    ...(tag !== 'all' ? { relationship_type: tag } : {}),
  }), [pageSize, search, tag]);

  const refetch = useCallback(async () => {
    const current = ++requestVersion.current;
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<ListResponse<Person>>('/people', { params: params(0) });
      if (current !== requestVersion.current) return;
      setPeople(res.items ?? []);
      setTotal(res.total ?? 0);
    } catch (err) {
      if (current === requestVersion.current) setError(toApiError(err));
    } finally {
      if (current === requestVersion.current) setLoading(false);
    }
  }, [params]);

  useEffect(() => {
    void refetch();
    return () => { requestVersion.current++; };
  }, [refetch]);

  const loadMore = useCallback(async () => {
    if (loading || loadingMore || people.length >= total) return;
    const current = requestVersion.current;
    setLoadingMore(true);
    try {
      const res = await api.get<ListResponse<Person>>('/people', { params: params(people.length) });
      if (current !== requestVersion.current) return;
      setPeople((prev) => {
        const seen = new Set(prev.map((p) => p.id));
        return [...prev, ...(res.items ?? []).filter((p) => !seen.has(p.id))];
      });
      setTotal(res.total ?? total);
    } catch (err) {
      if (current === requestVersion.current) setError(toApiError(err));
    } finally {
      if (current === requestVersion.current) setLoadingMore(false);
    }
  }, [loading, loadingMore, people.length, total, params]);

  const createPerson = async (data: PersonCreateInput) => {
    setError(null);
    try {
      const created = await api.post<Person>('/people', data);
      await refetch();
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
    people, total, loading, loadingMore, hasMore: people.length < total,
    error, refetch, loadMore, createPerson, updatePerson, deletePerson, getPerson,
  };
}

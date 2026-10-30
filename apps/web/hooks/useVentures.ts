'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api/browser-client';
import { ApiError } from '@/lib/api/errors';
import { toApiError } from '@/lib/api/format-error';
import type { ListResponse, Venture, VentureCreateInput } from '@/lib/api/domains';

export function useVentures() {
  const [ventures, setVentures] = useState<Venture[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<ListResponse<Venture>>('/ventures', { params: { limit: 100 } });
      setVentures(res.items ?? []);
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

  const createVenture = async (data: VentureCreateInput) => {
    setError(null);
    try {
      const created = await api.post<Venture>('/ventures', data);
      setVentures((prev) => [created, ...prev]);
      setTotal((t) => t + 1);
      return created;
    } catch (err) {
      const apiErr = toApiError(err);
      setError(apiErr);
      throw apiErr;
    }
  };

  const updateVenture = async (id: string, data: Partial<Venture>) => {
    setError(null);
    try {
      const updated = await api.patch<Venture>(`/ventures/${id}`, data);
      setVentures((prev) => prev.map((v) => (v.id === id ? updated : v)));
      return updated;
    } catch (err) {
      const apiErr = toApiError(err);
      setError(apiErr);
      throw apiErr;
    }
  };

  const deleteVenture = async (id: string) => {
    setError(null);
    try {
      await api.delete(`/ventures/${id}`);
      setVentures((prev) => prev.filter((v) => v.id !== id));
      setTotal((t) => Math.max(0, t - 1));
    } catch (err) {
      const apiErr = toApiError(err);
      setError(apiErr);
      throw apiErr;
    }
  };

  return { ventures, total, loading, error, refetch, createVenture, updateVenture, deleteVenture };
}

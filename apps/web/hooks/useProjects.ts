'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api/browser-client';
import { ApiError } from '@/lib/api/errors';
import { toApiError } from '@/lib/api/format-error';
import type { ListResponse, Project, ProjectCreateInput } from '@/lib/api/domains';

export interface UseProjectsParams {
  ventureId?: string;
}

export function useProjects(params: UseProjectsParams = {}) {
  const { ventureId } = params;
  const [projects, setProjects] = useState<Project[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const queryParams: Record<string, string | number> = { limit: 100 };
      if (ventureId) {
        queryParams.venture_id = ventureId;
      }
      const res = await api.get<ListResponse<Project>>('/projects', { params: queryParams });
      setProjects(res.items ?? []);
      setTotal(res.total ?? 0);
    } catch (err) {
      setError(toApiError(err));
    } finally {
      setLoading(false);
    }
  }, [ventureId]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  const createProject = async (data: ProjectCreateInput) => {
    setError(null);
    try {
      const created = await api.post<Project>('/projects', data);
      setProjects((prev) => [created, ...prev]);
      setTotal((t) => t + 1);
      return created;
    } catch (err) {
      const apiErr = toApiError(err);
      setError(apiErr);
      throw apiErr;
    }
  };

  const updateProject = async (id: string, data: Partial<Project>) => {
    setError(null);
    try {
      const updated = await api.patch<Project>(`/projects/${id}`, data);
      setProjects((prev) => prev.map((p) => (p.id === id ? updated : p)));
      return updated;
    } catch (err) {
      const apiErr = toApiError(err);
      setError(apiErr);
      throw apiErr;
    }
  };

  const deleteProject = async (id: string) => {
    setError(null);
    try {
      await api.delete(`/projects/${id}`);
      setProjects((prev) => prev.filter((p) => p.id !== id));
      setTotal((t) => Math.max(0, t - 1));
    } catch (err) {
      const apiErr = toApiError(err);
      setError(apiErr);
      throw apiErr;
    }
  };

  return { projects, total, loading, error, refetch, createProject, updateProject, deleteProject };
}

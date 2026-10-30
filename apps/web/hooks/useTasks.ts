'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api/browser-client';
import { ApiError } from '@/lib/api/errors';
import { toApiError } from '@/lib/api/format-error';
import type { ListResponse, Task, TaskCreateInput, TaskStatusFilter } from '@/lib/api/domains';

export interface UseTasksParams {
  status?: TaskStatusFilter;
}

export function useTasks(params: UseTasksParams = {}) {
  const { status = 'all' } = params;
  const [tasks, setTasks] = useState<Task[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const queryParams: Record<string, string | number> = { limit: 100 };
      if (status !== 'all') {
        queryParams.status = status;
      }
      const res = await api.get<ListResponse<Task>>('/tasks', { params: queryParams });
      setTasks(res.items ?? []);
      setTotal(res.total ?? 0);
    } catch (err) {
      setError(toApiError(err));
    } finally {
      setLoading(false);
    }
  }, [status]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  const createTask = async (data: TaskCreateInput) => {
    setError(null);
    try {
      const created = await api.post<Task>('/tasks', { status: 'todo', priority: 'medium', ...data });
      if (status === 'all' || status === 'todo') {
        setTasks((prev) => [created, ...prev]);
        setTotal((t) => t + 1);
      }
      return created;
    } catch (err) {
      const apiErr = toApiError(err);
      setError(apiErr);
      throw apiErr;
    }
  };

  const updateTask = async (id: string, data: Partial<Task>) => {
    setError(null);
    try {
      const updated = await api.patch<Task>(`/tasks/${id}`, data);
      setTasks((prev) => {
        const filtered =
          status === 'all' || updated.status === status
            ? prev.map((t) => (t.id === id ? updated : t))
            : prev.filter((t) => t.id !== id);
        return filtered;
      });
      return updated;
    } catch (err) {
      const apiErr = toApiError(err);
      setError(apiErr);
      throw apiErr;
    }
  };

  const deleteTask = async (id: string) => {
    setError(null);
    try {
      await api.delete(`/tasks/${id}`);
      setTasks((prev) => prev.filter((t) => t.id !== id));
      setTotal((t) => Math.max(0, t - 1));
    } catch (err) {
      const apiErr = toApiError(err);
      setError(apiErr);
      throw apiErr;
    }
  };

  return { tasks, total, loading, error, refetch, createTask, updateTask, deleteTask };
}

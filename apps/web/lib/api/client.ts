import { env } from '@/lib/env';
import { ApiError } from './errors';
import type { HttpMethod, RequestOptions } from './types';
import type { ApiResponse } from '@second-brain/shared-types';

export class FastApiClient {
  private baseUrl: string;
  private getToken: string | (() => string | null | Promise<string | null>);

  constructor(getToken: string | (() => string | null | Promise<string | null>), baseUrl?: string) {
    this.baseUrl = baseUrl || env.NEXT_PUBLIC_API_BASE_URL;
    this.getToken = getToken;
  }

  private async request<T>(endpoint: string, method: HttpMethod, options: RequestOptions = {}): Promise<T> {
    const { params, body, headers = {}, timeoutMs = 15000, ...fetchOptions } = options;
    const base = this.baseUrl.replace(/\/$/, '');
    const path = base.endsWith('/api/v1') ? endpoint.replace(/^\/?api\/v1\/?/, '') : endpoint;
    const url = new URL(`${base}/${path.replace(/^\//, '')}`);

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value));
        }
      });
    }

    const token = typeof this.getToken === 'function' ? await this.getToken() : this.getToken;
    const requestHeaders: Record<string, string> = {
      'Accept': 'application/json',
      ...headers,
    };

    if (body !== undefined && !(body instanceof FormData)) {
      requestHeaders['Content-Type'] = 'application/json';
    }

    if (token) {
      requestHeaders['Authorization'] = `Bearer ${token}`;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(url.toString(), {
        method,
        headers: requestHeaders,
        body: body !== undefined ? (body instanceof FormData ? body : JSON.stringify(body)) : undefined,
        signal: controller.signal,
        ...fetchOptions,
      });

      clearTimeout(timeoutId);

      // Handle empty successful responses
      if (response.status === 204) {
        return {} as T;
      }

      const contentType = response.headers.get('content-type');
      let data: any;
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        data = await response.text();
      }

      if (!response.ok) {
        throw ApiError.fromResponse(response.status, data);
      }

      // Automatically unwrap standard ApiResponse payload wrappers if present
      if (data && typeof data === 'object') {
        if ('data' in data && 'pagination' in data) {
          return data as T;
        }
        if ('data' in data && Object.keys(data).length <= 2) {
          return (data as ApiResponse<T>).data;
        }
      }

      return data as T;
    } catch (error: any) {
      clearTimeout(timeoutId);
      if (error instanceof ApiError) {
        throw error;
      }
      if (error.name === 'AbortError') {
        throw new ApiError(408, { code: 'TIMEOUT_ERROR', message: 'The backend request exceeded the timeout duration.' });
      }
      throw new ApiError(500, { code: 'NETWORK_ERROR', message: error.message || 'Network connectivity communication failure.' });
    }
  }

  public get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, 'GET', options);
  }

  public post<T>(endpoint: string, body?: unknown, options?: Omit<RequestOptions, 'body'>): Promise<T> {
    return this.request<T>(endpoint, 'POST', { ...options, body });
  }

  public put<T>(endpoint: string, body?: unknown, options?: Omit<RequestOptions, 'body'>): Promise<T> {
    return this.request<T>(endpoint, 'PUT', { ...options, body });
  }

  public patch<T>(endpoint: string, body?: unknown, options?: Omit<RequestOptions, 'body'>): Promise<T> {
    return this.request<T>(endpoint, 'PATCH', { ...options, body });
  }

  public delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, 'DELETE', options);
  }
}

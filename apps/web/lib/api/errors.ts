import type { ApiErrorDetail } from '@second-brain/shared-types';

export class ApiError extends Error {
  public readonly code: string;
  public readonly status: number;
  public readonly details?: unknown;
  public readonly requestId?: string;

  constructor(status: number, detail: ApiErrorDetail | string) {
    if (typeof detail === 'string') {
      super(detail);
      this.code = 'UNKNOWN_ERROR';
      this.status = status;
    } else {
      super(detail.message);
      this.code = detail.code || 'API_ERROR';
      this.status = status;
      this.details = detail.details;
      this.requestId = detail.request_id;
    }
    this.name = 'ApiError';
  }

  public static fromResponse(status: number, data: unknown): ApiError {
    if (data && typeof data === 'object' && 'error' in data) {
      const errorObj = (data as { error: ApiErrorDetail }).error;
      return new ApiError(status, errorObj);
    }
    return new ApiError(status, `Request failed with HTTP status code ${status}`);
  }
}

import { ApiError } from './errors';

export function formatApiError(err: unknown): string {
  if (err instanceof ApiError) {
    switch (err.status) {
      case 401:
        return 'Your session expired. Please sign in again.';
      case 403:
        return err.message || 'You do not have permission for this action.';
      case 404:
        return 'Record not found. It may have been archived or deleted.';
      case 409:
        return err.message || 'This record conflicts with an existing one.';
      case 422:
      case 400:
        return err.message || 'Validation failed. Check your input.';
      default:
        if (err.status >= 500) {
          return `Server error (${err.status}): ${err.message}`;
        }
        return err.message;
    }
  }
  if (err instanceof Error) {
    return err.message;
  }
  return 'An unexpected error occurred.';
}

export function toApiError(err: unknown): ApiError {
  if (err instanceof ApiError) {
    return err;
  }
  return new ApiError(500, {
    code: 'UNKNOWN_ERROR',
    message: formatApiError(err),
  });
}

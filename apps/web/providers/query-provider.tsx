'use client';

import * as React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ApiError } from '@/lib/api/errors';

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = React.useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Safe retries: retry idempotent network hiccups up to 2 times, never retry 401/403/404 or validation errors
            retry: (failureCount, error) => {
              if (error instanceof ApiError) {
                if (error.status === 401 || error.status === 403 || error.status >= 400 && error.status < 500) {
                  return false;
                }
              }
              return failureCount < 2;
            },
            staleTime: 60 * 1000, // 1 minute default stale time for dashboard metrics
            refetchOnWindowFocus: false,
          },
          mutations: {
            // Zero automatic retries on mutations to protect idempotency boundaries
            retry: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}

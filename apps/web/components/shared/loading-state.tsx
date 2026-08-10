import * as React from 'react';
import { Skeleton } from '@/components/ui/skeleton';

interface LoadingStateProps {
  rows?: number;
  showHeader?: boolean;
}

export function LoadingState({ rows = 3, showHeader = true }: LoadingStateProps) {
  return (
    <div className="space-y-6 my-4 w-full">
      {showHeader && (
        <div className="flex items-center justify-between border-b border-border/40 pb-4">
          <div className="space-y-2">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-4 w-96 max-w-full" />
          </div>
          <Skeleton className="h-10 w-32" />
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {Array.from({ length: rows }).map((_, index) => (
          <div key={index} className="rounded-lg border border-border bg-[#0a0510] p-6 space-y-4">
            <div className="flex items-center justify-between">
              <Skeleton className="h-5 w-24" />
              <Skeleton className="h-6 w-6 rounded-full" />
            </div>
            <Skeleton className="h-6 w-3/4" />
            <Skeleton className="h-12 w-full" />
            <div className="pt-2 border-t border-border/30 flex justify-between">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-20" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

import * as React from 'react';
import { cn } from '@/lib/utils';

export function ResponsivePageContainer({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("mx-auto w-full min-w-0 max-w-7xl space-y-5", className)}>
      {children}
    </div>
  );
}

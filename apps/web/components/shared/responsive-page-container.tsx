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
    <div className={cn("mx-auto max-w-7xl w-full px-2 sm:px-4 md:px-6 py-4 transition-all", className)}>
      {children}
    </div>
  );
}

import * as React from 'react';
import { cn } from '@/lib/utils';

interface SectionHeaderProps {
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function SectionHeader({ title, description, action, className }: SectionHeaderProps) {
  return (
    <div className={cn("my-6 flex items-center justify-between border-b border-border/40 pb-3", className)}>
      <div>
        <h2 className="text-lg sm:text-xl font-bold tracking-tight text-[#f7f4ea]">
          {title}
        </h2>
        {description && (
          <p className="text-xs text-muted-foreground mt-0.5">
            {description}
          </p>
        )}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}

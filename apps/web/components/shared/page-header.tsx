import * as React from 'react';
import { cn } from '@/lib/utils';

interface PageHeaderProps {
  title: string;
  description?: string;
  badge?: string;
  actions?: React.ReactNode;
  className?: string;
}

export function PageHeader({ title, description, badge, actions, className }: PageHeaderProps) {
  return (
    <div className={cn("mb-5 flex min-w-0 flex-wrap items-start justify-between gap-4", className)}>
      <div className="min-w-0 max-w-2xl space-y-1.5">
        <div className="flex flex-wrap items-center gap-2.5">
          <h1 className="text-[25px] leading-tight sm:text-3xl font-semibold tracking-tight text-foreground">
            {title}
          </h1>
          {badge && (
            <span className="inline-flex items-center rounded px-2 py-0.5 text-xs font-mono font-bold bg-[#251238] text-[#00ff9d] border border-[#00ff9d]/40 uppercase">
              {badge}
            </span>
          )}
        </div>
        {description && (
          <p className="text-sm text-muted-foreground leading-relaxed">
            {description}
          </p>
        )}
      </div>
      {actions && (
        <div className="flex max-w-full flex-wrap items-center gap-3">
          {actions}
        </div>
      )}
    </div>
  );
}

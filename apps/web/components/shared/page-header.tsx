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
    <div className={cn("mb-8 flex flex-col space-y-4 md:flex-row md:items-center md:justify-between md:space-y-0 border-b border-border/60 pb-6", className)}>
      <div className="space-y-1.5 max-w-2xl">
        <div className="flex items-center space-x-2.5">
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#f7f4ea]">
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
        <div className="flex items-center space-x-3 shrink-0">
          {actions}
        </div>
      )}
    </div>
  );
}

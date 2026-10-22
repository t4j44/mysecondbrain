import * as React from 'react';
import Link from 'next/link';
import { Terminal, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface EmptyStateProps {
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  actionHref?: string;
  icon?: React.ElementType;
}

export function EmptyState({
  title = 'No records saved yet',
  description = 'Add a record to keep useful context here.',
  actionLabel,
  onAction,
  actionHref,
  icon: Icon = Terminal,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed bg-card p-4 text-center my-5 sm:p-8">
      <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-[#251238] border border-[#00ff9d]/40 text-[#00ff9d] mb-5 shadow-[0_0_20px_rgba(0,255,157,0.15)]">
        <Icon className="h-7 w-7" />
      </div>
      
      <h2 className="text-lg font-semibold max-w-sm">
        {title}
      </h2>
      
      <p className="mt-2 text-base text-muted-foreground max-w-md leading-relaxed mb-4">
        {description}
      </p>

      {actionLabel && actionHref ? <Button asChild><Link href={actionHref}>{actionLabel}</Link></Button> : actionLabel && onAction && (
        <Button onClick={onAction} variant="default">
          <Plus className="mr-2 h-4 w-4" />
          {actionLabel}
        </Button>
      )}
    </div>
  );
}

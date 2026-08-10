import * as React from 'react';
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
  title = 'No Records Found',
  description = 'This venture feature vault currently holds zero populated entities in the database.',
  actionLabel,
  onAction,
  icon: Icon = Terminal,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-[#3b1e5a] bg-[#0c0614]/60 p-12 text-center shadow-[0_4px_20px_rgba(0,0,0,0.3)] my-8">
      <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-[#251238] border border-[#00ff9d]/40 text-[#00ff9d] mb-5 shadow-[0_0_20px_rgba(0,255,157,0.15)]">
        <Icon className="h-7 w-7" />
      </div>
      
      <h3 className="text-lg font-bold text-[#f7f4ea] max-w-sm">
        {title}
      </h3>
      
      <p className="mt-2 text-xs font-sans text-muted-foreground max-w-md leading-relaxed mb-6">
        {description}
      </p>

      {actionLabel && onAction && (
        <Button onClick={onAction} variant="default" className="font-mono text-xs font-semibold uppercase tracking-wider">
          <Plus className="mr-2 h-4 w-4" />
          {actionLabel}
        </Button>
      )}
    </div>
  );
}

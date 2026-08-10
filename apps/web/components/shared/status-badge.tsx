import * as React from 'react';
import { Badge } from '@/components/ui/badge';
import type { TaskStatus, VentureStatus, ProjectStatus, IdeaStatus, ContentStatus } from '@second-brain/shared-types';

type AnyStatus = TaskStatus | VentureStatus | ProjectStatus | IdeaStatus | ContentStatus | string;

export function StatusBadge({ status }: { status: AnyStatus }) {
  const lower = status.toLowerCase();

  if (lower === 'active' || lower === 'in_progress' || lower === 'published' || lower === 'executing') {
    return <Badge variant="default" className="text-[#00ff9d] bg-[#00ff9d]/15 border-[#00ff9d]/40 font-mono text-[10px]">{status}</Badge>;
  }

  if (lower === 'done' || lower === 'completed' || lower === 'converted') {
    return <Badge variant="default" className="text-[#00ff9d] bg-[#00ff9d]/20 border-[#00ff9d] font-bold font-mono text-[10px]">✓ {status}</Badge>;
  }

  if (lower === 'planning' || lower === 'validating' || lower === 'review') {
    return <Badge variant="purple" className="font-mono text-[10px]">{status}</Badge>;
  }

  if (lower === 'paused' || lower === 'on_hold') {
    return <Badge variant="outline" className="text-[#ffb800] border-[#ffb800]/50 bg-[#281c04] font-mono text-[10px]">{status}</Badge>;
  }

  if (lower === 'cancelled' || lower === 'failed' || lower === 'exited') {
    return <Badge variant="destructive" className="font-mono text-[10px]">{status}</Badge>;
  }

  return <Badge variant="outline" className="text-muted-foreground font-mono text-[10px]">{status}</Badge>;
}

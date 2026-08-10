import * as React from 'react';
import { Badge } from '@/components/ui/badge';
import type { TaskPriority } from '@second-brain/shared-types';

export function PriorityBadge({ priority }: { priority: TaskPriority | string }) {
  const lower = priority.toLowerCase();

  switch (lower) {
    case 'urgent':
      return (
        <Badge variant="destructive" className="animate-pulse-slow font-mono text-[10px] font-bold tracking-widest bg-red-600/30 text-red-200 border-red-500">
          ! {priority}
        </Badge>
      );
    case 'high':
      return (
        <Badge variant="default" className="text-[#ffb800] bg-[#2d2008] border-[#ffb800]/50 font-mono text-[10px]">
          ▲ {priority}
        </Badge>
      );
    case 'medium':
      return (
        <Badge variant="purple" className="font-mono text-[10px]">
          ▪ {priority}
        </Badge>
      );
    case 'low':
      return (
        <Badge variant="outline" className="text-muted-foreground border-border font-mono text-[10px]">
          ▽ {priority}
        </Badge>
      );
    default:
      return <Badge variant="outline" className="font-mono text-[10px]">{priority}</Badge>;
  }
}

'use client';

import React, { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import LayoutShell from '../../components/layout/Sidebar';
import TaskManager from '../../components/tasks/TaskManager';

function TasksContent() {
  const searchParams = useSearchParams();
  const filterParam = searchParams.get('filter') || 'all';
  
  const validFilters = ['all', 'today', 'upcoming', 'completed'] as const;
  const filter = validFilters.includes(filterParam as any) ? (filterParam as any) : 'all';

  return <TaskManager key={filter} initialView={filter} />;
}

export default function TasksPage() {
  return (
    <LayoutShell>
      <Suspense fallback={<div className="font-mono text-xs text-terminal-muted animate-pulse font-semibold">Loading task parameters...</div>}>
        <TasksContent />
      </Suspense>
    </LayoutShell>
  );
}

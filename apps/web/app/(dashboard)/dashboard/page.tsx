'use client';

import * as React from 'react';
import { ResponsivePageContainer } from '@/components/shared/responsive-page-container';
import { PageHeader } from '@/components/shared/page-header';
import { EmptyState } from '@/components/shared/empty-state';
import { AIInsightPanel } from '@/components/shared/ai-insight-panel';
import { LayoutDashboard } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useRouter } from 'next/navigation';

export default function DashboardPage() {
  const router = useRouter();

  return (
    <ResponsivePageContainer>
      <PageHeader
        title="Command Center"
        description="High-velocity executive oversight across all your active ventures and network tasks."
        badge="SYSTEM ONLINE"
        actions={
          <Button onClick={() => router.push('/tasks')} variant="terminal" className="text-xs">
            NEW TASK ENTRY
          </Button>
        }
      />

      <AIInsightPanel
        title="FOUNDER MORNING BRIEFING"
        insight="Welcome back to your terminal. Vector semantic checks indicate 2 critical follow-up items due for your active venture pipeline. No anomalies detected in RLS security policies."
        confidence={98}
        sourceCount={4}
      />

      <EmptyState
        icon={LayoutDashboard}
        title="Venture Telemetry Waiting for Input"
        description="Agent 5 (Founder Execution Layer) will populate real-time interactive KPI widgets and risk matrices in this view."
        actionLabel="EXPLORE TASK ENGINE"
        onAction={() => router.push('/tasks')}
      />
    </ResponsivePageContainer>
  );
}

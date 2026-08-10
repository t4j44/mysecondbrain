'use client';

import * as React from 'react';
import { ResponsivePageContainer } from '@/components/shared/responsive-page-container';
import { PageHeader } from '@/components/shared/page-header';
import { EmptyState } from '@/components/shared/empty-state';
import { LineChart } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';

export default function KpisPage() {
  const { toast } = useToast();

  return (
    <ResponsivePageContainer>
      <PageHeader
        title="Life & Founder KPIs"
        description="Quantified personal metrics and executive health indicators tracked across custom periodic targets."
        badge="ANALYTICS"
        actions={
          <Button onClick={() => toast({ title: 'KPI STUB', description: 'Agent 8 will implement automated metric trending here.' })} className="font-mono text-xs">
            + DEFINE METRIC
          </Button>
        }
      />

      <EmptyState
        icon={LineChart}
        title="No KPI Definitions Configured"
        description="Track personal habits, sleep scores, or venture milestones with automated trend graphs."
        actionLabel="CREATE NEW METRIC"
        onAction={() => toast({ title: 'READY FOR AGENT 8', description: 'Founder Growth Engines scheduled for Agent 8.' })}
      />
    </ResponsivePageContainer>
  );
}

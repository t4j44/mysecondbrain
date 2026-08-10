'use client';

import * as React from 'react';
import { ResponsivePageContainer } from '@/components/shared/responsive-page-container';
import { PageHeader } from '@/components/shared/page-header';
import { EmptyState } from '@/components/shared/empty-state';
import { Lightbulb } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';

export default function IdeasPage() {
  const { toast } = useToast();

  return (
    <ResponsivePageContainer>
      <PageHeader
        title="Idea Incubator"
        description="Capture early-stage hypotheses and submit them to proactive AI validation summaries."
        badge="INCUBATOR"
        actions={
          <Button onClick={() => toast({ title: 'IDEA INCUBATOR STUB', description: 'Agent 8 will implement AI idea scoring here.' })} className="font-mono text-xs">
            + LOG HYPOTHESIS
          </Button>
        }
      />

      <EmptyState
        icon={Lightbulb}
        title="No Ideas Registered in Vault"
        description="Capture spontaneous insights before they evaporate. AI validation agents will rank market viability."
        actionLabel="CAPTURE IDEA"
        onAction={() => toast({ title: 'READY FOR AGENT 8', description: 'Idea Validation incubator assigned to Agent 8.' })}
      />
    </ResponsivePageContainer>
  );
}

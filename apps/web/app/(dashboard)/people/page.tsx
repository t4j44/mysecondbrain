'use client';

import * as React from 'react';
import { ResponsivePageContainer } from '@/components/shared/responsive-page-container';
import { PageHeader } from '@/components/shared/page-header';
import { EmptyState } from '@/components/shared/empty-state';
import { Users } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';

export default function PeoplePage() {
  const { toast } = useToast();

  return (
    <ResponsivePageContainer>
      <PageHeader
        title="People & CRM Network"
        description="Relationship intelligence connecting mentors, investors, peers, and collaborators with context timeline history."
        badge="NETWORK"
        actions={
          <Button onClick={() => toast({ title: 'CRM STUB', description: 'Agent 6 will connect CRM contact profiles here.' })} className="font-mono text-xs">
            + ADD CONTACT
          </Button>
        }
      />

      <EmptyState
        icon={Users}
        title="Your Network CRM Directory is Empty"
        description="Agent 6 (Network Intelligence) will populate rich interaction timelines and AI contact summaries here."
        actionLabel="ADD FIRST CONTACT"
        onAction={() => toast({ title: 'READY FOR AGENT 6', description: 'Network Intelligence CRM implementation arriving next.' })}
      />
    </ResponsivePageContainer>
  );
}

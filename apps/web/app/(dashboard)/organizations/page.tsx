'use client';

import * as React from 'react';
import { ResponsivePageContainer } from '@/components/shared/responsive-page-container';
import { PageHeader } from '@/components/shared/page-header';
import { EmptyState } from '@/components/shared/empty-state';
import { Building2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';

export default function OrganizationsPage() {
  const { toast } = useToast();

  return (
    <ResponsivePageContainer>
      <PageHeader
        title="Organization Directory"
        description="Corporate entities and fund structures linked to your individual CRM contacts."
        badge="ENTITIES"
        actions={
          <Button onClick={() => toast({ title: 'ORG STUB', description: 'Agent 6 will enable corporate directory mapping here.' })} className="font-mono text-xs">
            + REGISTER ORG
          </Button>
        }
      />

      <EmptyState
        icon={Building2}
        title="No Organizations Recorded"
        description="Link individual people and interaction records directly to their affiliated company entities."
        actionLabel="REGISTER FIRST ORG"
        onAction={() => toast({ title: 'READY FOR AGENT 6', description: 'Organization directory assigned to Agent 6.' })}
      />
    </ResponsivePageContainer>
  );
}

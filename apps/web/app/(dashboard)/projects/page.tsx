'use client';

import * as React from 'react';
import { ResponsivePageContainer } from '@/components/shared/responsive-page-container';
import { PageHeader } from '@/components/shared/page-header';
import { EmptyState } from '@/components/shared/empty-state';
import { FolderKanban } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';

export default function ProjectsPage() {
  const { toast } = useToast();

  return (
    <ResponsivePageContainer>
      <PageHeader
        title="Project Portfolio"
        description="Target-date driven operational milestones nested inside your respective ventures."
        badge="PROJECTS"
        actions={
          <Button onClick={() => toast({ title: 'PROJECT STUB', description: 'Project management board arriving with Agent 5.' })} className="font-mono text-xs">
            + NEW PROJECT
          </Button>
        }
      />

      <EmptyState
        icon={FolderKanban}
        title="No Active Projects Tracked"
        description="Projects bridge high-level venture visions with actionable task execution items."
        actionLabel="INITIALIZE PROJECT"
        onAction={() => toast({ title: 'READY FOR AGENT 5', description: 'Project domain forms arriving in next phase.' })}
      />
    </ResponsivePageContainer>
  );
}

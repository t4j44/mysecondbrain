'use client';

import * as React from 'react';
import { ResponsivePageContainer } from '@/components/shared/responsive-page-container';
import { PageHeader } from '@/components/shared/page-header';
import { EmptyState } from '@/components/shared/empty-state';
import { FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';

export default function ContentPage() {
  const { toast } = useToast();

  return (
    <ResponsivePageContainer>
      <PageHeader
        title="AI Content Synthesis Engine"
        description="Transform internal memories, achievements, and meetings into thought leadership updates and LinkedIn posts."
        badge="CONTENT"
        actions={
          <Button onClick={() => toast({ title: 'CONTENT ENGINE STUB', description: 'Agent 8 will implement automated AI editorial workflows here.' })} className="font-mono text-xs">
            + DRAFT PIECE
          </Button>
        }
      />

      <EmptyState
        icon={FileText}
        title="No Content Drafts Active"
        description="Leverage your stored RAG context to produce authentic founder stories and technical case studies."
        actionLabel="GENERATE NEW DRAFT"
        onAction={() => toast({ title: 'READY FOR AGENT 8', description: 'Content synthesis engine assigned to Agent 8.' })}
      />
    </ResponsivePageContainer>
  );
}

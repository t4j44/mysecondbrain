'use client';

import * as React from 'react';
import { ResponsivePageContainer } from '@/components/shared/responsive-page-container';
import { PageHeader } from '@/components/shared/page-header';
import { EmptyState } from '@/components/shared/empty-state';
import { Brain } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';

export default function MemoriesPage() {
  const { toast } = useToast();

  return (
    <ResponsivePageContainer>
      <PageHeader
        title="Second Brain Memories"
        description="Unstructured founder reflections, research clips, and strategic notes indexed into vector embeddings for RAG retrieval."
        badge="VECTOR VAULT"
        actions={
          <Button onClick={() => toast({ title: 'MEMORY STUB', description: 'Agent 6 and 9 will attach vector embedding pipelines here.' })} className="font-mono text-xs">
            + CAPTURE MEMORY
          </Button>
        }
      />

      <EmptyState
        icon={Brain}
        title="Your Memory Vault is Clean"
        description="Every memory captured here is embedded via OpenAI/pgvector for instant proactive semantic search."
        actionLabel="CAPTURE FIRST MEMORY"
        onAction={() => toast({ title: 'READY FOR AGENT 6 & 9', description: 'Vector indexing pipeline ready for integration.' })}
      />
    </ResponsivePageContainer>
  );
}

'use client';

import * as React from 'react';
import { ResponsivePageContainer } from '@/components/shared/responsive-page-container';
import { PageHeader } from '@/components/shared/page-header';
import { EmptyState } from '@/components/shared/empty-state';
import { Calendar } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';

export default function MeetingsPage() {
  const { toast } = useToast();

  return (
    <ResponsivePageContainer>
      <PageHeader
        title="Meeting Intelligence & Audio"
        description="Recorded interaction transcriptions, automatic speaker summaries, and extracted action items."
        badge="MEETINGS"
        actions={
          <Button onClick={() => toast({ title: 'MEETING AUDIO STUB', description: 'Agent 6 will connect Whisper transcript extraction here.' })} className="font-mono text-xs">
            + UPLOAD RECORDING
          </Button>
        }
      />

      <EmptyState
        icon={Calendar}
        title="No Meeting Transcriptions Synced"
        description="Upload audio recordings or notes to trigger AI action item extraction and CRM linkage."
        actionLabel="UPLOAD AUDIO FILE"
        onAction={() => toast({ title: 'READY FOR AGENT 6', description: 'Meeting audio processing scheduled for Agent 6.' })}
      />
    </ResponsivePageContainer>
  );
}

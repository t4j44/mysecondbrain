'use client';

import * as React from 'react';
import { ResponsivePageContainer } from '@/components/shared/responsive-page-container';
import { PageHeader } from '@/components/shared/page-header';
import { AIInsightPanel } from '@/components/shared/ai-insight-panel';
import { ChatArea } from '@/components/chat/ChatArea';

export default function AssistantPage() {
  return (
    <ResponsivePageContainer>
      <PageHeader
        title="Proactive AI Assistant"
        description="Grounded conversational co-pilot with real-time read access across your entire multi-venture vector graph."
        badge="RAG CO-PILOT"
      />

      <AIInsightPanel
        title="ASSISTANT PROTOCOL ACTIVE"
        insight="I am your grounded Second Brain co-pilot. I synthesize answers strictly from your private RLS vault, citing specific meetings, tasks, and people without hallucinating external noise."
        confidence={100}
        sourceCount={0}
      />

      <div className="my-6">
        <ChatArea api="/api/v1/ai/search" />
      </div>
    </ResponsivePageContainer>
  );
}


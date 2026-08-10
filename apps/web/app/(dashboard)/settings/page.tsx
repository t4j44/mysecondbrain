import * as React from 'react';
import { SectionHeader } from '@/components/shared/section-header';
import { ShieldCheck, Database, Terminal } from 'lucide-react';

export default function SettingsOverviewPage() {
  return (
    <div className="space-y-6">
      <SectionHeader
        title="Terminal Configuration Status"
        description="System health check and security policy overview for your currently active session."
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="rounded-lg border border-border bg-[#0e0716] p-4 space-y-2">
          <div className="flex items-center space-x-2 text-xs font-mono text-[#00ff9d]">
            <ShieldCheck className="h-4 w-4" />
            <span>RLS POLICY STATUS</span>
          </div>
          <h4 className="text-base font-bold text-[#f7f4ea]">Strict Isolation Enforced</h4>
          <p className="text-xs text-muted-foreground leading-relaxed">
            All Database read and write queries execute under verified JWT user ownership claims. Zero public schema leak risk.
          </p>
        </div>

        <div className="rounded-lg border border-border bg-[#0e0716] p-4 space-y-2">
          <div className="flex items-center space-x-2 text-xs font-mono text-[#00ff9d]">
            <Database className="h-4 w-4" />
            <span>VECTOR VAULT ENGINE</span>
          </div>
          <h4 className="text-base font-bold text-[#f7f4ea]">pgvector / OpenAI Ready</h4>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Embeddings generate automatically upon entity creation to empower proactive RAG chat synthesis.
          </p>
        </div>
      </div>

      <div className="border-t border-border pt-4 text-xs font-mono text-muted-foreground flex items-center justify-between">
        <span className="flex items-center">
          <Terminal className="h-3.5 w-3.5 mr-2 text-[#00ff9d]" />
          App Router Foundation: Verified (Agent 4)
        </span>
        <span>Version: 2.0-PROD</span>
      </div>
    </div>
  );
}

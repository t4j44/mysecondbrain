'use client';

import * as React from 'react';
import { SectionHeader } from '@/components/shared/section-header';
import { Download, FileText, Package, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';

export default function SettingsExportPage() {
  const { toast } = useToast();

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Data Portability & Ownership Export"
        description="Export your entire Second Brain database into human-readable Markdown files or complete ZIP archives at any time."
      />

      <div className="rounded-lg border border-[#00ff9d]/30 bg-[#0c0614] p-6 space-y-3">
        <div className="flex items-center space-x-2 text-xs font-mono text-[#00ff9d]">
          <CheckCircle className="h-4 w-4" />
          <span>OWNERSHIP-FIRST GUARANTEE</span>
        </div>
        <p className="text-sm text-cream leading-relaxed">
          Taj’s Second Brain adheres strictly to zero lock-in design principles. All notes, CRM interactions, meetings, and task timelines can be generated as pristine Markdown bundles formatted for Obsidian, Logseq, or local Git repositories.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
        <div className="rounded-lg border border-border bg-[#0e0716] p-5 flex flex-col justify-between space-y-4">
          <div className="space-y-2">
            <div className="h-10 w-10 rounded-md bg-[#251238] border border-[#00ff9d]/30 flex items-center justify-center text-[#00ff9d]">
              <FileText className="h-5 w-5" />
            </div>
            <h4 className="text-base font-bold text-[#f7f4ea]">Markdown Vault Bundle</h4>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Export all memories, ventures, projects, and notes into structured `.md` folders with YAML frontmatter metadata.
            </p>
          </div>
          <Button
            onClick={() => toast({ title: 'PORTABILITY STUB', description: 'Agent 7 will implement streaming ZIP download endpoints here.' })}
            variant="default"
            className="w-full font-mono text-xs font-bold"
          >
            <Download className="mr-2 h-4 w-4" />
            GENERATE MARKDOWN EXPORT
          </Button>
        </div>

        <div className="rounded-lg border border-border bg-[#0e0716] p-5 flex flex-col justify-between space-y-4">
          <div className="space-y-2">
            <div className="h-10 w-10 rounded-md bg-[#251238] border border-[#00ff9d]/30 flex items-center justify-center text-[#00ff9d]">
              <Package className="h-5 w-5" />
            </div>
            <h4 className="text-base font-bold text-[#f7f4ea]">Full Relational JSON Archive</h4>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Complete raw JSON dumps of your relational Postgres tables, RAG embeddings metadata, and audit logs.
            </p>
          </div>
          <Button
            onClick={() => toast({ title: 'PORTABILITY STUB', description: 'Agent 7 will connect bulk JSON archive packaging here.' })}
            variant="outline"
            className="w-full font-mono text-xs font-bold"
          >
            <Download className="mr-2 h-4 w-4" />
            DOWNLOAD JSON ARCHIVE
          </Button>
        </div>
      </div>
    </div>
  );
}

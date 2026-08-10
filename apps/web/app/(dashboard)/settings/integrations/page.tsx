'use client';

import * as React from 'react';
import { SectionHeader } from '@/components/shared/section-header';
import { Share2, Calendar, HardDrive, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';

export default function SettingsIntegrationsPage() {
  const { toast } = useToast();

  return (
    <div className="space-y-6">
      <SectionHeader
        title="External Productivity Integrations"
        description="Connect Google Calendar, Google Drive backups, and third-party API data conduits."
        action={
          <span className="inline-block rounded px-2 py-0.5 text-[10px] font-mono font-bold bg-[#251238] text-[#00ff9d] border border-[#00ff9d]/30">
            AGENT 7 TARGET
          </span>
        }
      />

      <div className="space-y-4">
        <div className="flex items-center justify-between rounded-lg border border-border bg-[#0e0716] p-5">
          <div className="flex items-center space-x-4">
            <div className="h-12 w-12 rounded-lg bg-[#251238] border border-[#00ff9d]/30 flex items-center justify-center text-[#00ff9d]">
              <Calendar className="h-6 w-6" />
            </div>
            <div>
              <h4 className="text-base font-bold text-[#f7f4ea]">Google Calendar Synchronization</h4>
              <p className="text-xs text-muted-foreground">Automatically synchronize tasks, due dates, and CRM meeting invitations.</p>
            </div>
          </div>
          <Button
            variant="terminal"
            onClick={() => toast({ title: 'INTEGRATION STUB', description: 'Agent 7 (Data Portability Integrations) will attach OAuth flows here.' })}
            className="font-mono text-xs font-bold shrink-0"
          >
            CONNECT OAUTH
          </Button>
        </div>

        <div className="flex items-center justify-between rounded-lg border border-border bg-[#0e0716] p-5">
          <div className="flex items-center space-x-4">
            <div className="h-12 w-12 rounded-lg bg-[#251238] border border-[#00ff9d]/30 flex items-center justify-center text-[#00ff9d]">
              <HardDrive className="h-6 w-6" />
            </div>
            <div>
              <h4 className="text-base font-bold text-[#f7f4ea]">Google Drive Ownership Backup</h4>
              <p className="text-xs text-muted-foreground">Automated scheduled ZIP archive backups of all your memories and markdown notes.</p>
            </div>
          </div>
          <Button
            variant="terminal"
            onClick={() => toast({ title: 'INTEGRATION STUB', description: 'Agent 7 will connect scheduled background sync job runners here.' })}
            className="font-mono text-xs font-bold shrink-0"
          >
            CONFIGURE BACKUP
          </Button>
        </div>
      </div>
    </div>
  );
}

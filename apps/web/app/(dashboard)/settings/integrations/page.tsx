'use client';

import * as React from 'react';
import { SectionHeader } from '@/components/shared/section-header';
import { Calendar, HardDrive } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';

export default function SettingsIntegrationsPage() {
  const { toast } = useToast();

  const showDeferred = (surface: string) => {
    toast({
      title: 'GOOGLE DISABLED',
      description: `${surface} is NOT IMPLEMENTED (v0.1 deferred). The app will not claim connected or invent sync counts.`,
    });
  };

  return (
    <div className="space-y-6">
      <SectionHeader
        title="External Productivity Integrations"
        description="Google Workspace is DISABLED / NOT IMPLEMENTED until real OAuth ships. No connected state is claimed."
        action={
          <span className="inline-block rounded px-2 py-0.5 text-[10px] font-mono font-bold bg-[#251238] text-[#f7b267] border border-[#f7b267]/40">
            NOT IMPLEMENTED
          </span>
        }
      />

      <div className="space-y-4">
        <div className="flex items-center justify-between rounded-lg border border-border bg-[#0e0716] p-5">
          <div className="flex items-center space-x-4">
            <div className="h-12 w-12 rounded-lg bg-[#251238] border border-[#f7b267]/30 flex items-center justify-center text-[#f7b267]">
              <Calendar className="h-6 w-6" />
            </div>
            <div>
              <h4 className="text-base font-bold text-[#f7f4ea]">Google Calendar Synchronization</h4>
              <p className="text-xs text-muted-foreground">
                Status: DISABLED. Real Calendar API sync is deferred; connection cannot succeed yet.
              </p>
            </div>
          </div>
          <Button
            variant="terminal"
            onClick={() => showDeferred('Google Calendar')}
            className="font-mono text-xs font-bold shrink-0"
          >
            UNAVAILABLE
          </Button>
        </div>

        <div className="flex items-center justify-between rounded-lg border border-border bg-[#0e0716] p-5">
          <div className="flex items-center space-x-4">
            <div className="h-12 w-12 rounded-lg bg-[#251238] border border-[#f7b267]/30 flex items-center justify-center text-[#f7b267]">
              <HardDrive className="h-6 w-6" />
            </div>
            <div>
              <h4 className="text-base font-bold text-[#f7f4ea]">Google Drive Ownership Backup</h4>
              <p className="text-xs text-muted-foreground">
                Status: DISABLED. Real Drive backup is deferred; no fake sync metrics.
              </p>
            </div>
          </div>
          <Button
            variant="terminal"
            onClick={() => showDeferred('Google Drive')}
            className="font-mono text-xs font-bold shrink-0"
          >
            UNAVAILABLE
          </Button>
        </div>
      </div>
    </div>
  );
}

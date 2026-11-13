'use client';

import * as React from 'react';
import Link from 'next/link';
import { Breadcrumbs } from './breadcrumbs';
import { CommandMenu } from './command-menu';
import { UserMenu } from './user-menu';
import { BetaNotice } from '../shared/beta-notice';
import { Plus, BrainCircuit } from 'lucide-react';
import { MobileNavigation } from './mobile-navigation';

interface TopBarProps {
  onOpenQuickCapture?: () => void;
}

export function TopBar({ onOpenQuickCapture }: TopBarProps) {
  return (
    <header className="app-top-bar sticky top-0 z-30 flex h-[56px] w-full min-w-0 shrink-0 items-center justify-between gap-2 border-b bg-background/95 px-2.5 sm:px-6">
      <div className="flex min-w-0 items-center gap-2 sm:gap-4">
        <Link href="/dashboard" aria-label="Second Brain Home" className="flex min-h-11 min-w-11 items-center justify-center gap-2 text-sm font-semibold tracking-tight lg:hidden"><BrainCircuit className="h-5 w-5 shrink-0 text-primary" aria-hidden="true" /><span className="hidden truncate sm:inline">Second Brain</span></Link>
        <div className="hidden min-w-0 lg:block"><Breadcrumbs /></div>
      </div>

      <div className="flex shrink-0 items-center gap-2 sm:gap-3">
        <CommandMenu />
        {onOpenQuickCapture && (
          <button
            type="button"
            onClick={onOpenQuickCapture}
            className="inline-flex min-h-11 items-center gap-1.5 rounded-lg bg-primary px-3 text-sm font-medium text-primary-foreground"
            aria-label="Capture"
            title="Capture a note, recording, file or person"
          >
            <Plus className="h-4 w-4" aria-hidden="true" />
            <span>Capture</span>
          </button>
        )}

        <div className="lg:hidden"><MobileNavigation /></div>
        <div className="hidden xl:block"><BetaNotice /></div>
        <UserMenu />
      </div>
    </header>
  );
}

'use client';

import * as React from 'react';
import Link from 'next/link';
import { Breadcrumbs } from './breadcrumbs';
import { CommandMenu } from './command-menu';
import { UserMenu } from './user-menu';
import { BetaNotice } from '../shared/beta-notice';
import { MobileNavigation } from './mobile-navigation';
import { Plus, BrainCircuit } from 'lucide-react';

interface TopBarProps {
  onOpenQuickCapture?: () => void;
}

export function TopBar({ onOpenQuickCapture }: TopBarProps) {
  return (
    <header className="app-top-bar sticky top-0 z-30 flex h-[56px] w-full min-w-0 shrink-0 items-center justify-between gap-2 border-b bg-background/95 px-2.5 sm:px-6">
      <div className="flex min-w-0 items-center gap-2 sm:gap-4">
        <MobileNavigation />
        <Link href="/dashboard" aria-label="Second Brain Home" className="flex min-w-0 items-center gap-2 text-sm font-semibold tracking-tight lg:hidden"><BrainCircuit className="h-5 w-5 text-primary" /><span className="truncate">Second Brain</span></Link>
        <div className="hidden min-w-0 lg:block"><Breadcrumbs /></div>
      </div>

      <div className="flex shrink-0 items-center gap-2 sm:gap-3">
        {/* Quick Capture Pill (Desktop / Tablet) */}
        {onOpenQuickCapture && (
          <button
            type="button"
            onClick={onOpenQuickCapture}
            className="hidden 2xl:inline-flex min-h-11 items-center gap-1.5 px-3 rounded-lg bg-primary/10 text-primary border text-sm"
            title="1-Tap Smart Capture (Press Q or C)"
          >
            <Plus className="h-3.5 w-3.5 stroke-[3]" />
            <span>Capture</span>
            <kbd className="text-[10px] bg-[#0a0510] px-1 py-0.2 rounded border border-[#00ff9d]/30 text-[#00ff9d]">
              Q
            </kbd>
          </button>
        )}

        <CommandMenu />
        <div className="hidden sm:block"><BetaNotice /></div>
        <UserMenu />
      </div>
    </header>
  );
}

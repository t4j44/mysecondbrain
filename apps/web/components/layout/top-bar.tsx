'use client';

import * as React from 'react';
import { Breadcrumbs } from './breadcrumbs';
import { CommandMenu } from './command-menu';
import { UserMenu } from './user-menu';
import { MobileNavigation } from './mobile-navigation';
import { Plus, Mic, Sparkles } from 'lucide-react';

interface TopBarProps {
  onOpenQuickCapture?: () => void;
}

export function TopBar({ onOpenQuickCapture }: TopBarProps) {
  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-[#251238] bg-[#0a0510]/95 px-3 sm:px-6 backdrop-blur transition-all">
      <div className="flex items-center space-x-3 sm:space-x-4">
        <MobileNavigation />
        <Breadcrumbs />
      </div>

      <div className="flex items-center space-x-2 sm:space-x-3">
        {/* Quick Capture Pill (Desktop / Tablet) */}
        {onOpenQuickCapture && (
          <button
            type="button"
            onClick={onOpenQuickCapture}
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#00ff9d]/10 hover:bg-[#00ff9d]/20 text-[#00ff9d] border border-[#00ff9d]/40 font-mono text-xs font-bold transition-all shadow-[0_0_10px_rgba(0,255,157,0.15)]"
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
        <UserMenu />
      </div>
    </header>
  );
}

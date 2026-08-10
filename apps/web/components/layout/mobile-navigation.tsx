'use client';

import * as React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Menu, X, Terminal, ShieldCheck } from 'lucide-react';
import { Sidebar } from './sidebar';

export function MobileNavigation() {
  const [open, setOpen] = React.useState(false);
  const pathname = usePathname();

  // Close responsive drawer when navigation occurs
  React.useEffect(() => {
    setOpen(false);
  }, [pathname]);

  return (
    <div className="md:hidden">
      <button
        onClick={() => setOpen(true)}
        className="inline-flex h-11 w-11 items-center justify-center rounded-md border border-border bg-[#0e0716] text-cream hover:border-[#00ff9d] transition-colors"
        aria-label="Toggle navigation drawer"
      >
        <Menu className="h-6 w-6 text-[#00ff9d]" />
      </button>

      {open && (
        <div className="fixed inset-0 z-[200] flex">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200"
            onClick={() => setOpen(false)}
            aria-hidden="true"
          />

          {/* Drawer Container */}
          <div className="relative flex w-80 max-w-[85vw] flex-col bg-[#0a0510] shadow-[0_0_50px_rgba(0,0,0,0.9)] z-10 animate-in slide-in-from-left duration-200 border-r border-[#251238]">
            <div className="absolute right-3 top-3 z-20">
              <button
                onClick={() => setOpen(false)}
                className="inline-flex h-11 w-11 items-center justify-center rounded-md text-muted-foreground hover:bg-[#251238] hover:text-[#00ff9d] transition-colors"
                aria-label="Close navigation drawer"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            <Sidebar className="w-full h-full border-none" />
          </div>
        </div>
      )}
    </div>
  );
}

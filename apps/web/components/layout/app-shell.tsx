'use client';

import * as React from 'react';
import { Sidebar } from './sidebar';
import { TopBar } from './top-bar';

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-background text-foreground font-sans">
      {/* Skip to Main Content Accessibility Anchor */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:z-[999] focus:p-4 focus:bg-[#00ff9d] focus:text-[#0a0510] focus:font-mono focus:font-bold focus:shadow-2xl rounded-br-lg"
      >
        [ SKIP TO MAIN CONTENT ]
      </a>

      {/* Desktop Persistent Sidebar */}
      <Sidebar className="hidden md:flex" />

      {/* Main Content Workspace Column */}
      <div className="flex flex-1 flex-col min-w-0">
        <TopBar />
        <main id="main-content" className="flex-1 overflow-x-hidden p-4 sm:p-6 md:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}

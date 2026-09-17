'use client';

import * as React from 'react';
import { Sidebar } from './sidebar';
import { TopBar } from './top-bar';
import { MobileBottomBar } from './mobile-bottom-bar';
import { QuickCaptureModal } from '../capture/quick-capture-modal';
import { WorkSessionModal } from '../session/work-session-modal';
import { BetaNotice } from '../shared/beta-notice';

export function AppShell({ children }: { children: React.ReactNode }) {
  const [quickCaptureOpen, setQuickCaptureOpen] = React.useState(false);
  const [sessionModalOpen, setSessionModalOpen] = React.useState(false);

  // Global hotkey listeners for ADHD speed
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger if user is typing inside an input or textarea
      const target = e.target as HTMLElement;
      const isInput =
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable;

      if (!isInput) {
        if (e.key === 'q' || e.key === 'Q' || e.key === 'c' || e.key === 'C') {
          e.preventDefault();
          setQuickCaptureOpen(true);
        }
      }

      if ((e.metaKey || e.ctrlKey) && e.shiftKey && (e.key === 'c' || e.key === 'C')) {
        e.preventDefault();
        setQuickCaptureOpen(true);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

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
      <Sidebar
        className="hidden md:flex"
        onOpenQuickCapture={() => setQuickCaptureOpen(true)}
      />

      {/* Main Content Workspace Column */}
      <div className="flex flex-1 flex-col min-w-0">
        <TopBar onOpenQuickCapture={() => setQuickCaptureOpen(true)} />
        <BetaNotice />
        <main
          id="main-content"
          className="flex-1 overflow-x-hidden p-3 sm:p-5 md:p-6 pb-24 md:pb-8"
        >
          {children}
        </main>
      </div>

      {/* Mobile Sticky Bottom Navigation */}
      <MobileBottomBar onOpenQuickCapture={() => setQuickCaptureOpen(true)} />

      {/* Global Quick Capture Modal */}
      <QuickCaptureModal
        isOpen={quickCaptureOpen}
        onClose={() => setQuickCaptureOpen(false)}
      />

      {/* Global Work Session Finalizer Modal */}
      <WorkSessionModal
        isOpen={sessionModalOpen}
        onClose={() => setSessionModalOpen(false)}
      />
    </div>
  );
}

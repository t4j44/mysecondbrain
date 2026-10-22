'use client';

import * as React from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { Sidebar } from './sidebar';
import { TopBar } from './top-bar';
import { MobileBottomBar } from './mobile-bottom-bar';
import { BetaNotice } from '../shared/beta-notice';

export function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const conversation = pathname === '/assistant';
  const shellRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const viewport = window.visualViewport;
    const bottomBar = shellRef.current?.querySelector<HTMLElement>('.mobile-bottom-bar');
    const update = () => {
      const editable = document.activeElement?.matches('input, textarea, [contenteditable="true"]');
      const keyboard = Boolean(editable && viewport && window.innerHeight - viewport.height > 120);
      const shell = shellRef.current;
      if (!shell) return;
      shell.dataset.keyboard = String(keyboard);
      shell.dataset.expandedText = String(parseFloat(getComputedStyle(document.documentElement).fontSize) >= 24);
      shell.style.setProperty('--app-height', `${viewport?.height ?? window.innerHeight}px`);
      shell.style.setProperty('--viewport-top', `${viewport?.offsetTop ?? 0}px`);
      shell.style.setProperty('--bottom-nav-height', `${bottomBar?.getBoundingClientRect().height ?? 0}px`);
    };
    update();
    viewport?.addEventListener('resize', update);
    viewport?.addEventListener('scroll', update);
    document.addEventListener('focusin', update);
    document.addEventListener('focusout', update);
    const observer = new ResizeObserver(update);
    if (bottomBar) observer.observe(bottomBar);
    return () => {
      viewport?.removeEventListener('resize', update);
      viewport?.removeEventListener('scroll', update);
      document.removeEventListener('focusin', update);
      document.removeEventListener('focusout', update);
      observer.disconnect();
    };
  }, []);

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
          router.push('/capture');
        }
      }

      if ((e.metaKey || e.ctrlKey) && e.shiftKey && (e.key === 'c' || e.key === 'C')) {
        e.preventDefault();
        router.push('/capture');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [router]);

  return (
    <div ref={shellRef} data-conversation={conversation} className={`app-shell flex min-h-dvh bg-background text-foreground font-sans ${conversation ? 'conversation-shell' : ''}`}>
      {/* Skip to Main Content Accessibility Anchor */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:z-[999] focus:p-4 focus:bg-[#00ff9d] focus:text-[#0a0510] focus:font-mono focus:font-bold focus:shadow-2xl rounded-br-lg"
      >
        Skip to main content
      </a>

      {/* Desktop Persistent Sidebar */}
      <Sidebar
        className="hidden lg:flex"
        onOpenQuickCapture={() => router.push('/capture')}
      />

      {/* Main Content Workspace Column */}
      <div className="workspace-column flex min-h-0 min-w-0 flex-1 flex-col">
        <TopBar onOpenQuickCapture={() => router.push('/capture')} />
        <BetaNotice />
        <main
          id="main-content"
          tabIndex={-1}
          style={{paddingBottom: 'calc(var(--bottom-nav-height, 4rem) + 1rem)'}}
          className={`workspace-main min-h-0 min-w-0 flex-1 ${conversation ? 'flex flex-col' : 'p-4 pb-[calc(5rem+env(safe-area-inset-bottom))] sm:p-5 md:p-6 md:pb-8'}`}
        >
          {children}
        </main>
      </div>

      {/* Mobile Sticky Bottom Navigation */}
      <MobileBottomBar onOpenQuickCapture={() => router.push('/capture')} />
    </div>
  );
}

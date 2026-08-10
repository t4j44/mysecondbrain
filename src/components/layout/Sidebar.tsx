'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  Briefcase, 
  FolderGit2, 
  CheckSquare, 
  Plus, 
  Terminal, 
  Menu, 
  X, 
  Settings,
  BrainCircuit
} from 'lucide-react';
import { Button } from '../ui/CustomUi';
import QuickCreate from '../execution/QuickCreate';
import CommandMenu from './CommandMenu';
import { mockApi } from '../../lib/mockApi';

interface LayoutShellProps {
  children: React.ReactNode;
}

export default function LayoutShell({ children }: LayoutShellProps) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [quickCreateOpen, setQuickCreateOpen] = useState(false);
  const [commandMenuOpen, setCommandMenuOpen] = useState(false);
  const [profile, setProfile] = useState<{ email: string; full_name: string; settings: { current_mission?: string } } | null>(null);

  useEffect(() => {
    mockApi.getProfile().then(setProfile);
  }, []);

  const navItems = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Ventures', href: '/ventures', icon: Briefcase },
    { name: 'Projects', href: '/projects', icon: FolderGit2 },
    { name: 'Tasks', href: '/tasks', icon: CheckSquare },
  ];

  // Listen for keyboard shortcuts: Ctrl+K for command menu, C for Quick Create
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setCommandMenuOpen(prev => !prev);
      } else if (e.key === 'c' && !['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) {
        e.preventDefault();
        setQuickCreateOpen(true);
      }
    };

    const handleOpenEvent = () => {
      setQuickCreateOpen(true);
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('open-quick-create', handleOpenEvent);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('open-quick-create', handleOpenEvent);
    };
  }, []);

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-terminal-bg text-terminal-fg">
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex flex-col w-64 bg-terminal-panel border-r border-terminal-border flex-shrink-0">
        {/* Brand Header */}
        <div className="p-6 border-b border-terminal-border flex items-center gap-2">
          <Terminal className="text-terminal-accent w-6 h-6 animate-pulse" />
          <span className="font-mono font-bold tracking-widest text-sm text-white uppercase">
            Taj's OS // v1.0
          </span>
        </div>

        {/* Global Mission Indicator */}
        {profile?.settings.current_mission && (
          <div className="px-5 py-3 border-b border-terminal-border bg-terminal-bg/50">
            <span className="text-[10px] uppercase font-mono tracking-wider text-terminal-accent flex items-center gap-1">
              <BrainCircuit size={12} /> Active Mission
            </span>
            <p className="text-xs text-terminal-muted truncate mt-1">
              {profile.settings.current_mission}
            </p>
          </div>
        )}

        {/* Quick Actions */}
        <div className="p-4">
          <Button 
            variant="primary" 
            className="w-full flex items-center justify-center gap-1.5 py-2.5"
            onClick={() => setQuickCreateOpen(true)}
          >
            <Plus size={16} />
            <span className="font-mono text-xs">QUICK EXECUTE [C]</span>
          </Button>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-3 py-2 space-y-1.5">
          {navItems.map((item) => {
            const isActive = pathname.startsWith(item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg font-mono text-sm transition-all border border-transparent ${
                  isActive 
                    ? 'bg-terminal-fg/5 text-terminal-accent border-terminal-border shadow-[0_0_10px_rgba(0,255,157,0.02)]' 
                    : 'text-terminal-muted hover:text-terminal-fg hover:bg-terminal-fg/5'
                }`}
              >
                <Icon size={18} />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* Command shortcut hint */}
        <div className="px-5 py-3 border-t border-terminal-border bg-terminal-bg/40 text-[10px] text-terminal-muted font-mono flex justify-between items-center">
          <span>Command Menu</span>
          <kbd className="px-1.5 py-0.5 rounded bg-terminal-panel border border-terminal-border text-white text-[9px]">Ctrl+K</kbd>
        </div>

        {/* User Profile Card */}
        <div className="p-4 border-t border-terminal-border flex items-center gap-3 bg-terminal-panel">
          <div className="w-9 h-9 rounded-lg bg-terminal-fg/10 flex items-center justify-center font-mono border border-terminal-border text-terminal-accent text-sm font-semibold">
            TI
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-bold text-white truncate font-mono">{profile?.full_name || 'Tajul Islam'}</p>
            <p className="text-[10px] text-terminal-muted truncate">{profile?.email || 'taj@founder.ai'}</p>
          </div>
        </div>
      </aside>

      {/* Mobile Top Header */}
      <header className="md:hidden flex items-center justify-between px-4 py-4 bg-terminal-panel border-b border-terminal-border">
        <div className="flex items-center gap-2">
          <Terminal className="text-terminal-accent w-5 h-5 animate-pulse" />
          <span className="font-mono font-bold tracking-wider text-xs text-white uppercase">Taj's OS</span>
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" onClick={() => setQuickCreateOpen(true)} className="p-1.5">
            <Plus size={16} />
          </Button>
          <Button size="sm" onClick={() => setMobileOpen(!mobileOpen)} className="p-1.5">
            {mobileOpen ? <X size={18} /> : <Menu size={18} />}
          </Button>
        </div>
      </header>

      {/* Mobile Sidebar Dropdown */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 top-[57px] z-40 bg-terminal-bg/95 border-b border-terminal-border flex flex-col animate-in slide-in-from-top duration-200">
          <nav className="flex-1 px-4 py-4 space-y-2">
            {navItems.map((item) => {
              const isActive = pathname.startsWith(item.href);
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3.5 rounded-lg font-mono text-sm ${
                    isActive 
                      ? 'bg-terminal-fg/5 text-terminal-accent border border-terminal-border' 
                      : 'text-terminal-muted hover:text-terminal-fg'
                  }`}
                >
                  <Icon size={18} />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
          <div className="p-4 border-t border-terminal-border bg-terminal-panel flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-terminal-fg/10 flex items-center justify-center font-mono border border-terminal-border text-terminal-accent text-sm">
              TI
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-bold text-white font-mono">{profile?.full_name}</p>
              <p className="text-[10px] text-terminal-muted truncate">{profile?.email}</p>
            </div>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-x-hidden p-4 md:p-8">
        {children}
      </main>

      {/* Shared Modals */}
      <QuickCreate 
        isOpen={quickCreateOpen} 
        onClose={() => setQuickCreateOpen(false)} 
      />
      <CommandMenu 
        isOpen={commandMenuOpen} 
        onClose={() => setCommandMenuOpen(false)} 
      />
    </div>
  );
}

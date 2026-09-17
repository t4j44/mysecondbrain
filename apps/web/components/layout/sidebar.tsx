'use client';

import * as React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Bot,
  Users,
  CheckSquare,
  Briefcase,
  FolderKanban,
  Lightbulb,
  Building2,
  Calendar,
  Brain,
  LineChart,
  Trophy,
  FileText,
  Settings,
  Terminal,
  Plus,
  ChevronDown,
  Sparkles,
} from 'lucide-react';

interface SidebarProps {
  className?: string;
  onOpenQuickCapture?: () => void;
}

export function Sidebar({ className = '', onOpenQuickCapture }: SidebarProps) {
  const pathname = usePathname();
  const [showSecondary, setShowSecondary] = React.useState(false);

  // 4 Primary Surfaces
  const primarySurfaces = [
    { title: 'Home', href: '/dashboard', icon: LayoutDashboard },
    { title: 'Capture', href: '/capture', icon: Plus },
    { title: 'People', href: '/people', icon: Users },
    { title: 'Work', href: '/tasks', icon: CheckSquare },
    { title: 'Ask', href: '/assistant', icon: Bot },
  ];

  // Secondary Modules underneath
  const secondaryGroups = [
    {
      group: 'Venture Execution',
      items: [
        { title: 'Projects', href: '/projects', icon: FolderKanban },
        { title: 'Ventures', href: '/ventures', icon: Briefcase },
        { title: 'Idea Incubator', href: '/ideas', icon: Lightbulb },
        { title: 'Second Brain Vault', href: '/memories', icon: Brain },
        { title: 'Meetings & Audio', href: '/meetings', icon: Calendar },
        { title: 'Documents', href: '/documents', icon: FileText },
        { title: 'Portfolio', href: '/portfolio', icon: Briefcase },
        { title: 'Organizations', href: '/organizations', icon: Building2 },
      ],
    },
    {
      group: 'Growth & Synthesis',
      items: [
        { title: 'Life KPIs', href: '/kpis', icon: LineChart },
        { title: 'Achievements', href: '/achievements', icon: Trophy },
        { title: 'Content Engine', href: '/content', icon: FileText },
        { title: 'Operator Settings', href: '/settings', icon: Settings },
      ],
    },
  ];

  return (
    <aside
      aria-label="Main Navigation"
      className={`flex flex-col border-r border-[#251238] bg-[#0a0510] text-[#f7f4ea] w-64 shrink-0 select-none ${className}`}
    >
      {/* Brand Header */}
      <div className="flex h-16 items-center px-5 border-b border-[#251238]/80">
        <Link href="/dashboard" className="flex items-center space-x-3 group">
          <div className="h-9 w-9 rounded-lg bg-[#00ff9d]/10 border border-[#00ff9d] flex items-center justify-center text-[#00ff9d] group-hover:bg-[#00ff9d]/20 transition-all shadow-[0_0_15px_rgba(0,255,157,0.2)]">
            <Terminal className="h-5 w-5" />
          </div>
          <div>
            <span className="text-sm font-bold tracking-tight text-[#f7f4ea] block">Taj’s Second Brain</span>
            <span className="text-[10px] font-mono text-[#00ff9d] uppercase block tracking-widest">ADHD-FIRST OS</span>
          </div>
        </Link>
      </div>

      {/* Quick Capture CTA Button */}
      {onOpenQuickCapture && (
        <div className="p-3 border-b border-[#251238]/60">
          <button
            type="button"
            onClick={onOpenQuickCapture}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl bg-[#00ff9d] hover:bg-[#00e08a] text-[#0a0510] font-mono text-xs font-bold uppercase tracking-wider transition-all shadow-[0_0_15px_rgba(0,255,157,0.25)] min-h-[44px]"
          >
            <Plus className="h-4 w-4 stroke-[3]" />
            <span>Smart Capture [Q]</span>
          </button>
        </div>
      )}

      {/* Navigation Links */}
      <nav aria-label="Primary Navigation" className="flex-1 overflow-y-auto p-3 space-y-5">
        {/* PRIMARY SURFACES */}
        <div className="space-y-1">
          <div className="px-3 py-1 text-[10px] font-mono uppercase text-[#00ff9d] tracking-widest font-bold flex items-center justify-between">
            <span>Primary Surfaces</span>
            <Sparkles className="h-3 w-3 text-[#00ff9d]" />
          </div>

          {primarySurfaces.map((item) => {
            const isActive =
              item.href === '/dashboard'
                ? pathname === '/dashboard' || pathname === '/'
                : pathname === item.href || pathname.startsWith(item.href);
            const Icon = item.icon;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-sans font-semibold transition-all duration-200 group min-h-[44px] ${
                  isActive
                    ? 'bg-[#00ff9d]/15 text-[#00ff9d] border border-[#00ff9d]/40 shadow-[0_0_15px_rgba(0,255,157,0.15)]'
                    : 'text-[#f7f4ea]/80 hover:bg-[#1d0e2e] hover:text-[#f7f4ea]'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon
                    className={`h-4 w-4 shrink-0 transition-transform group-hover:scale-110 ${
                      isActive ? 'text-[#00ff9d]' : 'text-muted-foreground'
                    }`}
                  />
                  <span>{item.title}</span>
                </div>
              </Link>
            );
          })}
        </div>

        {/* SECONDARY MODULES (Underneath) */}
        <div className="pt-2 border-t border-[#251238]/60 space-y-4">
          <button
            type="button"
            onClick={() => setShowSecondary(!showSecondary)}
            className="w-full flex items-center justify-between px-3 py-1 text-[10px] font-mono uppercase text-muted-foreground tracking-widest hover:text-[#f7f4ea]"
          >
            <span>All Deep Modules</span>
            <ChevronDown
              className={`h-3 w-3 transition-transform ${showSecondary ? 'rotate-180' : ''}`}
            />
          </button>

          {showSecondary &&
            secondaryGroups.map((navGroup) => (
              <div key={navGroup.group} className="space-y-1">
                <div className="px-3 text-[9px] font-mono uppercase text-muted-foreground/60 tracking-wider">
                  {navGroup.group}
                </div>
                <div className="space-y-0.5">
                  {navGroup.items.map((item) => {
                    const isActive = pathname === item.href || pathname.startsWith(item.href);
                    const Icon = item.icon;

                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        className={`flex items-center space-x-3 px-3 py-2 rounded-lg text-xs font-sans transition-colors min-h-[38px] ${
                          isActive
                            ? 'bg-[#1d0e2e] text-[#00ff9d] font-semibold border-l-2 border-[#00ff9d]'
                            : 'text-muted-foreground hover:bg-[#170b24] hover:text-[#f7f4ea]'
                        }`}
                      >
                        <Icon className={`h-3.5 w-3.5 shrink-0 ${isActive ? 'text-[#00ff9d]' : 'text-muted-foreground'}`} />
                        <span>{item.title}</span>
                      </Link>
                    );
                  })}
                </div>
              </div>
            ))}
        </div>
      </nav>

      {/* Terminal System Footer */}
      <div className="p-3.5 border-t border-[#251238] bg-[#050208] text-[11px] font-mono text-muted-foreground">
        <div className="flex items-center justify-between">
          <span className="flex items-center">
            <span className="h-2 w-2 rounded-full bg-[#00ff9d] mr-2 shadow-[0_0_6px_#00ff9d]" />
            PRIVATE WORKSPACE
          </span>
          <span className="text-[#00ff9d]/80 text-[10px]">Zero Overload</span>
        </div>
      </div>
    </aside>
  );
}

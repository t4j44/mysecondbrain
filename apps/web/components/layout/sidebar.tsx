'use client';

import * as React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  CheckSquare,
  Briefcase,
  FolderKanban,
  Lightbulb,
  Users,
  Building2,
  Calendar,
  Brain,
  LineChart,
  Trophy,
  FileText,
  Bot,
  Settings,
  Terminal,
} from 'lucide-react';

interface NavGroup {
  group: string;
  items: {
    title: string;
    href: string;
    icon: React.ElementType;
    badge?: string;
  }[];
}

const navigationGroups: NavGroup[] = [
  {
    group: 'Command Center',
    items: [
      { title: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
      { title: 'Tasks Engine', href: '/tasks', icon: CheckSquare },
    ],
  },
  {
    group: 'Build',
    items: [
      { title: 'Ventures', href: '/ventures', icon: Briefcase },
      { title: 'Projects', href: '/projects', icon: FolderKanban },
      { title: 'Idea Incubator', href: '/ideas', icon: Lightbulb },
    ],
  },
  {
    group: 'Relationships & Knowledge',
    items: [
      { title: 'People & CRM', href: '/people', icon: Users },
      { title: 'Organizations', href: '/organizations', icon: Building2 },
      { title: 'Meetings & Audio', href: '/meetings', icon: Calendar },
      { title: 'Second Brain', href: '/memories', icon: Brain, badge: 'RAG' },
    ],
  },
  {
    group: 'Growth & Output',
    items: [
      { title: 'Life KPIs', href: '/kpis', icon: LineChart },
      { title: 'Achievements', href: '/achievements', icon: Trophy },
      { title: 'Content Engine', href: '/content', icon: FileText },
    ],
  },
  {
    group: 'Intelligence',
    items: [
      { title: 'AI Assistant', href: '/assistant', icon: Bot, badge: 'ACTIVE' },
    ],
  },
  {
    group: 'System',
    items: [
      { title: 'Operator Settings', href: '/settings', icon: Settings },
    ],
  },
];

export function Sidebar({ className = '' }: { className?: string }) {
  const pathname = usePathname();

  return (
    <aside aria-label="Main Navigation" className={`flex flex-col border-r border-[#251238] bg-[#0a0510] text-[#f7f4ea] w-64 shrink-0 select-none ${className}`}>
      {/* Brand Header */}
      <div className="flex h-16 items-center px-6 border-b border-[#251238]/80">
        <Link href="/dashboard" className="flex items-center space-x-3 group">
          <div className="h-9 w-9 rounded-lg bg-[#00ff9d]/10 border border-[#00ff9d] flex items-center justify-center text-[#00ff9d] group-hover:bg-[#00ff9d]/20 transition-all shadow-[0_0_15px_rgba(0,255,157,0.2)]">
            <Terminal className="h-5 w-5" />
          </div>
          <div>
            <span className="text-sm font-bold tracking-tight text-[#f7f4ea] block">Taj’s Second Brain</span>
            <span className="text-[10px] font-mono text-[#00ff9d] uppercase block tracking-widest">OS // v2.0 TERMINAL</span>
          </div>
        </Link>
      </div>

      {/* Grouped Navigation Links */}
      <nav aria-label="Section Navigation" className="flex-1 overflow-y-auto p-4 space-y-6">
        {navigationGroups.map((navGroup) => (
          <div key={navGroup.group} className="space-y-1.5">
            <div className="px-2 text-[10px] font-mono uppercase text-muted-foreground/70 tracking-widest font-semibold">
              {navGroup.group}
            </div>
            <div className="space-y-1">
              {navGroup.items.map((item) => {
                const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href));
                const Icon = item.icon;

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center justify-between px-3 py-2 rounded-md text-sm font-sans font-medium transition-all duration-200 group ${
                      isActive
                        ? 'bg-[#00ff9d]/15 text-[#00ff9d] border border-[#00ff9d]/30 shadow-[0_0_15px_rgba(0,255,157,0.1)] font-semibold'
                        : 'text-muted-foreground hover:bg-[#1d0e2e] hover:text-[#f7f4ea]'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <Icon className={`h-4 w-4 shrink-0 transition-transform group-hover:scale-110 ${isActive ? 'text-[#00ff9d]' : 'text-muted-foreground'}`} />
                      <span>{item.title}</span>
                    </div>
                    {item.badge && (
                      <span className={`text-[9px] font-mono font-bold uppercase px-1.5 py-0.5 rounded border ${
                        isActive ? 'bg-[#00ff9d] text-[#0a0510] border-[#00ff9d]' : 'bg-[#251238] text-[#00ff9d] border-[#00ff9d]/40'
                      }`}>
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Terminal System Footer */}
      <div className="p-4 border-t border-[#251238] bg-[#050208] text-[11px] font-mono text-muted-foreground">
        <div className="flex items-center justify-between">
          <span className="flex items-center">
            <span className="h-2 w-2 rounded-full bg-[#00ff9d] mr-2" />
            RLS SYNCED
          </span>
          <span className="text-[#00ff9d]/80">99.9% Uptime</span>
        </div>
      </div>
    </aside>
  );
}

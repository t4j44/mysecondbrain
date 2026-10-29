'use client';

import Link from 'next/link';
import { useState } from 'react';
import { usePathname } from 'next/navigation';
import { Settings, Users, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { primaryNavigation, isPrimaryActive } from '@/lib/navigation';

interface SidebarProps { className?: string; onOpenQuickCapture?: () => void; collapsible?: boolean }

export function Sidebar({ className = '', collapsible = false }: SidebarProps) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  return <aside aria-label="Main Navigation" className={`flex ${collapsed ? 'w-20' : 'w-[220px]'} shrink-0 flex-col border-r border-border bg-card ${className}`}>
    <Link href="/dashboard" className="flex min-w-0 items-center gap-2 border-b p-4">
      <Users className="h-5 w-5 shrink-0 text-primary" /><span className={collapsed ? 'sr-only' : 'min-w-0 font-semibold [overflow-wrap:anywhere]'}>Second Brain</span>
    </Link>
    {collapsible && <button type="button" aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'} aria-expanded={!collapsed} onClick={() => setCollapsed(value => !value)} className="m-3 inline-flex min-h-11 items-center justify-center gap-2 rounded-xl text-muted-foreground hover:bg-muted">{collapsed ? <PanelLeftOpen className="h-5 w-5" /> : <><PanelLeftClose className="h-5 w-5" /><span className="text-sm">Collapse</span></>}</button>}
    <nav aria-label="Primary Navigation" className="flex-1 space-y-2 p-3">{primaryNavigation.map(item => {
      const active = isPrimaryActive(item.href, pathname); const Icon = item.icon;
      return <Link key={item.href} href={item.href} title={collapsed ? item.title : undefined} aria-current={active ? 'page' : undefined}
        className={`flex min-h-12 items-center gap-3 rounded-xl px-4 text-sm font-medium transition-colors ${active ? 'bg-primary/15 text-primary' : 'text-muted-foreground hover:bg-muted hover:text-foreground'}`}>
        <Icon className="h-5 w-5 shrink-0" /><span className={collapsed ? 'sr-only' : ''}>{item.title}</span>
      </Link>;
    })}</nav>
    <div className="border-t p-3"><Link href="/settings" title={collapsed ? 'Settings' : undefined} className="flex min-h-11 items-center gap-3 rounded-lg px-4 text-sm text-muted-foreground hover:bg-muted"><Settings className="h-4 w-4 shrink-0" /><span className={collapsed ? 'sr-only' : ''}>Settings</span></Link>
      {!collapsed && <p className="px-4 pt-2 text-xs text-muted-foreground">Private workspace · Early beta</p>}</div>
  </aside>;
}

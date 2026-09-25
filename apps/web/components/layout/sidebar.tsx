'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Settings, Users } from 'lucide-react';
import { primaryNavigation, isPrimaryActive } from '@/lib/navigation';

interface SidebarProps { className?: string; onOpenQuickCapture?: () => void }

export function Sidebar({ className = '' }: SidebarProps) {
  const pathname = usePathname();
  return <aside aria-label="Main Navigation" className={`flex w-64 shrink-0 flex-col border-r border-border bg-card ${className}`}>
    <Link href="/dashboard" className="flex items-center gap-3 border-b p-5">
      <Users className="h-6 w-6 text-primary" /><span><span className="block font-semibold">Second Brain</span><span className="text-xs text-muted-foreground">Your relationships, remembered</span></span>
    </Link>
    <nav aria-label="Primary Navigation" className="flex-1 space-y-2 p-3">{primaryNavigation.map(item => {
      const active = isPrimaryActive(item.href, pathname); const Icon = item.icon;
      return <Link key={item.href} href={item.href} aria-current={active ? 'page' : undefined}
        className={`flex min-h-12 items-center gap-3 rounded-xl px-4 text-sm font-medium transition-colors ${active ? 'bg-primary/15 text-primary' : 'text-muted-foreground hover:bg-muted hover:text-foreground'}`}>
        <Icon className="h-5 w-5" /><span>{item.title}</span>
      </Link>;
    })}</nav>
    <div className="border-t p-3"><Link href="/settings" className="flex min-h-11 items-center gap-3 rounded-lg px-4 text-sm text-muted-foreground hover:bg-muted"><Settings className="h-4 w-4" />Settings</Link>
      <p className="px-4 pt-2 text-xs text-muted-foreground">Private workspace · Early beta</p></div>
  </aside>;
}

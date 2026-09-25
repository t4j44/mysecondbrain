'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { primaryNavigation, isPrimaryActive } from '@/lib/navigation';

interface MobileBottomBarProps { onOpenQuickCapture: () => void }
export function MobileBottomBar(_props: MobileBottomBarProps) {
  const pathname = usePathname();
  return <nav aria-label="Mobile Primary Navigation" className="fixed inset-x-0 bottom-0 z-40 border-t bg-background/95 px-1 py-1.5 backdrop-blur-xl safe-area-pb md:hidden">
    <div className="mx-auto grid max-w-md grid-cols-5">{primaryNavigation.map(item => {
      const active = isPrimaryActive(item.href, pathname); const Icon = item.icon;
      return <Link key={item.href} href={item.href} aria-current={active ? 'page' : undefined}
        className={`flex min-h-12 min-w-0 flex-col items-center justify-center gap-1 rounded-lg px-1 text-xs ${active ? 'text-primary' : 'text-muted-foreground'} ${item.title === 'Capture' ? 'bg-primary/10 font-semibold' : ''}`}>
        <Icon className="h-5 w-5" /><span>{item.title}</span>
      </Link>;
    })}</div>
  </nav>;
}

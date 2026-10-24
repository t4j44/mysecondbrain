'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { primaryNavigation, isPrimaryActive } from '@/lib/navigation';

interface MobileBottomBarProps { onOpenQuickCapture: () => void }
export function MobileBottomBar(_props: MobileBottomBarProps) {
  const pathname = usePathname();
  return <nav aria-label="Mobile Primary Navigation" className="mobile-bottom-bar fixed inset-x-0 bottom-0 z-40 border-t bg-card/95 px-2 pt-2 pb-[calc(0.5rem+env(safe-area-inset-bottom))] shadow-[0_-6px_28px_rgba(0,0,0,0.08)] backdrop-blur-xl lg:hidden">
    <div className="mx-auto grid max-w-md grid-cols-5 items-end gap-1">{primaryNavigation.map(item => {
      const active = isPrimaryActive(item.href, pathname); const Icon = item.icon;
      return <Link key={item.href} href={item.href} aria-current={active ? 'page' : undefined}
        className={`sb-interactive flex min-h-12 min-w-0 flex-col items-center justify-center gap-1 rounded-xl px-1 py-1 text-[11px] ${active ? 'text-primary' : 'text-muted-foreground hover:text-foreground hover:bg-muted/60'} ${item.title === 'Capture' ? 'font-semibold' : ''}`}>
        <span className={item.title === 'Capture' ? 'flex h-10 w-10 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-sm' : 'flex h-7 w-10 items-center justify-center'}><Icon className={item.title === 'Capture' ? 'h-6 w-6' : 'h-5 w-5'} /></span><span className="max-w-full text-center leading-tight [overflow-wrap:anywhere]">{item.title}</span>
      </Link>;
    })}</div>
  </nav>;
}

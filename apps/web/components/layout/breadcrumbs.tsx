'use client';

import * as React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ChevronRight, Home } from 'lucide-react';

export function Breadcrumbs() {
  const pathname = usePathname();
  const segments = pathname.split('/').filter(Boolean);

  if (segments.length <= 0 || segments[0] !== 'dashboard' && segments.length === 1 && segments[0] === 'dashboard') {
    return null;
  }

  return (
    <nav aria-label="Breadcrumb" className="flex items-center space-x-1.5 text-xs font-mono text-muted-foreground">
      <Link href="/dashboard" className="flex items-center hover:text-[#00ff9d] transition-colors" title="Command Center">
        <Home className="h-3.5 w-3.5" />
      </Link>

      {segments.map((segment, index) => {
        const url = `/${segments.slice(0, index + 1).join('/')}`;
        const isLast = index === segments.length - 1;
        const formattedTitle = segment
          .replace(/-/g, ' ')
          .toUpperCase();

        return (
          <React.Fragment key={url}>
            <ChevronRight className="h-3 w-3 text-muted-foreground/50 shrink-0" />
            {isLast ? (
              <span className="font-semibold text-[#f7f4ea] tracking-wider" aria-current="page">
                {formattedTitle}
              </span>
            ) : (
              <Link href={url} className="hover:text-[#00ff9d] transition-colors tracking-wider">
                {formattedTitle}
              </Link>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
}

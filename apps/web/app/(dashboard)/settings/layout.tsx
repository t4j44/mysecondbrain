'use client';

import * as React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ResponsivePageContainer } from '@/components/shared/responsive-page-container';
import { PageHeader } from '@/components/shared/page-header';
import { Settings, User, Share2, Download, Monitor } from 'lucide-react';

const settingsTabs = [
  { name: 'General Overview', href: '/settings', icon: Settings },
  { name: 'Operator Profile', href: '/settings/profile', icon: User },
  { name: 'Data Portability & Export', href: '/settings/export', icon: Download },
  { name: 'UI Appearance & Theme', href: '/settings/appearance', icon: Monitor },
  { name: 'External Integrations', href: '/settings/integrations', icon: Share2, badge: 'AGENT 7' },
];

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <ResponsivePageContainer>
      <PageHeader
        title="Operator Settings & Protocols"
        description="Configure terminal preferences, identity security keys, data export backups, and cloud integrations."
        badge="SYSTEM CONFIG"
      />

      <div className="grid grid-cols-1 md:grid-cols-4 gap-8 my-6">
        <aside aria-label="Settings navigation" className="md:col-span-1 space-y-1">
          {settingsTabs.map((tab) => {
            const isActive = pathname === tab.href;
            const Icon = tab.icon;

            return (
              <Link
                key={tab.href}
                href={tab.href}
                className={`flex items-center justify-between px-3 py-2 rounded-md text-sm font-sans font-medium transition-all ${
                  isActive
                    ? 'bg-[#00ff9d]/15 text-[#00ff9d] border border-[#00ff9d]/40 font-bold'
                    : 'text-muted-foreground hover:bg-[#1d0e2e] hover:text-[#f7f4ea]'
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <Icon className={`h-4 w-4 shrink-0 ${isActive ? 'text-[#00ff9d]' : 'text-muted-foreground'}`} />
                  <span>{tab.name}</span>
                </div>
                {tab.badge && (
                  <span className="text-[9px] font-mono uppercase bg-[#251238] text-[#00ff9d] px-1 py-0.5 rounded border border-[#00ff9d]/30">
                    {tab.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </aside>

        <main className="md:col-span-3">
          <div className="rounded-lg border border-border bg-[#0a0510] p-6 shadow-sm">
            {children}
          </div>
        </main>
      </div>
    </ResponsivePageContainer>
  );
}

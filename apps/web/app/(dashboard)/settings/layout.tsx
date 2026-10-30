'use client';

import * as React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ResponsivePageContainer } from '@/components/shared/responsive-page-container';
import { PageHeader } from '@/components/shared/page-header';
import { Settings, User, Share2, Download, Monitor } from 'lucide-react';

const settingsTabs = [
  { name: 'Overview', href: '/settings', icon: Settings },
  { name: 'Profile', href: '/settings/profile', icon: User },
  { name: 'Export', href: '/settings/export', icon: Download },
  { name: 'Appearance', href: '/settings/appearance', icon: Monitor },
  { name: 'Connections', href: '/settings/integrations', icon: Share2 },
];

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <ResponsivePageContainer>
      <PageHeader
        title="Settings"
        description="Manage your profile, appearance, connections and saved data."
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
                aria-current={isActive ? 'page' : undefined}
                className={`flex min-h-11 items-center justify-between px-3 py-2 rounded-md text-sm font-sans font-medium transition-all ${
                  isActive
                    ? 'bg-primary/10 text-primary border border-primary/30 font-bold'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <Icon className="h-4 w-4 shrink-0" />
                  <span>{tab.name}</span>
                </div>
              </Link>
            );
          })}
        </aside>

        <main className="md:col-span-3">
          <div className="rounded-lg border border-border bg-card p-4 sm:p-6 shadow-sm">
            {children}
          </div>
        </main>
      </div>
    </ResponsivePageContainer>
  );
}

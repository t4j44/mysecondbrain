'use client';

import * as React from 'react';
import { Breadcrumbs } from './breadcrumbs';
import { CommandMenu } from './command-menu';
import { UserMenu } from './user-menu';
import { MobileNavigation } from './mobile-navigation';

export function TopBar() {
  return (
    <header className="sticky top-0 z-50 flex h-16 w-full items-center justify-between border-b border-[#251238] bg-[#0a0510]/95 px-4 sm:px-6 backdrop-blur transition-all">
      <div className="flex items-center space-x-4">
        <MobileNavigation />
        <Breadcrumbs />
      </div>

      <div className="flex items-center space-x-3 sm:space-x-4">
        <CommandMenu />
        <UserMenu />
      </div>
    </header>
  );
}

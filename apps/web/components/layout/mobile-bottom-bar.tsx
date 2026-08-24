'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Bot, Plus, Users, CheckSquare } from 'lucide-react';

interface MobileBottomBarProps {
  onOpenQuickCapture: () => void;
}

export function MobileBottomBar({ onOpenQuickCapture }: MobileBottomBarProps) {
  const pathname = usePathname();

  const navItems = [
    {
      title: 'Today',
      href: '/dashboard',
      icon: LayoutDashboard,
      isActive: pathname === '/dashboard' || pathname === '/',
    },
    {
      title: 'Ask Brain',
      href: '/assistant',
      icon: Bot,
      isActive: pathname === '/assistant',
    },
    {
      title: 'Capture',
      isAction: true,
      onClick: onOpenQuickCapture,
      icon: Plus,
    },
    {
      title: 'Network',
      href: '/people',
      icon: Users,
      isActive: pathname.startsWith('/people') || pathname.startsWith('/organizations') || pathname.startsWith('/meetings'),
    },
    {
      title: 'Work',
      href: '/tasks',
      icon: CheckSquare,
      isActive: pathname.startsWith('/tasks') || pathname.startsWith('/projects') || pathname.startsWith('/ventures'),
    },
  ];

  return (
    <nav
      aria-label="Mobile Primary Navigation"
      className="fixed bottom-0 left-0 right-0 z-40 md:hidden bg-[#0a0510]/95 backdrop-blur-xl border-t border-[#251238] px-2 py-1.5 safe-area-pb"
    >
      <div className="flex items-center justify-around max-w-md mx-auto">
        {navItems.map((item, index) => {
          if (item.isAction) {
            return (
              <button
                key="capture-fab"
                type="button"
                onClick={item.onClick}
                className="relative -top-3 flex flex-col items-center justify-center h-13 w-13 rounded-full bg-[#00ff9d] text-[#0a0510] font-bold shadow-[0_0_20px_rgba(0,255,157,0.4)] active:scale-95 transition-transform"
                aria-label="1-Tap Quick Capture"
              >
                <Plus className="h-6 w-6 stroke-[2.5]" />
                <span className="sr-only">Quick Capture</span>
              </button>
            );
          }

          const Icon = item.icon;
          const active = item.isActive;

          return (
            <Link
              key={item.href || index}
              href={item.href!}
              className={`flex flex-col items-center justify-center min-w-[56px] min-h-[48px] py-1 px-2 rounded-xl transition-all ${
                active
                  ? 'text-[#00ff9d]'
                  : 'text-muted-foreground hover:text-[#f7f4ea] active:scale-95'
              }`}
            >
              <div className="relative">
                <Icon className={`h-5 w-5 ${active ? 'text-[#00ff9d]' : 'text-muted-foreground'}`} />
                {active && (
                  <span className="absolute -bottom-1 left-1/2 -translate-x-1/2 h-1 w-1 rounded-full bg-[#00ff9d] shadow-[0_0_6px_#00ff9d]" />
                )}
              </div>
              <span className={`text-[10px] font-sans mt-1 ${active ? 'font-bold text-[#00ff9d]' : 'font-medium'}`}>
                {item.title}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

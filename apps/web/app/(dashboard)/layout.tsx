import * as React from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { requireAuthenticatedUser } from '@/lib/auth/session';

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Ensure server-side verification of operator authentication before rendering shell
  await requireAuthenticatedUser('/login');

  return <AppShell>{children}</AppShell>;
}

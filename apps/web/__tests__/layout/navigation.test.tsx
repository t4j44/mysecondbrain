import * as React from 'react';
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Breadcrumbs } from '@/components/layout/breadcrumbs';
import { Sidebar } from '@/components/layout/sidebar';
import { MobileBottomBar } from '@/components/layout/mobile-bottom-bar';
import { isMoreActive, isPrimaryActive } from '@/lib/navigation';

describe('Global App Shell & Navigation', () => {
  it('renders a plain-language title and predictable back navigation', () => {
    // Note: usePathname is mocked to '/dashboard/ventures' in test/setup.ts
    render(<Breadcrumbs />);
    expect(screen.getByText('Ventures')).toBeInTheDocument();
    expect(screen.getByRole('link', {name: 'Back to Home'})).toHaveAttribute('href','/dashboard');
  });

  it('exposes four mobile destinations and More while retaining desktop tools', () => {
    render(<Sidebar />);
    render(<MobileBottomBar onOpenQuickCapture={() => {}} />);
    const desktop = within(screen.getByRole('navigation', { name: 'Primary Navigation' }));
    expect(desktop.getAllByRole('link').map(link => link.textContent)).toEqual(['Home', 'People', 'Meetings', 'Capture', 'Ask', 'Work', 'Documents']);
    const mobile = within(screen.getByRole('navigation', { name: 'Mobile Primary Navigation' }));
    expect(mobile.getAllByRole('link').map(link => link.textContent)).toEqual(['Home', 'People', 'Capture', 'Meetings']);
    fireEvent.click(mobile.getByRole('button', { name: 'More' }));
    const drawer = within(screen.getByRole('dialog', { name: 'Navigation' }));
    expect(drawer.getByRole('link', { name: 'Ask' })).toHaveAttribute('href', '/assistant');
    expect(drawer.getByRole('link', { name: 'Documents' })).toHaveAttribute('href', '/documents');
    fireEvent.click(drawer.getByRole('button', { name: 'Close navigation' }));
    expect(screen.queryByText('Life KPIs')).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Settings' })).toBeInTheDocument();
  });

  it('keeps Work selected while viewing its nested destinations', () => {
    expect(isPrimaryActive('/work', '/meetings/meeting-id')).toBe(false);
    expect(isPrimaryActive('/meetings', '/meetings/meeting-id')).toBe(true);
    expect(isPrimaryActive('/work', '/documents')).toBe(false);
    expect(isPrimaryActive('/work', '/work/commitments')).toBe(true);
    expect(isPrimaryActive('/people', '/meetings/meeting-id')).toBe(false);
    expect(isPrimaryActive('/people', '/people/person-id')).toBe(true);
    expect(isMoreActive('/assistant')).toBe(true);
    expect(isMoreActive('/settings/privacy')).toBe(true);
    expect(isMoreActive('/meetings/meeting-id')).toBe(false);
  });

  it('keeps accessible destinations when the desktop sidebar collapses', () => {
    render(<Sidebar collapsible />);
    fireEvent.click(screen.getByRole('button', { name: 'Collapse sidebar' }));
    expect(screen.getByRole('link', { name: 'Meetings' })).toHaveAttribute('title', 'Meetings');
    expect(screen.getByRole('link', { name: 'Settings' })).toHaveAttribute('href', '/settings');
    fireEvent.click(screen.getByRole('button', { name: 'Expand sidebar' }));
    expect(screen.getByRole('link', { name: 'Meetings' })).not.toHaveAttribute('title');
  });
});

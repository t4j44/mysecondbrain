import * as React from 'react';
import '@testing-library/jest-dom/vitest';
import { render, screen, within } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Breadcrumbs } from '@/components/layout/breadcrumbs';
import { Sidebar } from '@/components/layout/sidebar';
import { MobileBottomBar } from '@/components/layout/mobile-bottom-bar';
import { isPrimaryActive } from '@/lib/navigation';

describe('Global App Shell & Navigation', () => {
  it('renders Breadcrumbs formatting pathname segments into terminal uppercase titles', () => {
    // Note: usePathname is mocked to '/dashboard/ventures' in test/setup.ts
    render(<Breadcrumbs />);
    expect(screen.getByText('VENTURES')).toBeInTheDocument();
  });

  it('keeps desktop and mobile navigation in the same relationship-first order', () => {
    render(<Sidebar />);
    render(<MobileBottomBar onOpenQuickCapture={() => {}} />);
    for (const name of ['Primary Navigation', 'Mobile Primary Navigation']) {
      const links = within(screen.getByRole('navigation', { name })).getAllByRole('link');
      expect(links.map(link => link.textContent)).toEqual(['Home', 'Capture', 'People', 'Work', 'Ask']);
      expect(links[3]).toHaveAttribute('href', '/work');
    }
    expect(screen.queryByText('Life KPIs')).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Settings' })).toBeInTheDocument();
  });

  it('keeps Work selected while viewing its nested destinations', () => {
    expect(isPrimaryActive('/work', '/meetings/meeting-id')).toBe(true);
    expect(isPrimaryActive('/work', '/work/commitments')).toBe(true);
    expect(isPrimaryActive('/people', '/meetings/meeting-id')).toBe(false);
    expect(isPrimaryActive('/people', '/people/person-id')).toBe(true);
  });
});

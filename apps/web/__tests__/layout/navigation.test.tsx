import * as React from 'react';
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Breadcrumbs } from '@/components/layout/breadcrumbs';
import { Sidebar } from '@/components/layout/sidebar';

describe('Global App Shell & Navigation', () => {
  it('renders Breadcrumbs formatting pathname segments into terminal uppercase titles', () => {
    // Note: usePathname is mocked to '/dashboard/ventures' in test/setup.ts
    render(<Breadcrumbs />);
    expect(screen.getByText('VENTURES')).toBeInTheDocument();
  });

  it('renders desktop Sidebar displaying all core domain navigation groups', () => {
    render(<Sidebar />);
    expect(screen.getByText('Command Center')).toBeInTheDocument();
    expect(screen.getByText('Build')).toBeInTheDocument();
    expect(screen.getByText('Relationships & Knowledge')).toBeInTheDocument();
    expect(screen.getByText('Growth & Output')).toBeInTheDocument();
    expect(screen.getByText('Intelligence')).toBeInTheDocument();
    expect(screen.getByText('System')).toBeInTheDocument();
  });
});

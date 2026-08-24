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

  it('renders desktop Sidebar displaying primary surfaces and secondary groups', () => {
    render(<Sidebar />);
    expect(screen.getByText('Primary Surfaces')).toBeInTheDocument();
    expect(screen.getByText('TODAY')).toBeInTheDocument();
    expect(screen.getByText('ASK BRAIN')).toBeInTheDocument();
    expect(screen.getByText('NETWORK')).toBeInTheDocument();
    expect(screen.getByText('WORK & EVIDENCE')).toBeInTheDocument();
    expect(screen.getByText('Venture Execution')).toBeInTheDocument();
    expect(screen.getByText('Growth & Synthesis')).toBeInTheDocument();
  });
});

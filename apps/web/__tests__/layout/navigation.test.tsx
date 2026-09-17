import * as React from 'react';
import '@testing-library/jest-dom/vitest';
import { render, screen, fireEvent } from '@testing-library/react';
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
    for (const name of ['Home', 'Capture', 'People', 'Work', 'Ask']) {
      expect(screen.getByRole('link', { name })).toBeInTheDocument();
    }
    expect(screen.queryByText('Venture Execution')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'All Deep Modules' }));
    expect(screen.getByText('Venture Execution')).toBeInTheDocument();
    expect(screen.getByText('Growth & Synthesis')).toBeInTheDocument();
  });
});

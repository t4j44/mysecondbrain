import * as React from 'react';
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { Button } from '@/components/ui/button';
import { StatusBadge } from '@/components/shared/status-badge';
import { PriorityBadge } from '@/components/shared/priority-badge';

describe('Shared UI Primitives & Design System', () => {
  it('renders terminal Button with uppercase font styling and fires onClick', async () => {
    const handleClick = vi.fn();
    render(<Button variant="terminal" onClick={handleClick}>INITIALIZE PROTOCOL</Button>);

    const button = screen.getByRole('button', { name: /initialize protocol/i });
    expect(button).toBeInTheDocument();
    expect(button.className).toContain('font-mono');

    await userEvent.click(button);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('renders StatusBadge with checkmark styling when status is done', () => {
    render(<StatusBadge status="completed" />);
    const badge = screen.getByText(/✓ completed/i);
    expect(badge).toBeInTheDocument();
  });

  it('renders PriorityBadge with urgent warning motif when priority is urgent', () => {
    render(<PriorityBadge priority="Urgent" />);
    const badge = screen.getByText(/! Urgent/i);
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain('animate-pulse-slow');
  });
});

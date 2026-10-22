import * as React from 'react';
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { BetaNotice } from '@/components/shared/beta-notice';

describe('Compact beta status', () => {
  it('keeps only a short visible beta label with a privacy destination', () => {
    render(<BetaNotice />);
    const link = screen.getByRole('link', { name: /beta version.*privacy and data/i });
    expect(link).toHaveAttribute('href', '/settings/privacy');
    expect(link).toHaveTextContent(/^Beta$/);
    expect(screen.queryByText(/early closed beta/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/google gemini/i)).not.toBeInTheDocument();
  });

  it('supports keyboard focus and hover states without requiring hover-only disclosure', () => {
    render(<BetaNotice />);
    const link = screen.getByRole('link');
    expect(link.className).toContain('focus-visible:ring-2');
    expect(link).toHaveAttribute('title', expect.stringMatching(/privacy/i));
  });
});

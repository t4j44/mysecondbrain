import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { PersonContext } from '@/components/relationships/person-context';
import type { Profile } from '@/lib/relationships';

const { get } = vi.hoisted(() => ({ get: vi.fn() }));
vi.mock('@/lib/api/browser-client', () => ({ api: { get, post: vi.fn() } }));
vi.mock('@/components/relationships/enrichment-panel', () => ({ EnrichmentPanel: () => null }));
vi.mock('@/components/relationships/connection-editor', () => ({ ConnectionEditor: () => null }));
vi.mock('@/components/relationships/private-photo', () => ({ PrivatePhoto: () => null }));

const profile = (extra: Partial<Profile> = {}): Profile => ({
  person: { id: 'p1', kind: 'person', title: 'Sarah', uri: '/people/p1', name: 'Sarah', role: null, company: null, notes: null, email: 'sarah@example.test',
    phone: null, linkedin_url: null, where_met: null, when_met: null, industry: null, location: null, relationship_type: 'contact' },
  first_interaction: null, last_interaction: '2026-10-09T10:00:00Z',
  recency: { label: 'Active', days_since: 4, interaction_count: 0, explanation: '0 recorded interactions. Last recorded contact 4 days ago.', rule: 'Recency only.' },
  timeline: [], topics: [], affiliations: [], related: [], commitments: [], tasks: [], brief: [], followups: [], limits: 'Limits.', ...extra });

describe('last email on the person page', () => {
  beforeEach(() => get.mockReset());

  it('shows when you last wrote and when they last wrote, from dates only', async () => {
    get.mockResolvedValue(profile({ email_contact: { last_sent_at: '2026-10-09T10:00:00Z', last_received_at: '2026-09-30T10:00:00Z' } }));
    render(<PersonContext personId="p1" />);
    const line = await screen.findByText(/Last email, from dates only:/);
    expect(line.textContent).toMatch(/you wrote on .+ · they wrote on /);
  });

  it('shows only the direction that exists', async () => {
    get.mockResolvedValue(profile({ email_contact: { last_sent_at: null, last_received_at: '2026-09-30T10:00:00Z' } }));
    render(<PersonContext personId="p1" />);
    const line = await screen.findByText(/Last email, from dates only:/);
    expect(line.textContent).toMatch(/they wrote on /);
    expect(line.textContent).not.toMatch(/you wrote on/);
  });

  it('says nothing about email when no dates are known', async () => {
    get.mockResolvedValue(profile({ email_contact: { last_sent_at: null, last_received_at: null } }));
    render(<PersonContext personId="p1" />);
    await screen.findByText('Relationship brief');
    expect(screen.queryByText(/Last email/)).not.toBeInTheDocument();
  });

  it('still works with an older server that does not send email dates', async () => {
    get.mockResolvedValue(profile());
    render(<PersonContext personId="p1" />);
    await screen.findByText('Relationship brief');
    expect(screen.queryByText(/Last email/)).not.toBeInTheDocument();
  });
});

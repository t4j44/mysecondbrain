import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { FollowupCard } from '@/components/relationships/followup-card';
import type { Followup } from '@/lib/relationships';

const post = vi.hoisted(() => vi.fn());
vi.mock('@/lib/api/browser-client', () => ({api: {post}}));
const item: Followup = {key: 'commitment:synthetic:version', person_id: 'synthetic-person', name: 'Ahmed',
  why_now: 'You promised the deck.', context: 'Agami · ABC Ventures', suggested_action: 'Review the promise.',
  evidence: {id: 'synthetic-commitment', kind: 'commitment', title: 'Send deck', uri: '/sources/commitment/synthetic'},
  due_at: null, commitment_id: 'synthetic-commitment', recency: {label: 'Cooling', days_since: 50, interaction_count: 1, explanation: '50 days', rule: 'Recency only'}};

describe('Approved relationship actions', () => {
  beforeEach(() => { post.mockReset(); });
  it('requires an outcome and explicit approval; an uncertain retry keeps its idempotency key', async () => {
    const changed = vi.fn();
    post.mockRejectedValueOnce(new Error('Network interrupted. Retry.')).mockResolvedValueOnce({action: 'completed'});
    render(<FollowupCard item={item} onChanged={changed} />);
    fireEvent.click(screen.getByRole('button', {name: 'Mark completed'}));
    expect(post).not.toHaveBeenCalled();
    expect(screen.getByRole('button', {name: 'Confirm outcome'})).toBeDisabled();
    fireEvent.change(screen.getByLabelText('Follow-up outcome'), {target: {value: 'Sent the deck and received feedback.'}});
    fireEvent.click(screen.getByRole('button', {name: 'Confirm outcome'}));
    await screen.findByRole('alert');
    expect(changed).not.toHaveBeenCalled();
    const first = post.mock.calls[0][1];
    expect(first).toMatchObject({confirmed: true, action: 'completed', outcome: 'Sent the deck and received feedback.'});
    fireEvent.click(screen.getByRole('button', {name: 'Confirm outcome'}));
    await waitFor(() => expect(changed).toHaveBeenCalledTimes(1));
    expect(post.mock.calls[1][1].request_id).toBe(first.request_id);
  });
  it('drafting does not complete the follow-up or send a message', async () => {
    const changed = vi.fn();
    post.mockResolvedValue({draft: 'Hi Ahmed, checking in about the deck.'});
    render(<FollowupCard item={item} onChanged={changed} />);
    fireEvent.click(screen.getByRole('button', {name: 'Draft message'}));
    await waitFor(() => expect(screen.getByLabelText('Follow-up draft')).toHaveValue('Hi Ahmed, checking in about the deck.'));
    expect(post).toHaveBeenCalledWith('/relationships/people/synthetic-person/draft', {suggestion_key: item.key});
    expect(changed).not.toHaveBeenCalled();
    expect(screen.getByText(/Nothing has been sent/)).toBeInTheDocument();
  });
  it('dismissal is reviewed and keeps the underlying promise', () => {
    render(<FollowupCard item={item} onChanged={() => {}} />);
    fireEvent.click(screen.getByRole('button', {name: 'Dismiss'}));
    expect(screen.getByText(/promise and relationship history stay/)).toBeInTheDocument();
    expect(post).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', {name: 'Cancel'}));
    expect(screen.queryByRole('button', {name: 'Confirm dismissal'})).not.toBeInTheDocument();
  });
});

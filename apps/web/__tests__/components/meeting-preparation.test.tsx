import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { MeetingPreparation } from '@/components/meetings/meeting-preparation';

const { get } = vi.hoisted(() => ({ get: vi.fn() }));
vi.mock('@/lib/api/browser-client', () => ({ api: { get } }));
const result = { generated_at: '2026-10-29T12:00:00Z', more_people: false, basis: 'Saved records only.', people: [{ person: { id: 'person', title: 'Synthetic contact', uri: '/people/person' }, notes: 'Prefers a short agenda.', saved_role: '', saved_company: '', last_interaction: null, more_commitments: false, commitments: [{ source: { id: 'promise', uri: '/sources/commitment/promise' }, description: 'Send proposal', direction: 'owed_by_me', status: 'in_progress', due_at: null }] }] };
beforeEach(() => vi.resetAllMocks());

it('loads only when asked and links saved facts without inventing a deadline', async () => {
  get.mockResolvedValue(result); render(<MeetingPreparation meetingId="meeting" />);
  expect(get).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Prepare meeting' }));
  expect(await screen.findByRole('link', { name: 'Synthetic contact' })).toHaveAttribute('href', '/people/person');
  expect(screen.getByRole('link', { name: 'Send proposal' })).toHaveAttribute('href', '/sources/commitment/promise');
  expect(screen.getByText('You owe · Working · No deadline recorded')).toBeInTheDocument();
});

it('clears stale facts when reload fails and supports a deliberate retry', async () => {
  get.mockResolvedValueOnce(result).mockRejectedValueOnce(new Error('Deleted')).mockResolvedValueOnce({ ...result, people: [] });
  render(<MeetingPreparation meetingId="meeting" />);
  fireEvent.click(screen.getByRole('button', { name: 'Prepare meeting' }));
  await screen.findByRole('link', { name: 'Send proposal' });
  fireEvent.click(screen.getByRole('button', { name: 'Reload preparation' }));
  await screen.findByRole('alert'); expect(screen.queryByText('Send proposal')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Prepare meeting' }));
  expect(await screen.findByText(/No saved participants/)).toBeInTheDocument();
});

it('ignores an old meeting response after navigation', async () => {
  let finish!: (value: unknown) => void;
  get.mockReturnValue(new Promise(resolve => { finish = resolve; }));
  const view = render(<MeetingPreparation meetingId="first" />);
  fireEvent.click(screen.getByRole('button', { name: 'Prepare meeting' }));
  view.rerender(<MeetingPreparation meetingId="second" />);
  finish(result);
  await new Promise(resolve => setTimeout(resolve, 0));
  expect(screen.queryByText('Synthetic contact')).not.toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Prepare meeting' })).toBeEnabled();
});

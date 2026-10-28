import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { CommitmentCard, type Commitment } from '@/components/relationships/commitment-card';
import { ApiError } from '@/lib/api/errors';

const { post } = vi.hoisted(() => ({ post: vi.fn() }));
vi.mock('@/lib/api/browser-client', () => ({ api: { post } }));
const row: Commitment = { id: 'promise-1', description: 'Send the proposal', direction: 'owed_by_me', status: 'open', revision: 2, due_at: null, reminder_at: null, source_timezone: null, from_person_id: null, to_person_id: null };
const saved = vi.fn(), reload = vi.fn();
beforeEach(() => { vi.resetAllMocks(); saved.mockResolvedValue(undefined); reload.mockResolvedValue(undefined); });
const mount = (item = row) => render(<CommitmentCard row={item} onSaved={saved} onReload={reload} />);

it('waits for persisted acknowledgement before calling Done successful', async () => {
  let finish!: (value: unknown) => void;
  post.mockReturnValue(new Promise(resolve => { finish = resolve; }));
  mount(); fireEvent.click(screen.getByRole('button', { name: 'Done' }));
  expect(saved).not.toHaveBeenCalled();
  expect(screen.getByRole('button', { name: 'Done' })).toBeDisabled();
  finish({ action: 'done', self_reported: true, help: null });
  await waitFor(() => expect(saved).toHaveBeenCalledWith('Marked done based on your confirmation.'));
  expect(post.mock.calls[0][1]).toMatchObject({ action: 'done', expected_revision: 2 });
});

it('retries the identical request after an uncertain network result', async () => {
  post.mockRejectedValueOnce(new Error('timeout')).mockResolvedValue({ action: 'working', self_reported: false, help: null });
  mount(); fireEvent.click(screen.getByRole('button', { name: 'Working' }));
  fireEvent.click(await screen.findByRole('button', { name: 'Retry same action' }));
  await waitFor(() => expect(post).toHaveBeenCalledTimes(2));
  expect(post.mock.calls[1][1]).toEqual(post.mock.calls[0][1]);
});

it('requires reload after conflict and never retries an old revision automatically', async () => {
  post.mockRejectedValue(new ApiError(409, 'Changed'));
  mount(); fireEvent.click(screen.getByRole('button', { name: 'Done' }));
  await screen.findByText('This promise changed or is no longer available. Reload it before acting.');
  expect(screen.getByRole('button', { name: 'Done' })).toBeDisabled();
  expect(screen.queryByRole('button', { name: 'Retry same action' })).not.toBeInTheDocument();
  expect(saved).not.toHaveBeenCalled(); expect(post).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getByRole('button', { name: 'Reload promises' }));
  expect(reload).toHaveBeenCalledOnce();
});

it('requires an explicit future snooze time and sends its timezone', async () => {
  post.mockResolvedValue({ action: 'snooze', self_reported: false, help: null });
  mount(); fireEvent.click(screen.getByRole('button', { name: 'Snooze' }));
  const date = new Date(); date.setDate(date.getDate() + 2);
  const future = [date.getFullYear(), String(date.getMonth() + 1).padStart(2, '0'), String(date.getDate()).padStart(2, '0')].join('-') + 'T10:30';
  fireEvent.change(screen.getByLabelText(/Check-in time in/), { target: { value: future } });
  fireEvent.click(screen.getByRole('button', { name: 'Save check-in time' }));
  await waitFor(() => expect(post).toHaveBeenCalledOnce());
  expect(post.mock.calls[0][1]).toMatchObject({ action: 'snooze', timezone: Intl.DateTimeFormat().resolvedOptions().timeZone });
  expect(post.mock.calls[0][1].snoozed_until).toBe(new Date(future).toISOString());
});

it('shows editable sourced Help without claiming any external delivery', async () => {
  post.mockResolvedValue({ action: 'help', help: { label: 'Draft to review', text: 'Could we agree on a next step?', suggestion: 'Review the source.', sources: [{ id: row.id, kind: 'commitment', uri: '/sources/commitment/promise-1' }] } });
  mount(); fireEvent.click(screen.getByRole('button', { name: 'Help' }));
  const draft = await screen.findByLabelText('Draft to review');
  fireEvent.change(draft, { target: { value: 'My edited draft' } });
  expect(draft).toHaveValue('My edited draft');
  expect(screen.getByText(/Nothing has been sent/)).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'View commitment' })).toHaveAttribute('href', '/sources/commitment/promise-1');
  expect(saved).not.toHaveBeenCalled(); expect(post).toHaveBeenCalledOnce();
});

it('keeps actions disabled for an API response without a revision', () => {
  mount({ ...row, revision: undefined as unknown as number });
  expect(screen.getByRole('button', { name: 'Done' })).toBeDisabled();
  expect(post).not.toHaveBeenCalled();
});

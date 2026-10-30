import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { TelegramActivity, TelegramPreferences } from '@/components/settings/telegram-reminders';

const { get, put } = vi.hoisted(() => ({ get: vi.fn(), put: vi.fn() }));
vi.mock('@/lib/api/browser-client', () => ({ api: { get, put } }));
const defaults = { version: 2, timezone: 'Asia/Dhaka', quiet_start_minute: 1320, quiet_end_minute: 480, quiet_enabled: true, telegram_enabled: false, include_details: false, daily_cap: 3 };
beforeEach(() => vi.resetAllMocks());

it('requires an explicit preference save and keeps details opt-in', async () => {
  get.mockResolvedValue(defaults); put.mockResolvedValue({ ...defaults, version: 3, telegram_enabled: true });
  render(<TelegramPreferences />);
  const consent = await screen.findByLabelText('Allow check-ins in my private Telegram chat');
  expect(consent).not.toBeChecked(); expect(put).not.toHaveBeenCalled();
  expect(screen.getByLabelText('Include commitment details in Telegram messages')).not.toBeChecked();
  fireEvent.click(consent); fireEvent.click(screen.getByRole('button', { name: 'Save reminder preferences' }));
  await waitFor(() => expect(put).toHaveBeenCalledWith('/assistant/preferences', expect.objectContaining({ expected_version: 2, consent: true, telegram_enabled: true, include_details: false, timezone: 'Asia/Dhaka' })));
  expect(await screen.findByRole('status')).toHaveTextContent('previous pending reminders were cancelled');
});

it('requires a reload after an uncertain preference save', async () => {
  get.mockResolvedValue(defaults); put.mockRejectedValue(new Error('Unknown result'));
  render(<TelegramPreferences />);
  fireEvent.click(await screen.findByRole('button', { name: 'Save reminder preferences' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Saving was not confirmed');
  expect(screen.queryByRole('button', { name: 'Save reminder preferences' })).not.toBeInTheDocument();
  expect(put).toHaveBeenCalledOnce();
});

it('loads history on demand and distinguishes accepted from uncertain delivery', async () => {
  get.mockResolvedValue({ items: ['delivered', 'uncertain'].map(status => ({ id: status, commitment_id: 'promise', status, scheduled_at: '2026-10-29T12:00:00Z' })), next_offset: 20 });
  render(<TelegramActivity />); expect(get).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'View reminder history' }));
  expect(await screen.findByText('Accepted by Telegram')).toBeInTheDocument();
  expect(screen.getByText('Delivery unknown')).toBeInTheDocument();
  expect(screen.getByText(/will not resend automatically/)).toBeInTheDocument();
  expect(screen.getByText(/does not confirm that you read it/)).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Older check-ins' }));
  await waitFor(() => expect(get).toHaveBeenLastCalledWith('/assistant/activity?limit=20&offset=20'));
});

it('clears stale history when refresh fails', async () => {
  get.mockResolvedValueOnce({ items: [{ id: '1', commitment_id: 'promise', status: 'delivered', scheduled_at: '2026-10-29T12:00:00Z' }], next_offset: null }).mockRejectedValue(new Error('Offline'));
  render(<TelegramActivity />);
  fireEvent.click(screen.getByRole('button', { name: 'View reminder history' }));
  await screen.findByText('Accepted by Telegram');
  fireEvent.click(screen.getByRole('button', { name: 'View reminder history' }));
  await screen.findByRole('alert');
  expect(screen.queryByText('Accepted by Telegram')).not.toBeInTheDocument();
});

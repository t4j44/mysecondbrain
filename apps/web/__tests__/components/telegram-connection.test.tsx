import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { TelegramConnection } from '@/components/settings/telegram-connection';

const { get, post, remove } = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn(), remove: vi.fn() }));
vi.mock('@/lib/api/browser-client', () => ({ api: { get, post, delete: remove } }));
const status = (state: string, available = true) => ({ status: state, available, linked_at: null, expires_at: null });
beforeEach(() => { vi.resetAllMocks(); });

it('keeps setup unavailable when the server feature is off', async () => {
  get.mockResolvedValue(status('not_connected', false));
  render(<TelegramConnection />);
  expect(await screen.findByText('Telegram setup is not available in this release.')).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Link my Telegram' })).not.toBeInTheDocument();
  expect(post).not.toHaveBeenCalled();
});

it('shows a status failure without inventing an unlinked state and supports retry', async () => {
  get.mockRejectedValueOnce(new Error('Offline')).mockResolvedValue(status('active'));
  render(<TelegramConnection />);
  await screen.findByRole('alert');
  expect(screen.queryByText('No Telegram chat is linked.')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Refresh Telegram status' }));
  expect(await screen.findByText('Your Telegram chat is linked.')).toBeInTheDocument();
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});

it('waits for explicit user action to open a returned private bot link', async () => {
  get.mockResolvedValueOnce(status('not_connected')).mockResolvedValue(status('pending'));
  post.mockResolvedValue({ url: 'https://t.me/SyntheticBrainBot?start=synthetic', expires_at: '2026-10-28T10:10:00Z' });
  render(<TelegramConnection />);
  fireEvent.click(await screen.findByRole('button', { name: 'Link my Telegram' }));
  const link = await screen.findByRole('link', { name: 'Open Telegram and tap Start' });
  expect(link).toHaveAttribute('href', 'https://t.me/SyntheticBrainBot?start=synthetic');
  expect(screen.getByText('Reminder delivery is not available in this build. You can disconnect here or send /stop to the linked bot.')).toBeInTheDocument();
  expect(screen.queryByText('Your Telegram chat is linked.')).not.toBeInTheDocument();
});

it('refuses unexpected provider URLs', async () => {
  get.mockResolvedValue(status('not_connected'));
  post.mockResolvedValue({ url: 'https://malicious.invalid/link', expires_at: '2026-10-28T10:10:00Z' });
  render(<TelegramConnection />);
  fireEvent.click(await screen.findByRole('button', { name: 'Link my Telegram' }));
  await screen.findByRole('alert');
  expect(screen.queryByRole('link')).not.toBeInTheDocument();
});

it('lets the owner disconnect while the feature is disabled', async () => {
  get.mockResolvedValueOnce(status('active', false)).mockResolvedValue(status('revoked', false));
  remove.mockResolvedValue({ status: 'revoked' });
  render(<TelegramConnection />);
  fireEvent.click(await screen.findByRole('button', { name: 'Disconnect Telegram' }));
  await waitFor(() => expect(remove).toHaveBeenCalledWith('/assistant/connections/telegram'));
  expect(await screen.findByRole('status')).toHaveTextContent('Notification permission has been removed');
  expect(screen.queryByRole('button', { name: 'Disconnect Telegram' })).not.toBeInTheDocument();
});

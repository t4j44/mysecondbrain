import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import SettingsProfilePage from '@/app/(dashboard)/settings/profile/page';

const { getUser, updateUser, toast } = vi.hoisted(() => ({ getUser: vi.fn(), updateUser: vi.fn(), toast: vi.fn() }));
vi.mock('@/lib/supabase/client', () => ({ createClient: () => ({ auth: { getUser, updateUser } }) }));
vi.mock('@/components/ui/use-toast', () => ({ useToast: () => ({ toast }) }));
beforeEach(() => vi.resetAllMocks());

it('loads and preserves saved bio and any valid international timezone', async () => {
  getUser.mockResolvedValue({ data: { user: { user_metadata: { full_name: 'Avery Chen', bio: 'Independent consultant', timezone: 'Pacific/Auckland' } } }, error: null });
  updateUser.mockResolvedValue({ error: null });
  render(<SettingsProfilePage />);
  await waitFor(() => expect(screen.getByLabelText('Bio')).toHaveValue('Independent consultant'));
  expect(screen.getByLabelText('Timezone')).toHaveValue('Pacific/Auckland');
  fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'Avery C.' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save profile' }));
  await waitFor(() => expect(updateUser).toHaveBeenCalledWith({ data: { full_name: 'Avery C.', bio: 'Independent consultant', timezone: 'Pacific/Auckland' } }));
});

it('cannot overwrite an unavailable profile with placeholders', async () => {
  getUser.mockRejectedValue(new Error('Offline'));
  render(<SettingsProfilePage />);
  expect(await screen.findByRole('alert')).toHaveTextContent('could not be loaded');
  expect(screen.getByRole('button', { name: 'Save profile' })).toBeDisabled();
  expect(screen.getByLabelText('Full name')).toHaveValue('');
  expect(updateUser).not.toHaveBeenCalled();
});

it('retains edits and permits retry after a rejected save', async () => {
  getUser.mockResolvedValue({ data: { user: { user_metadata: { full_name: 'Avery Chen', timezone: 'Europe/London' } } } });
  updateUser.mockRejectedValue(new Error('Offline'));
  render(<SettingsProfilePage />);
  await waitFor(() => expect(screen.getByRole('button', { name: 'Save profile' })).toBeEnabled());
  fireEvent.change(screen.getByLabelText('Bio'), { target: { value: 'My edited bio' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save profile' }));
  await waitFor(() => expect(toast).toHaveBeenCalledWith(expect.objectContaining({ title: 'Profile not saved' })));
  expect(screen.getByLabelText('Bio')).toHaveValue('My edited bio');
  expect(screen.getByRole('button', { name: 'Save profile' })).toBeEnabled();
});

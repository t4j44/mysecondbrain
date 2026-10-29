import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import SettingsProfilePage from '@/app/(dashboard)/settings/profile/page';

const { getUser, updateUser, toast } = vi.hoisted(() => ({
  getUser: vi.fn(),
  updateUser: vi.fn(),
  toast: vi.fn(),
}));

vi.mock('@/lib/supabase/client', () => ({
  createClient: () => ({ auth: { getUser, updateUser } }),
}));
vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({ toast }),
}));

beforeEach(() => {
  vi.clearAllMocks();
  updateUser.mockResolvedValue({ error: null });
});

it('never submits sample or blank defaults before the real saved profile loads', async () => {
  getUser.mockReturnValue(new Promise(() => {}));
  render(<SettingsProfilePage />);
  expect(screen.getByRole('status')).toHaveTextContent('Loading your profile');
  expect(screen.getByRole('button', { name: 'Save profile' })).toBeDisabled();
  expect(screen.queryByDisplayValue('Visionary founder')).not.toBeInTheDocument();
  expect(updateUser).not.toHaveBeenCalled();
});

it('preserves existing bio and a non-listed IANA time zone when changing only the name', async () => {
  getUser.mockResolvedValue({
    data: {
      user: { user_metadata: { full_name: 'Existing User', bio: 'Important saved biography', timezone: 'Europe/Paris' } },
    },
    error: null,
  });
  render(<SettingsProfilePage />);
  expect(await screen.findByDisplayValue('Important saved biography')).toBeInTheDocument();
  expect(screen.getByLabelText('Time zone')).toHaveValue('Europe/Paris');
  fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'Updated User' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save profile' }));
  await waitFor(() => expect(updateUser).toHaveBeenCalledWith({
    data: { full_name: 'Updated User', bio: 'Important saved biography', timezone: 'Europe/Paris' },
  }));
  expect(toast).toHaveBeenCalledWith(expect.objectContaining({ title: 'Profile saved' }));
});

it('keeps saving disabled when loading the account fails', async () => {
  getUser.mockResolvedValue({ data: { user: null }, error: { message: 'Offline' } });
  render(<SettingsProfilePage />);
  expect(await screen.findByRole('alert')).toHaveTextContent("couldn't load");
  expect(screen.getByRole('button', { name: 'Save profile' })).toBeDisabled();
  expect(updateUser).not.toHaveBeenCalled();
});

it('does not claim a failed profile update was saved', async () => {
  getUser.mockResolvedValue({
    data: { user: { user_metadata: { full_name: 'Existing User', bio: '', timezone: 'UTC' } } },
    error: null,
  });
  updateUser.mockResolvedValue({ error: { message: 'Network issue' } });
  render(<SettingsProfilePage />);
  await waitFor(() => expect(screen.getByRole('button', { name: 'Save profile' })).toBeEnabled());
  fireEvent.click(screen.getByRole('button', { name: 'Save profile' }));
  await waitFor(() => expect(toast).toHaveBeenCalledWith(expect.objectContaining({
    title: 'Could not save profile',
    variant: 'destructive',
  })));
  expect(toast).not.toHaveBeenCalledWith(expect.objectContaining({ title: 'Profile saved' }));
});

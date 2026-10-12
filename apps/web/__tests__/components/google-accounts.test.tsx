import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import SettingsIntegrationsPage from '@/app/(dashboard)/settings/integrations/page';
import { groupAccounts, UNKNOWN_ACCOUNT, type Integration } from '@/lib/google-accounts';

const { get, post, del } = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn(), del: vi.fn() }));
vi.mock('@/lib/api/browser-client', () => ({ api: { get, post, delete: del } }));

const row = (id: string, provider: string, account: string | null, connected = true): Integration =>
  ({ id, provider_name: provider, account_identifier: account, is_connected: connected });

describe('grouping connections by Google account', () => {
  it('puts each capability under its account, ignores disconnected rows and other providers', () => {
    const groups = groupAccounts([
      row('1', 'google_drive', 'One@Example.test'), row('2', 'google_calendar', 'one@example.test'),
      row('3', 'google_drive', 'two@example.test'), row('4', 'google_calendar', 'two@example.test', false),
      row('5', 'github', 'one@example.test'), row('6', 'google_calendar', null)]);
    expect(groups.map(group => group.name)).toEqual(['one@example.test', 'two@example.test', UNKNOWN_ACCOUNT]);
    expect(Object.keys(groups[0].byProvider)).toEqual(['google_drive', 'google_calendar']);
    expect(Object.keys(groups[1].byProvider)).toEqual(['google_drive']);
    expect(groups[2].email).toBeUndefined();
    expect(groupAccounts([])).toEqual([]);
  });
});

// The Drive account dropdown repeats each email, so look inside the accounts section only.
const card = async (email: string) => {
  const section = await screen.findByRole('region', { name: 'Connected Google accounts' });
  return (await within(section).findByText(email)).closest('div') as HTMLElement;
};

describe('Google connections page', () => {
  const assign = vi.fn();
  beforeEach(() => {
    get.mockReset(); post.mockReset(); del.mockReset(); assign.mockReset();
    Object.defineProperty(window, 'location', { configurable: true, value: { ...window.location, assign } });
    get.mockImplementation(async (path: string) => path.startsWith('/tasks')
      ? { items: [{ id: 'task-1', title: 'Send deck' }] }
      : { items: [row('d1', 'google_drive', 'one@example.test'), row('c1', 'google_calendar', 'one@example.test'),
                  row('d2', 'google_drive', 'two@example.test')] });
  });

  it('lists each account with what it allows', async () => {
    render(<SettingsIntegrationsPage />);
    const one = await card('one@example.test');
    expect(within(one).getByText('Drive: allowed')).toBeInTheDocument();
    expect(within(one).getByText('Calendar: allowed')).toBeInTheDocument();
    const two = await card('two@example.test');
    expect(within(two).getByText('Calendar: not allowed')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Add another account for Calendar' })).toBeInTheDocument();
  });

  it('allowing another capability for a known account preselects that account at Google', async () => {
    post.mockResolvedValue({ url: 'https://accounts.google.com/o/oauth2/v2/auth?x=1' });
    render(<SettingsIntegrationsPage />);
    const two = await card('two@example.test');
    fireEvent.click(within(two).getByRole('button', { name: 'Allow Calendar' }));
    await waitFor(() => expect(assign).toHaveBeenCalledWith('https://accounts.google.com/o/oauth2/v2/auth?x=1'));
    expect(post).toHaveBeenCalledWith('/integrations/google/authorize?provider=google_calendar&login_hint=two%40example.test');
  });

  it('refuses to follow an authorization link that does not point at Google', async () => {
    post.mockResolvedValue({ url: 'https://evil.example/o/oauth2/v2/auth' });
    render(<SettingsIntegrationsPage />);
    fireEvent.click(await screen.findByRole('button', { name: 'Add another account for Drive' }));
    expect(await screen.findByText('Invalid authorization destination.')).toBeInTheDocument();
    expect(assign).not.toHaveBeenCalled();
  });

  it('disconnects exactly the chosen account', async () => {
    del.mockResolvedValue({ disconnected: true });
    render(<SettingsIntegrationsPage />);
    const two = await card('two@example.test');
    fireEvent.click(within(two).getByRole('button', { name: 'Disconnect Drive' }));
    await waitFor(() => expect(del).toHaveBeenCalledWith('/integrations/google/google_drive?integration_id=d2'));
  });

  it('asks which Drive account to export to when more than one is connected', async () => {
    post.mockResolvedValue({ id: 'job-1' });
    render(<SettingsIntegrationsPage />);
    const exportButton = await screen.findByRole('button', { name: 'Export my records to Drive' });
    expect(exportButton).toBeDisabled();
    fireEvent.change(screen.getByLabelText('Export to'), { target: { value: 'd2' } });
    expect(exportButton).toBeEnabled();
    fireEvent.click(exportButton);
    await waitFor(() => expect(post).toHaveBeenCalledWith('/sync/gdrive', { sync_mode: 'one_way', integration_id: 'd2' }, { timeoutMs: 45000 }));
  });

  it('uses the only Calendar account without asking and sends it when scheduling', async () => {
    post.mockResolvedValue({ job_id: 'job-2' });
    render(<SettingsIntegrationsPage />);
    await screen.findByText('Schedule a task');
    expect(screen.queryByLabelText('Calendar account')).not.toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole('option', { name: 'Send deck' })).toBeInTheDocument());
    fireEvent.change(screen.getByLabelText('Task'), { target: { value: 'task-1' } });
    fireEvent.change(screen.getByLabelText(/Start time/), { target: { value: '2026-11-02T10:00' } });
    fireEvent.click(screen.getByRole('button', { name: 'Schedule / reschedule' }));
    await waitFor(() => expect(post).toHaveBeenCalled());
    expect(post.mock.calls[0][0]).toBe('/integrations/google/tasks/task-1/schedule');
    expect(post.mock.calls[0][1]).toMatchObject({ integration_id: 'c1', cancel: false });
  });
});

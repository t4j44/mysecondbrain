'use client';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from '@/lib/api/browser-client';
import { groupAccounts, type Integration, type Provider, PROVIDERS, UNKNOWN_ACCOUNT } from '@/lib/google-accounts';

export default function SettingsIntegrationsPage() {
  const [items, setItems] = useState<Integration[]>([]);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [job, setJob] = useState<string | null>(null);
  const [driveAccount, setDriveAccount] = useState('');
  const load = useCallback(async () => { const data = await api.get<{ items: Integration[] }>('/integrations'); setItems(data.items); }, []);
  useEffect(() => { load().catch(error => setMessage(error.message)); }, [load]);
  const accounts = useMemo(() => groupAccounts(items), [items]);
  const driveAccounts = useMemo(() => items.filter(item => item.provider_name === 'google_drive' && item.is_connected), [items]);
  const driveChoice = driveAccount || (driveAccounts.length === 1 ? driveAccounts[0].id : '');
  const [gmailAccount, setGmailAccount] = useState('');
  const gmailAccounts = useMemo(() => items.filter(item => item.provider_name === 'gmail' && item.is_connected), [items]);
  const gmailChoice = gmailAccount || (gmailAccounts.length === 1 ? gmailAccounts[0].id : '');
  async function run(action: () => Promise<void>) {
    setBusy(true); setMessage(''); try { await action(); await load(); }
    catch (error) { setMessage(error instanceof Error ? error.message : 'Connection failed.'); } finally { setBusy(false); }
  }
  function connect(provider: Provider, hint?: string) {
    return run(async () => {
      const query = `provider=${provider}` + (hint ? `&login_hint=${encodeURIComponent(hint)}` : '');
      const data = await api.post<{ url: string }>(`/integrations/google/authorize?${query}`);
      const target = new URL(data.url); if (target.origin !== 'https://accounts.google.com') throw new Error('Invalid authorization destination.');
      window.location.assign(target.href);
    });
  }
  function disconnect(integration: Integration) {
    return run(async () => {
      await api.delete(`/integrations/google/${integration.provider_name}?integration_id=${encodeURIComponent(integration.id)}`);
      setMessage('Disconnected from Second Brain. You can also remove access in your Google account.');
    });
  }
  return <div className="space-y-6">
    <h1 className="text-2xl font-semibold">Google connections</h1>
    <p>Your private database stays authoritative. Drive exports are copies. Calendar receives only tasks you explicitly schedule. Connect as many Google accounts as you use.</p>
    <section className="space-y-4 rounded-xl border p-5" aria-label="Connected Google accounts">
      <h2 className="text-lg font-semibold">Your Google accounts</h2>
      {accounts.length === 0 && <p>No Google account is connected yet.</p>}
      {accounts.map(account => <div key={account.key} className="space-y-2 rounded-lg border p-4">
        <p className="font-medium">{account.name}</p>
        {account.name === UNKNOWN_ACCOUNT && <p className="text-sm text-muted-foreground">This connection was made before accounts were shown. Disconnect and connect it again to see which account it is.</p>}
        <ul className="space-y-2">
          {PROVIDERS.map(({ provider, label }) => {
            const integration = account.byProvider[provider];
            return <li key={provider} className="flex flex-wrap items-center justify-between gap-2">
              <span>{label}: {integration ? 'allowed' : 'not allowed'}</span>
              {integration
                ? <button disabled={busy} className="min-h-11 rounded border px-4" onClick={() => disconnect(integration)}>Disconnect {label}</button>
                : <button disabled={busy} className="min-h-11 rounded border px-4" onClick={() => connect(provider, account.email)}>Allow {label}</button>}
            </li>;
          })}
        </ul>
      </div>)}
      <div className="space-y-2">
        <p className="text-sm text-muted-foreground">Choose what to allow, then pick the Google account on the next screen.</p>
        <div className="flex flex-wrap gap-3">
          {PROVIDERS.map(({ provider, label, blurb }) => <button key={provider} disabled={busy} className="min-h-11 rounded border px-4" onClick={() => connect(provider)} title={blurb}>
            {accounts.length ? `Add another account for ${label}` : `Connect ${label}`}</button>)}
        </div>
      </div>
    </section>
    <section className="space-y-3 rounded-xl border p-5">
      <h2 className="text-lg font-semibold">Export to Google Drive</h2>
      <p className="text-sm text-muted-foreground">Export a Markdown copy of your active records to your own Drive. This includes private record text; check your Google account before exporting.</p>
      {driveAccounts.length > 1 && <AccountSelect label="Export to" integrations={driveAccounts} value={driveChoice} onChange={setDriveAccount} />}
      <button disabled={busy || !driveChoice} className="min-h-11 rounded bg-primary px-4 text-primary-foreground" onClick={() => run(async () => {
        const result = await api.post<{ id: string }>('/sync/gdrive', { sync_mode: 'one_way', integration_id: driveChoice }, { timeoutMs: 45000 });
        setJob(result.id); setMessage('Export queued. Check status below.');
      })}>Export my records to Drive</button>
      {driveAccounts.length === 0 && <p className="text-sm">Connect Drive above first.</p>}
    </section>
    <section className="space-y-3 rounded-xl border p-5">
      <h2 className="text-lg font-semibold">Email dates</h2>
      <p className="text-sm text-muted-foreground">Second Brain looks only at who sent or received each message and when, and only for people you have saved with an email address. It never reads subjects or message text, and nothing from your email is sent to an AI. Disconnecting removes the dates it imported.</p>
      {gmailAccounts.length > 1 && <AccountSelect label="Refresh from" integrations={gmailAccounts} value={gmailChoice} onChange={setGmailAccount} />}
      <button disabled={busy || !gmailChoice} className="min-h-11 rounded border px-4" onClick={() => run(async () => {
        const result = await api.post<{ id: string }>('/sync/gmail', { integration_id: gmailChoice }, { timeoutMs: 45000 });
        setJob(result.id); setMessage('Refresh queued. Check status below.');
      })}>Refresh email dates</button>
      {gmailAccounts.length === 0 && <p className="text-sm">Connect Email dates above first.</p>}
    </section>
    <ScheduleTask integrations={items.filter(item => item.provider_name === 'google_calendar' && item.is_connected)} onJob={setJob} onMessage={setMessage} />
    {job && <button disabled={busy} className="min-h-11 rounded border px-4" onClick={() => run(async () => {
      const result = await api.get<{ status: string; error_code?: string }>(`/jobs/${job}`);
      setMessage(`Job: ${result.status}${result.error_code ? ` (${result.error_code})` : ''}`);
    })}>Check latest job</button>}
    {message && <p role="status" className="rounded border p-3">{message}</p>}
  </div>;
}
function AccountSelect({ label, integrations, value, onChange }: { label: string; integrations: Integration[]; value: string; onChange: (id: string) => void }) {
  return <label className="block">{label}
    <select value={value} onChange={event => onChange(event.target.value)} className="mt-1 min-h-11 w-full rounded border bg-background p-2">
      <option value="">Choose a Google account</option>
      {integrations.map(item => <option key={item.id} value={item.id}>{item.account_identifier || UNKNOWN_ACCOUNT}</option>)}
    </select></label>;
}
function ScheduleTask({ integrations, onJob, onMessage }: { integrations: Integration[]; onJob: (id: string) => void; onMessage: (text: string) => void }) {
  const [tasks, setTasks] = useState<{ id: string; title: string }[]>([]);
  const [task, setTask] = useState(''); const [start, setStart] = useState(''); const [busy, setBusy] = useState(false);
  const [account, setAccount] = useState('');
  const choice = account || (integrations.length === 1 ? integrations[0].id : '');
  useEffect(() => { api.get<{ items: { id: string; title: string }[] }>('/tasks?limit=100').then(data => setTasks(data.items)).catch(error => onMessage(error.message)); }, [onMessage]);
  async function schedule(cancel: boolean) {
    if (!task || !start || !choice) return;
    setBusy(true); try {
      const result = await api.post<{ job_id: string }>(`/integrations/google/tasks/${task}/schedule`, {
        start: new Date(start).toISOString(), duration_minutes: 30, timezone: Intl.DateTimeFormat().resolvedOptions().timeZone, cancel,
        integration_id: choice,
      }); onJob(result.job_id); onMessage(cancel ? 'Cancellation queued.' : 'Calendar update queued.');
    } catch (error) { onMessage(error instanceof Error ? error.message : 'Could not schedule.'); } finally { setBusy(false); }
  }
  return <section className="space-y-3 rounded-xl border p-5"><h2 className="text-lg font-semibold">Schedule a task</h2>
    {integrations.length === 0 && <p className="text-sm">Connect Calendar above first.</p>}
    {integrations.length > 1 && <AccountSelect label="Calendar account" integrations={integrations} value={choice} onChange={setAccount} />}
    <label className="block">Task<select value={task} onChange={event => setTask(event.target.value)} className="mt-1 min-h-11 w-full rounded border bg-background p-2"><option value="">Choose a task</option>{tasks.map(item => <option key={item.id} value={item.id}>{item.title}</option>)}</select></label>
    <label className="block">Start time (your device timezone)<input type="datetime-local" value={start} onChange={event => setStart(event.target.value)} className="mt-1 block min-h-11 max-w-full rounded border bg-background p-2" /></label>
    <p className="text-sm">Creates or updates a 30-minute event in your primary calendar.</p>
    <div className="flex flex-wrap gap-3"><button disabled={busy || !task || !start || !choice} onClick={() => schedule(false)} className="min-h-11 rounded border px-4">Schedule / reschedule</button>
    <button disabled={busy || !task || !start || !choice} onClick={() => schedule(true)} className="min-h-11 rounded border px-4">Remove calendar event</button></div>
  </section>;
}

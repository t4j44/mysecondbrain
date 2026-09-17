'use client';
import { useCallback, useEffect, useState } from 'react';
import { api } from '@/lib/api/browser-client';
type Integration = { provider_name: string; is_connected: boolean };
export default function SettingsIntegrationsPage() {
  const [items, setItems] = useState<Integration[]>([]);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [job, setJob] = useState<string | null>(null);
  const load = useCallback(async () => { const data = await api.get<{ items: Integration[] }>('/integrations'); setItems(data.items); }, []);
  useEffect(() => { load().catch(error => setMessage(error.message)); }, [load]);
  async function run(action: () => Promise<void>) {
    setBusy(true); setMessage(''); try { await action(); await load(); }
    catch (error) { setMessage(error instanceof Error ? error.message : 'Connection failed.'); } finally { setBusy(false); }
  }
  return <div className="space-y-6">
    <h1 className="text-2xl font-semibold">Google connections</h1>
    <p>Your private database stays authoritative. Drive exports are copies. Calendar receives only tasks you explicitly schedule.</p>
    {(['google_drive', 'google_calendar'] as const).map(provider => {
      const connected = items.some(item => item.provider_name === provider && item.is_connected);
      return <section key={provider} className="space-y-3 rounded-xl border p-5">
        <h2 className="text-lg font-semibold">{provider === 'google_drive' ? 'Google Drive' : 'Google Calendar'}</h2>
        <p>{connected ? 'Connected' : 'Not connected'}</p>
        <p className="text-sm text-muted-foreground">{provider === 'google_drive' ? 'Export a Markdown copy of your active records to your own Drive. This includes private record text; check your Google account before exporting.' : 'Grant Calendar access, then choose a task and time below. No attendee invitations are sent.'}</p>
        <div className="flex flex-wrap gap-3">
          <button disabled={busy} className="min-h-11 rounded border px-4" onClick={() => run(async () => {
            const data = await api.post<{ url: string }>(`/integrations/google/authorize?provider=${provider}`);
            const target = new URL(data.url); if (target.origin !== 'https://accounts.google.com') throw new Error('Invalid authorization destination.');
            window.location.assign(target.href);
          })}>{connected ? 'Reconnect' : 'Connect'}</button>
          {connected && <>
            <button disabled={busy} className="min-h-11 rounded border px-4" onClick={() => run(async () => {
              await api.delete(`/integrations/google/${provider}`); setMessage('Disconnected from Second Brain. You can also remove access in your Google account.');
            })}>Disconnect</button>
            {provider === 'google_drive' && <button disabled={busy} className="min-h-11 rounded bg-primary px-4 text-primary-foreground" onClick={() => run(async () => {
              const result = await api.post<{ id: string }>('/sync/gdrive', { sync_mode: 'one_way' }, { timeoutMs: 45000 });
              setJob(result.id); setMessage('Export queued. Check status below.');
            })}>Export my records to Drive</button>}
          </>}
        </div>
      </section>;
    })}
    <ScheduleTask onJob={setJob} onMessage={setMessage} />
    {job && <button disabled={busy} className="min-h-11 rounded border px-4" onClick={() => run(async () => {
      const result = await api.get<{ status: string; error_code?: string }>(`/jobs/${job}`);
      setMessage(`Job: ${result.status}${result.error_code ? ` (${result.error_code})` : ''}`);
    })}>Check latest job</button>}
    {message && <p role="status" className="rounded border p-3">{message}</p>}
  </div>;
}
function ScheduleTask({ onJob, onMessage }: { onJob: (id: string) => void; onMessage: (text: string) => void }) {
  const [tasks, setTasks] = useState<{ id: string; title: string }[]>([]);
  const [task, setTask] = useState(''); const [start, setStart] = useState(''); const [busy, setBusy] = useState(false);
  useEffect(() => { api.get<{ items: { id: string; title: string }[] }>('/tasks?limit=100').then(data => setTasks(data.items)).catch(error => onMessage(error.message)); }, [onMessage]);
  async function schedule(cancel: boolean) {
    if (!task || !start) return;
    setBusy(true); try {
      const result = await api.post<{ job_id: string }>(`/integrations/google/tasks/${task}/schedule`, {
        start: new Date(start).toISOString(), duration_minutes: 30, timezone: Intl.DateTimeFormat().resolvedOptions().timeZone, cancel,
      }); onJob(result.job_id); onMessage(cancel ? 'Cancellation queued.' : 'Calendar update queued.');
    } catch (error) { onMessage(error instanceof Error ? error.message : 'Could not schedule.'); } finally { setBusy(false); }
  }
  return <section className="space-y-3 rounded-xl border p-5"><h2 className="text-lg font-semibold">Schedule a task</h2>
    <label className="block">Task<select value={task} onChange={event => setTask(event.target.value)} className="mt-1 min-h-11 w-full rounded border bg-background p-2"><option value="">Choose a task</option>{tasks.map(item => <option key={item.id} value={item.id}>{item.title}</option>)}</select></label>
    <label className="block">Start time (your device timezone)<input type="datetime-local" value={start} onChange={event => setStart(event.target.value)} className="mt-1 block min-h-11 max-w-full rounded border bg-background p-2" /></label>
    <p className="text-sm">Creates or updates a 30-minute event in your primary calendar.</p>
    <div className="flex flex-wrap gap-3"><button disabled={busy || !task || !start} onClick={() => schedule(false)} className="min-h-11 rounded border px-4">Schedule / reschedule</button>
    <button disabled={busy || !task || !start} onClick={() => schedule(true)} className="min-h-11 rounded border px-4">Remove calendar event</button></div>
  </section>;
}

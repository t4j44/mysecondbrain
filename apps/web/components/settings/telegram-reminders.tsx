'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Bell, CheckCircle2, CircleHelp, Clock3, XCircle } from 'lucide-react';
import { api } from '@/lib/api/browser-client';
import { Button } from '@/components/ui/button';

type Preferences = { version: number; timezone: string | null; quiet_start_minute: number; quiet_end_minute: number; quiet_enabled: boolean; telegram_enabled: boolean; include_details: boolean; daily_cap: number };
type Activity = { id: string; commitment_id: string; status: string; scheduled_at: string };
type ActivityPage = { items: Activity[]; next_offset: number | null };
const time = (n: number) => `${String(Math.floor(n / 60)).padStart(2, '0')}:${String(n % 60).padStart(2, '0')}`;
const minutes = (value: string) => { const [h, m] = value.split(':').map(Number); return h * 60 + m; };
const inputClass = 'min-h-11 w-full rounded-lg border bg-background px-3 text-sm';

export function TelegramPreferences() {
  const [preferences, setPreferences] = useState<Preferences | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  async function load() {
    setBusy(true); setError(''); setMessage('');
    try { const value = await api.get<Preferences>('/assistant/preferences'); setPreferences({ ...value, timezone: value.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone }); }
    catch { setError('Reminder preferences could not be loaded.'); setPreferences(null); }
    finally { setBusy(false); }
  }
  useEffect(() => { void load(); }, []);
  const update = (patch: Partial<Preferences>) => setPreferences(current => current ? { ...current, ...patch } : current);
  return <div className="space-y-3 border-t pt-4">
    <h3 className="flex items-center gap-2 font-medium"><Bell className="h-4 w-4" aria-hidden="true" />Your reminders</h3>
    {preferences && <form className="space-y-3" onSubmit={async event => {
      event.preventDefault(); setBusy(true); setError(''); setMessage('');
      try {
        const { version, ...values } = preferences;
        setPreferences(await api.put<Preferences>('/assistant/preferences', { ...values, expected_version: version, consent: values.telegram_enabled }));
        setMessage('Preferences saved. Choose a new check-in time for reminders; previous pending reminders were cancelled.');
      } catch { setError('Saving was not confirmed. Reload preferences before trying again.'); setPreferences(null); }
      finally { setBusy(false); }
    }}>
      <fieldset disabled={busy} className="space-y-3">
        <label className="flex min-h-11 items-center gap-3 text-sm"><input type="checkbox" className="h-5 w-5" checked={preferences.telegram_enabled} onChange={e => update({ telegram_enabled: e.target.checked })} />Allow check-ins in my private Telegram chat</label>
        <label className="block space-y-1 text-sm"><span>My timezone</span><input required maxLength={100} className={inputClass} value={preferences.timezone || ''} onChange={e => update({ timezone: e.target.value })} /><span className="block text-xs text-muted-foreground">Use a location such as Asia/Dhaka or Europe/London.</span></label>
        <label className="flex min-h-11 items-center gap-3 text-sm"><input type="checkbox" className="h-5 w-5" checked={preferences.quiet_enabled} onChange={e => update({ quiet_enabled: e.target.checked })} />Keep quiet hours</label>
        {preferences.quiet_enabled && <div className="grid grid-cols-2 gap-3">
          <label className="space-y-1 text-sm"><span>Quiet from</span><input type="time" required className={inputClass} value={time(preferences.quiet_start_minute)} onChange={e => update({ quiet_start_minute: minutes(e.target.value) })} /></label>
          <label className="space-y-1 text-sm"><span>Until</span><input type="time" required className={inputClass} value={time(preferences.quiet_end_minute)} onChange={e => update({ quiet_end_minute: minutes(e.target.value) })} /></label>
        </div>}
        <label className="block space-y-1 text-sm"><span>Daily reminder limit</span><select className={inputClass} value={preferences.daily_cap} onChange={e => update({ daily_cap: Number(e.target.value) })}>{[1, 2, 3, 4, 5].map(value => <option key={value} value={value}>{value} per day</option>)}</select></label>
        <label className="flex min-h-11 items-center gap-3 text-sm"><input type="checkbox" className="h-5 w-5" checked={preferences.include_details} onChange={e => update({ include_details: e.target.checked })} />Include commitment details in Telegram messages</label>
        <p className="text-xs text-muted-foreground">Details are hidden by default. Enabling them shares commitment text with Telegram.</p>
        <Button type="submit">{busy ? 'Saving…' : 'Save reminder preferences'}</Button>
      </fieldset>
    </form>}
    {!preferences && !error && <p role="status" className="text-sm">Loading reminder preferences…</p>}
    {error && <p role="alert" className="text-sm">{error}</p>}
    {message && <p role="status" className="text-sm">{message}</p>}
    <Button variant="outline" disabled={busy} onClick={() => void load()}>Reload reminder preferences</Button>
  </div>;
}

const states: Record<string, { label: string; icon: typeof Clock3 }> = {
  queued: { label: 'Scheduled', icon: Clock3 }, leased: { label: 'Preparing', icon: Clock3 },
  dispatching: { label: 'Sending', icon: Clock3 }, delivered: { label: 'Accepted by Telegram', icon: CheckCircle2 },
  uncertain: { label: 'Delivery unknown', icon: CircleHelp }, failed: { label: 'Not sent', icon: XCircle },
  cancelled: { label: 'Cancelled', icon: XCircle },
};

export function TelegramActivity() {
  const [data, setData] = useState<ActivityPage | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function load(offset = 0) {
    setBusy(true); setError(''); setData(null);
    try { setData(await api.get<ActivityPage>(`/assistant/activity?limit=20&offset=${offset}`)); }
    catch { setError('Reminder history could not be loaded. Try again.'); }
    finally { setBusy(false); }
  }
  return <div className="space-y-3 border-t pt-3">
    <Button variant="outline" disabled={busy} onClick={() => void load()}>{busy ? 'Loading history…' : 'View reminder history'}</Button>
    {error && <p role="alert" className="text-sm">{error}</p>}
    {data && <div className="space-y-3" aria-label="Reminder history">
      {data.items.length === 0 && <p className="text-sm text-muted-foreground">No scheduled check-ins yet.</p>}
      {data.items.map(item => { const state = states[item.status] || states.uncertain; const Icon = state.icon;
        return <article key={item.id} className="flex gap-3 rounded-lg border p-3">
          <Icon className="mt-1 h-5 w-5 shrink-0" aria-hidden="true" />
          <div className="min-w-0 text-sm"><p className="font-medium">{state.label}</p>
            <p className="text-muted-foreground">{new Date(item.scheduled_at).toLocaleString()}</p>
            {item.status === 'uncertain' && <p className="mt-1">Telegram may have received it. We will not resend automatically.</p>}
            {item.status === 'delivered' && <p className="mt-1 text-xs text-muted-foreground">This does not confirm that you read it.</p>}
            <Link className="inline-flex min-h-11 items-center underline underline-offset-4" href={`/sources/commitment/${encodeURIComponent(item.commitment_id)}`}>View commitment</Link>
          </div>
        </article>;
      })}
      {data.next_offset !== null && <Button variant="outline" disabled={busy} onClick={() => void load(data.next_offset!)}>Older check-ins</Button>}
    </div>}
  </div>;
}

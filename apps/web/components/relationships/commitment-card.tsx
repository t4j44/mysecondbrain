'use client';

import Link from 'next/link';
import { useState } from 'react';
import { Check, Clock3, Play, Sparkles } from 'lucide-react';
import { api } from '@/lib/api/browser-client';
import { ApiError } from '@/lib/api/errors';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export type Commitment = {
  id: string; description: string; direction: string; due_at: string | null;
  from_person_id: string | null; to_person_id: string | null;
  status: string; revision: number; reminder_at: string | null; source_timezone: string | null;
};
type Action = 'done' | 'working' | 'snooze' | 'help';
type Request = { request_id: string; expected_revision: number; action: Action; snoozed_until?: string; timezone?: string };
type Help = { label: string; text: string; suggestion: string; sources: { kind: string; id: string; uri: string }[] };
type Result = { commitment: Commitment; action: Action; self_reported: boolean; help: Help | null };
const statusLabel: Record<string, string> = { open: 'Open', in_progress: 'Working', waiting: 'Waiting', snoozed: 'Snoozed' };

export function CommitmentCard({ row, onSaved, onReload }: { row: Commitment; onSaved: (message: string) => Promise<void>; onReload: () => Promise<void> }) {
  const [busy, setBusy] = useState(false);
  const [pending, setPending] = useState<Request | null>(null);
  const [conflict, setConflict] = useState(false);
  const [error, setError] = useState('');
  const [showSnooze, setShowSnooze] = useState(false);
  const [time, setTime] = useState('');
  const [help, setHelp] = useState<Help | null>(null);
  const zone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const ready = Number.isInteger(row.revision) && row.revision > 0;
  const blocked = busy || !!pending || conflict || !ready;

  async function send(request: Request) {
    setBusy(true); setPending(request); setError(''); setHelp(null);
    try {
      const result = await api.post<Result>(`/commitments/${row.id}/action`, request);
      setPending(null);
      if (result.help) setHelp(result.help);
      else await onSaved(result.self_reported ? 'Marked done based on your confirmation.' : result.action === 'snooze' ? 'Check-in time saved. Telegram delivery is not enabled in this build.' : 'Marked as working.');
    } catch (cause) {
      if (cause instanceof ApiError && [404, 409].includes(cause.status)) {
        setConflict(true); setPending(null);
        setError('This promise changed or is no longer available. Reload it before acting.');
      } else if (cause instanceof ApiError && [400, 422].includes(cause.status)) {
        setPending(null); setError(cause.message);
      } else setError('This change was not confirmed. Retry the same action or reload its current state.');
    } finally { setBusy(false); }
  }

  function choose(action: Action) {
    if (blocked) return;
    const request: Request = { action, expected_revision: row.revision, request_id: crypto.randomUUID() };
    if (action === 'snooze') {
      const date = new Date(time);
      const [year, month, day, hour, minute] = time.split(/[-T:]/).map(Number);
      if (!time || !Number.isFinite(date.getTime()) || date.getTime() <= Date.now() ||
          date.getFullYear() !== year || date.getMonth() + 1 !== month || date.getDate() !== day || date.getHours() !== hour || date.getMinutes() !== minute) {
        setError('Choose a valid future time in your timezone.'); return;
      }
      request.snoozed_until = date.toISOString(); request.timezone = zone;
    }
    void send(request);
  }

  return <article className="space-y-3 rounded-xl border bg-card p-4 sm:p-5" aria-labelledby={`promise-${row.id}`}>
    <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
      <span className="text-muted-foreground">{row.direction === 'owed_by_me' ? 'I promised' : row.direction === 'owed_to_me' ? 'They promised' : 'Direction not recorded'}</span>
      <span className="rounded-full bg-muted px-3 py-1">{statusLabel[row.status] || row.status}</span>
    </div>
    <h2 id={`promise-${row.id}`} className="break-words font-semibold">{row.description}</h2>
    <p className="text-sm">{row.due_at ? `Due ${new Date(row.due_at).toLocaleString()}` : 'No due date recorded'}</p>
    {row.reminder_at && <p className="text-sm text-muted-foreground">Check in {new Date(row.reminder_at).toLocaleString()} · {zone}</p>}
    <div className="grid grid-cols-2 gap-2 sm:flex sm:flex-wrap">
      <Button variant={showSnooze ? 'outline' : 'default'} disabled={blocked} onClick={() => choose('done')}><Check className="h-4 w-4" aria-hidden="true" />Done</Button>
      <Button variant="outline" disabled={blocked || row.status === 'in_progress'} onClick={() => choose('working')}><Play className="h-4 w-4" aria-hidden="true" />Working</Button>
      <Button variant="outline" disabled={blocked} onClick={() => setShowSnooze(!showSnooze)} aria-expanded={showSnooze}><Clock3 className="h-4 w-4" aria-hidden="true" />Snooze</Button>
      <Button variant="outline" disabled={blocked} onClick={() => choose('help')}><Sparkles className="h-4 w-4" aria-hidden="true" />Help</Button>
    </div>
    {!ready && <p className="text-sm text-muted-foreground">Actions are unavailable until the connected API supports reviewed changes.</p>}
    {showSnooze && <form className="space-y-2 rounded-lg bg-muted/40 p-3" onSubmit={event => { event.preventDefault(); choose('snooze'); }}>
      <label htmlFor={`time-${row.id}`} className="block text-sm font-medium">Check-in time in {zone}</label>
      <Input id={`time-${row.id}`} type="datetime-local" required value={time} onChange={event => setTime(event.target.value)} disabled={blocked} />
      <p className="text-xs text-muted-foreground">The promised deadline stays the same. Telegram delivery is not enabled in this build.</p>
      <Button type="submit" disabled={blocked}>Save check-in time</Button>
    </form>}
    {help && <div className="space-y-2 rounded-lg bg-muted/40 p-3">
      <label htmlFor={`draft-${row.id}`} className="block text-sm font-semibold">{help.label}</label>
      <textarea id={`draft-${row.id}`} className="min-h-28 w-full rounded-md border bg-card p-3 text-base" value={help.text} onChange={event => setHelp({ ...help, text: event.target.value })} />
      <p className="text-sm text-muted-foreground">{help.suggestion} Nothing has been sent.</p>
      <div className="flex flex-wrap gap-3">{help.sources.map(source => <Link className="inline-flex min-h-11 items-center text-sm underline" key={source.id} href={source.uri}>View {source.kind}</Link>)}</div>
    </div>}
    {busy && <p role="status" className="text-sm">Saving your action…</p>}
    {error && <div role="alert" className="space-y-2 text-sm"><p>{error}</p><div className="flex flex-wrap gap-2">
      {pending && <Button disabled={busy} variant="outline" onClick={() => void send(pending)}>Retry same action</Button>}
      <Button disabled={busy} variant="outline" onClick={() => void onReload()}>Reload promises</Button>
    </div></div>}
    <details className="text-sm"><summary className="flex min-h-11 cursor-pointer items-center text-primary">Source and person</summary>
      <div className="flex flex-wrap gap-4"><Link className="inline-flex min-h-11 items-center underline" href={`/sources/commitment/${row.id}`}>View source</Link>
      {(row.to_person_id || row.from_person_id) && <Link className="inline-flex min-h-11 items-center underline" href={`/people/${row.to_person_id || row.from_person_id}`}>View person</Link>}</div>
    </details>
  </article>;
}

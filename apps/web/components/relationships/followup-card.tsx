'use client';

import { useRef, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api/browser-client';
import type { Followup } from '@/lib/relationships';

export function FollowupCard({item, onChanged}: {item: Followup; onChanged: () => void}) {
  const [mode, setMode] = useState<'draft' | 'scheduled' | 'completed' | 'dismissed' | null>(null);
  const [draft, setDraft] = useState('');
  const [outcome, setOutcome] = useState('');
  const [date, setDate] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const request = useRef<string | null>(null);
  async function act() {
    setBusy(true); setError('');
    request.current ||= crypto.randomUUID();
    try {
      await api.post(`/relationships/people/${item.person_id}/actions`, {confirmed: true, request_id: request.current,
        suggestion_key: item.key, action: mode, outcome: outcome || null, scheduled_at: date ? new Date(date).toISOString() : null});
      onChanged();
    } catch (error) { setError(error instanceof Error ? error.message : 'Could not save. Retry to check the same request.'); }
    finally { setBusy(false); }
  }
  const button = 'min-h-11 rounded-lg border px-3 py-2 text-sm disabled:opacity-50';
  return <article className="space-y-3 rounded-xl border bg-card p-4">
    <div className="flex flex-wrap items-center justify-between gap-2"><Link className="text-lg font-semibold underline-offset-4 hover:underline" href={`/people/${item.person_id}`}>{item.name}</Link><span className="rounded-full bg-muted px-2 py-1 text-xs">{item.recency.label}</span></div>
    <p>{item.why_now}</p>{item.context && <p className="text-sm text-muted-foreground">{item.context}</p>}
    <p className="text-sm">{item.suggested_action}</p>
    <Link className="inline-block text-sm underline" href={item.evidence.uri}>View recorded context</Link>
    <div className="flex flex-wrap gap-2">
      <button className={button} disabled={busy} onClick={async () => {
        setBusy(true); setError(''); setMode('draft'); request.current = null;
        try { const result = await api.post<{draft: string}>(`/relationships/people/${item.person_id}/draft`, {suggestion_key: item.key}); setDraft(result.draft); }
        catch (error) { setError(error instanceof Error ? error.message : 'Could not draft.'); }
        finally { setBusy(false); }
      }}>Draft message</button>
      {(['scheduled', 'completed', 'dismissed'] as const).map(action => <button className={button} disabled={busy} key={action} onClick={() => { setMode(action); setError(''); request.current = null; }}>{({scheduled: 'Schedule', completed: 'Mark completed', dismissed: 'Dismiss'})[action]}</button>)}
    </div>
    {mode === 'draft' && <div className="space-y-2"><label className="block">Review your draft<textarea aria-label="Follow-up draft" className="mt-2 w-full rounded border bg-background p-3" rows={5} value={draft} onChange={event => setDraft(event.target.value)} /></label><p className="text-sm text-muted-foreground">Copy and send this yourself after reviewing it. Nothing has been sent.</p></div>}
    {mode && mode !== 'draft' && <div className="space-y-3 border-t pt-3">
      {mode === 'completed' && <label className="block">What actually happened?<textarea aria-label="Follow-up outcome" className="mt-2 w-full rounded border bg-background p-3" maxLength={2000} rows={3} value={outcome} onChange={event => setOutcome(event.target.value)} placeholder="Sent the deck. Ahmed offered an introduction next week." /></label>}
      {mode === 'completed' && item.commitment_id && <p className="text-sm">This will complete the promise and its linked task, then save your outcome as relationship history.</p>}
      {mode === 'scheduled' && <label className="block">Remind me (your device timezone)<input className="mt-2 block min-h-11 max-w-full rounded border bg-background p-2" type="datetime-local" value={date} onChange={event => setDate(event.target.value)} /></label>}
      {mode === 'dismissed' && <p className="text-sm">Hide this suggestion. The promise and relationship history stay in your records.</p>}
      <button className={button + ' bg-primary text-primary-foreground'} disabled={busy || (mode === 'completed' && !outcome.trim()) || (mode === 'scheduled' && !date)} onClick={act}>{busy ? 'Saving…' : 'Confirm ' + ({scheduled: 'reminder', completed: 'outcome', dismissed: 'dismissal'})[mode]}</button>
      <button className={button + ' ml-2'} disabled={busy} onClick={() => setMode(null)}>Cancel</button>
    </div>}
    {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
  </article>;
}

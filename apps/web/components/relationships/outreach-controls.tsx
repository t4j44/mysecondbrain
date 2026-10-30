'use client';
import { useRef, useState } from 'react';
import { api } from '@/lib/api/browser-client';

type Opened = { id: string; channel: 'whatsapp' | 'email'; url: string; sent: false };

export function OutreachControls({personId, draft, onChanged}: {personId: string; draft: string; onChanged: () => void}) {
  const [opened, setOpened] = useState<Opened | null>(null);
  const [outcome, setOutcome] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const openRequest = useRef<{id: string; channel: string; draft: string} | null>(null);
  const sentRequest = useRef<string | null>(null);
  async function open(channel: Opened['channel']) {
    if (!draft.trim()) return;
    setBusy(true); setError('');
    // Open inside this explicit click; asynchronous work would trigger popup blocking.
    const tab = channel === 'whatsapp' ? window.open('about:blank', '_blank') : null;
    if (tab) tab.opener = null;
    if (!openRequest.current || openRequest.current.channel !== channel || openRequest.current.draft !== draft)
      openRequest.current = {id: crypto.randomUUID(), channel, draft};
    try {
      const result = await api.post<Opened>(`/relationships/people/${personId}/outreach/open`, {
        confirmed: true, request_id: openRequest.current.id, channel, message: draft, subject: 'Following up',
      });
      setOpened(result); sentRequest.current = null;
      if (channel === 'email') window.location.href = result.url;
      else if (tab) tab.location.href = result.url;
      else setError('Your browser blocked the new tab. Use the reviewed link below.');
    } catch (error) { tab?.close(); setError(error instanceof Error ? error.message : 'Could not open the draft.'); }
    finally { setBusy(false); }
  }
  async function sent() {
    if (!opened) return;
    setBusy(true); setError(''); sentRequest.current ||= crypto.randomUUID();
    try {
      await api.post(`/relationships/people/${personId}/outreach/sent`, {confirmed: true,
        request_id: sentRequest.current, opened_id: opened.id, outcome});
      setOpened(null); setOutcome(''); onChanged();
    } catch (error) { setError(error instanceof Error ? error.message : 'Could not record your confirmation. Retry safely.'); }
    finally { setBusy(false); }
  }
  const button = 'min-h-11 rounded-lg border px-3 py-2 text-sm disabled:opacity-50';
  return <div className="space-y-3">
    <p className="text-sm text-muted-foreground">Review this message, then open your app. Opening it does not record a send.</p>
    <div className="flex flex-wrap gap-2"><button className={button} disabled={busy || !draft.trim()} onClick={() => open('whatsapp')}>Open WhatsApp</button>
      <button className={button} disabled={busy || !draft.trim()} onClick={() => open('email')}>Open email</button></div>
    {opened && <div className="space-y-3 rounded-lg border p-3"><p className="font-medium">Did you send it?</p>
      <p className="text-sm">Only you can confirm what happened. Nothing is marked sent yet.</p>
      <a href={opened.url} target="_blank" rel="noopener noreferrer" className="inline-block min-h-11 py-2 text-sm underline">Reopen reviewed message</a>
      <label className="block">Outcome<textarea aria-label="Outreach outcome" className="mt-2 w-full rounded border bg-background p-2" rows={3} maxLength={2000} value={outcome} onChange={event => setOutcome(event.target.value)} placeholder="Sent my update and asked to reconnect next month." /></label>
      <div className="flex flex-wrap gap-2"><button className={button + ' bg-primary text-primary-foreground'} disabled={busy || !outcome.trim()} onClick={sent}>I sent it — record outcome</button>
        <button className={button} disabled={busy} onClick={() => setOpened(null)}>I didn’t send it</button></div>
    </div>}
    {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
  </div>;
}

'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api/browser-client';
import { ApiError } from '@/lib/api/errors';
import { Button } from '@/components/ui/button';
import { ResponsivePageContainer } from '@/components/shared/responsive-page-container';

type Draft = { status: 'draft'; host_start: string; host_end: string; guest_start: string; guest_end: string; calendar: string };
const field = 'mt-1 min-h-12 w-full rounded-lg border bg-background p-3 text-base';
function displayTime(value: string) { return value.replace('T', ' ').replace(/:00(?=[+-])/, ' '); }

export default function SchedulePage() {
  const [title, setTitle] = useState('');
  const [localStart, setLocalStart] = useState('');
  const [hostZone, setHostZone] = useState('UTC');
  const [guestZone, setGuestZone] = useState('UTC');
  const [duration, setDuration] = useState('30');
  const [location, setLocation] = useState('');
  const [occurrence, setOccurrence] = useState('');
  const [draft, setDraft] = useState<Draft | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const sequence = useRef(0);
  useEffect(() => { setHostZone(Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'); return () => { sequence.current += 1; }; }, []);
  function invalidate() { sequence.current += 1; setDraft(null); setBusy(false); setError(''); }
  async function preview(event: React.FormEvent) {
    event.preventDefault();
    const request = ++sequence.current;
    setBusy(true); setError(''); setDraft(null);
    try {
      const result = await api.post<Draft>('/meetings/schedule/preview', {
        request_id: crypto.randomUUID(), title: title.trim(), local_start: localStart,
        host_timezone: hostZone.trim(), guest_timezone: guestZone.trim(), duration_minutes: Number(duration),
        location: location.trim(), occurrence: occurrence || null,
      });
      if (request === sequence.current) setDraft(result);
    } catch (failure) {
      if (request === sequence.current) setError(failure instanceof ApiError && failure.code !== 'UNKNOWN_ERROR' ? failure.message : 'Could not prepare this draft. Check the date, time zones and connection, then retry.');
    } finally { if (request === sequence.current) setBusy(false); }
  }
  function download() {
    if (!draft) return;
    const url = URL.createObjectURL(new Blob([draft.calendar], { type: 'text/calendar;charset=utf-8' }));
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'second-brain-calendar-draft.ics'; anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return <ResponsivePageContainer>
    <Link href="/meetings" className="inline-flex min-h-11 items-center text-sm underline">Back to Meetings</Link>
    <header><h1 className="text-2xl font-semibold tracking-tight">Schedule a conversation</h1><p className="mt-2 text-muted-foreground">Prepare a calendar file to review and share manually.</p></header>
    <p className="rounded-xl border bg-card p-4 text-sm">This is a draft, not a booking. Check calendars and agree a time with your guest. Second Brain does not reserve availability, send invitations or reminders, or save this draft to your meetings.</p>
    <form onSubmit={event => void preview(event)} onChange={invalidate} className="max-w-2xl space-y-4">
      <label className="block text-sm">Title<input required maxLength={255} className={field} value={title} onChange={event => setTitle(event.target.value)} /></label>
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block text-sm">Date and time in your time zone<input required type="datetime-local" className={field} value={localStart} onChange={event => setLocalStart(event.target.value)} /></label>
        <label className="block text-sm">Duration in minutes<input required type="number" min={5} max={480} className={field} value={duration} onChange={event => setDuration(event.target.value)} /></label>
        <label className="block text-sm">Your time zone<input required maxLength={100} placeholder="Asia/Dhaka" className={field} value={hostZone} onChange={event => setHostZone(event.target.value)} /></label>
        <label className="block text-sm">Guest time zone<input required maxLength={100} placeholder="Europe/London" className={field} value={guestZone} onChange={event => setGuestZone(event.target.value)} /></label>
      </div>
      <p className="text-sm text-muted-foreground">Use a city-based time zone, such as Asia/Dhaka, Europe/London or America/New_York. Daylight-saving changes are checked before preview.</p>
      <label className="block text-sm">Location or meeting link (optional)<input maxLength={255} className={field} value={location} onChange={event => setLocation(event.target.value)} /></label>
      <details><summary className="min-h-11 cursor-pointer py-3 text-sm">If the clock repeats this time</summary>
        <label htmlFor="clock-occurrence" className="text-sm">Clock occurrence</label><select id="clock-occurrence" className={field} value={occurrence} onChange={event => setOccurrence(event.target.value)}><option value="">Ask me if this time is ambiguous</option><option value="earlier">Earlier occurrence</option><option value="later">Later occurrence</option></select>
      </details>
      <Button type="submit" disabled={busy || !title.trim()}>{busy ? 'Preparing…' : 'Review calendar draft'}</Button>
    </form>
    {error && <p role="alert" className="max-w-2xl rounded-xl border p-4 text-sm">{error}</p>}
    {draft && <section aria-label="Calendar draft" className="max-w-2xl space-y-3 rounded-xl border bg-card p-4">
      <h2 className="text-lg font-semibold">Review before downloading</h2><p className="break-words">{title}</p>
      <dl className="space-y-3 text-sm"><div><dt className="font-medium">Your time · {hostZone}</dt><dd>{displayTime(draft.host_start)} → {displayTime(draft.host_end)}</dd></div><div><dt className="font-medium">Guest time · {guestZone}</dt><dd>{displayTime(draft.guest_start)} → {displayTime(draft.guest_end)}</dd></div></dl>
      <p className="text-sm text-muted-foreground">The file contains the title, times and location you entered. It contains no saved meeting notes or contacts. Import it into your calendar to review; agree the time and send any invitation yourself. Changes or cancellations must also be handled there.</p>
      <Button onClick={download}>Download calendar file (.ics)</Button>
    </section>}
  </ResponsivePageContainer>;
}

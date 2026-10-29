'use client';
import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { CalendarDays, Search, Users, CheckCircle2, Clock3, ArrowRight } from 'lucide-react';
import { ResponsivePageContainer } from '@/components/shared/responsive-page-container';
import { CapturePanel } from '@/components/meetings/capture-panel';
import { useMeetings } from '@/hooks/useMeetings';
import { statusLabel, type Meeting } from '@/lib/meetings/types';

type Filter = 'all' | 'review' | 'processing';
const processingStates = new Set(['recording', 'uploading', 'uploaded', 'transcribing', 'extracting']);
const isReview = (meeting: Meeting) => meeting.capture?.state === 'awaiting_review';
const isProcessing = (meeting: Meeting) => processingStates.has(meeting.capture?.state || '');
function safeDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Date unavailable' : date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

export default function MeetingsPage() {
  const { meetings, loading, error, refetch } = useMeetings();
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<Filter>('all');
  const [captureOpen, setCaptureOpen] = useState(false);
  const [captureActive, setCaptureActive] = useState(false);
  useEffect(() => {
    if (new URLSearchParams(window.location.search).get('capture') === '1') setCaptureOpen(true);
  }, []);
  const counts = useMemo(() => ({
    total: meetings.length,
    review: meetings.filter(isReview).length,
    processing: meetings.filter(isProcessing).length,
  }), [meetings]);
  const filtered = useMemo(() => {
    const term = search.trim().toLocaleLowerCase();
    return meetings.filter(meeting =>
      (!term || meeting.title.toLocaleLowerCase().includes(term) || (meeting.ai_summary || '').toLocaleLowerCase().includes(term)) &&
      (filter === 'all' || (filter === 'review' ? isReview(meeting) : isProcessing(meeting)))
    );
  }, [meetings, search, filter]);

  return <ResponsivePageContainer>
    <header className="flex flex-wrap items-start justify-between gap-3">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Meetings</h1>
        <p className="text-sm text-muted-foreground">Remember conversations. Keep the promises that matter.</p>
      </div>
      <button type="button" disabled={captureActive} onClick={() => setCaptureOpen(open => !open)} aria-expanded={captureOpen} aria-controls="meeting-capture" className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-primary px-4 py-2 font-semibold text-primary-foreground disabled:opacity-60">
        {captureOpen ? 'Hide recorder' : '+ Record or upload'}
      </button>
    </header>

    {!loading && !error && meetings.length > 0 && <div className="grid grid-cols-3 gap-2 sm:gap-3" aria-label="Meeting overview">
      <div className="rounded-xl border bg-card p-3 sm:p-4"><CalendarDays className="mb-2 h-5 w-5 text-muted-foreground" aria-hidden="true" /><p className="text-xl font-semibold">{counts.total}</p><p className="text-xs text-muted-foreground">Meetings shown</p></div>
      <div className="rounded-xl border bg-card p-3 sm:p-4"><CheckCircle2 className="mb-2 h-5 w-5 text-muted-foreground" aria-hidden="true" /><p className="text-xl font-semibold">{counts.review}</p><p className="text-xs text-muted-foreground">Need review</p></div>
      <div className="rounded-xl border bg-card p-3 sm:p-4"><Clock3 className="mb-2 h-5 w-5 text-muted-foreground" aria-hidden="true" /><p className="text-xl font-semibold">{counts.processing}</p><p className="text-xs text-muted-foreground">In progress</p></div>
    </div>}

    {/* Hiding must never dispose the recorder or clear consent, title or recovery state. */}
    <div id="meeting-capture" hidden={!captureOpen}><CapturePanel onSaved={() => { void refetch(); }} onActivityChange={setCaptureActive} /></div>

    <section className="space-y-3" aria-label="Saved meetings">
      <div className="flex flex-wrap items-center justify-between gap-2"><h2 className="text-lg font-semibold">Your conversations</h2><span className="text-xs text-muted-foreground">Review before saving AI suggestions</span></div>
      <div className="flex flex-col gap-2 sm:flex-row">
        <label className="relative min-w-0 flex-1"><span className="sr-only">Search meetings</span><Search className="pointer-events-none absolute left-3 top-3.5 h-4 w-4 text-muted-foreground" aria-hidden="true" /><input type="search" value={search} onChange={event => setSearch(event.target.value)} placeholder="Find a conversation…" className="min-h-11 w-full rounded-xl border bg-background py-2 pl-10 pr-3 text-base" /></label>
        <div className="flex gap-1 rounded-xl border p-1" aria-label="Filter meetings">
          {([['all','All'],['review','Review'],['processing','In progress']] as const).map(([value,label]) => <button type="button" key={value} onClick={() => setFilter(value)} aria-pressed={filter===value} className={`min-h-11 min-w-11 flex-1 whitespace-nowrap rounded-lg px-3 text-sm sm:flex-none ${filter===value?'bg-primary text-primary-foreground':'text-muted-foreground hover:bg-accent'}`}>{label}</button>)}
        </div>
      </div>
      {loading && <p role="status" className="rounded-xl border p-4 text-sm text-muted-foreground">Loading your meetings…</p>}
      {error && <div role="alert" className="rounded-xl border p-4"><p>{error}</p><button type="button" onClick={() => void refetch()} className="mt-2 text-sm underline">Try again</button></div>}
      {!loading && !error && !meetings.length && <div className="rounded-2xl border bg-card px-5 py-8 text-center"><CalendarDays className="mx-auto mb-3 h-8 w-8 text-muted-foreground" aria-hidden="true" /><h3 className="text-lg font-semibold">Your first meeting starts here</h3><p className="mx-auto mt-2 max-w-sm text-sm text-muted-foreground">Record a conversation or upload audio. Second Brain can help you review its decisions, people and follow-ups.</p><button type="button" onClick={() => setCaptureOpen(true)} className="mt-4 min-h-11 rounded-xl bg-primary px-4 font-semibold text-primary-foreground">Record or upload</button></div>}
      {!loading && !error && meetings.length > 0 && !filtered.length && <p className="rounded-xl border p-4 text-sm text-muted-foreground">No matching meetings. Try another search or filter.</p>}
      {!loading && !error && filtered.length > 0 && <div className="grid gap-3 md:grid-cols-2">{filtered.map(meeting => <Link key={meeting.id} href={`/meetings/${meeting.id}`} className="group block min-w-0 rounded-xl border bg-card p-4 transition-colors hover:bg-accent focus-visible:outline-2 focus-visible:outline-offset-2">
        <div className="flex items-start justify-between gap-3"><div className="min-w-0"><h3 className="break-words font-semibold">{meeting.title}</h3><p className="mt-1 text-xs text-muted-foreground">{safeDate(meeting.meeting_date)}{meeting.duration_minutes ? ` · ${meeting.duration_minutes} min` : ''}</p></div><ArrowRight className="h-4 w-4 shrink-0 text-muted-foreground group-hover:text-foreground" aria-hidden="true" /></div>
        {meeting.ai_summary && <p className="mt-3 line-clamp-2 text-sm text-muted-foreground">{meeting.ai_summary}</p>}
        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs"><span className="rounded-full bg-secondary px-2.5 py-1 text-secondary-foreground">{meeting.capture ? statusLabel(meeting.capture.state) : 'Notes saved'}</span>{meeting.participant_person_ids?.length > 0 && <span className="inline-flex items-center gap-1 text-muted-foreground"><Users className="h-3.5 w-3.5" aria-hidden="true" />{meeting.participant_person_ids.length} people</span>}{meeting.action_items?.length > 0 && <span className="text-muted-foreground">{meeting.action_items.length} action items</span>}</div>
      </Link>)}</div>}
    </section>
  </ResponsivePageContainer>;
}

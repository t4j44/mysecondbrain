'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { ResponsivePageContainer } from '@/components/shared/responsive-page-container';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api/browser-client';
import { ApiError } from '@/lib/api/errors';
import { meetingApi } from '@/lib/meetings/api';
import { meetingSession } from '@/components/meetings/capture-panel';
import { EvidenceLinks, MeetingEvidenceNavigation, MeetingOutputs } from '@/components/meetings/meeting-outputs';
import { MeetingPreparation } from '@/components/meetings/meeting-preparation';
import { env } from '@/lib/env';
import { statusLabel, type Candidate, type EvidenceRef, type Meeting } from '@/lib/meetings/types';

type Person = { id: string; name: string };
const labels: Record<string, string> = { decisions: 'Decisions', action_items: 'Next steps', commitments: 'Promises', follow_ups: 'Follow-ups', important_facts: 'Important facts', customer_feedback: 'Customer feedback', questions_open: 'Open questions', people_mentions: 'People mentioned', venture_candidates: 'Businesses mentioned', project_candidates: 'Projects mentioned', relationship_updates: 'Relationship notes', memory_candidates: 'Things to remember', lesson_candidates: 'Lessons', risks: 'Risks', ideas: 'Ideas', important_numbers_or_dates: 'Important numbers or dates' };
export default function MeetingDetailPage() {
  const params = useParams(); const router = useRouter(); const id = params?.meetingId as string;
  const [meeting, setMeeting] = useState<Meeting | null>(null); const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  const [people, setPeople] = useState<Person[]>([]); const [search, setSearch] = useState(''); const [selected, setSelected] = useState<string[]>([]); const [initialized, setInitialized] = useState(false);
  const [newName, setNewName] = useState(''); const [player, setPlayer] = useState('');
  const [transcriptSearch, setTranscriptSearch] = useState('');
  const loadSequence = useRef(0);
  const [evidenceTarget, setEvidenceTarget] = useState<Pick<EvidenceRef, 'segment_id' | 'start_seconds'> | null>(null);
  const [evidenceNotice, setEvidenceNotice] = useState('');
  const refresh = useCallback(async (resetSelection = false) => {
    const sequence = ++loadSequence.current;
    setError('');
    try { const result = await meetingApi.get(id); if (sequence === loadSequence.current) { setMeeting(result); if (resetSelection) { setSelected([]); setInitialized(false); } } }
    catch { if (sequence === loadSequence.current) setError("Couldn't load this meeting. Retry."); }
  }, [id]);
  useEffect(() => {
    setMeeting(null); setInitialized(false); setSelected([]); setPlayer(''); setTranscriptSearch(''); setEvidenceNotice(''); setEvidenceTarget(null);
    void refresh();
    try { if (window.location.hash.startsWith('#segment-')) setEvidenceTarget({ segment_id: decodeURIComponent(window.location.hash.slice(9)), start_seconds: 0 }); } catch { /* A malformed URL is not a source reference. */ }
    return () => { loadSequence.current += 1; };
  }, [id, refresh]);
  useEffect(() => {
    if (!evidenceTarget || !meeting) return;
    const segment = document.getElementById(`segment-${evidenceTarget.segment_id}`);
    if (!segment) { setEvidenceNotice('This source segment is unavailable. Review the saved transcript before acting.'); setEvidenceTarget(null); return; }
    const details = segment.closest('details'); if (details) details.open = true;
    segment.focus(); segment.scrollIntoView?.({ block: 'center', behavior: 'instant' });
    window.history.replaceState(window.history.state, '', `#segment-${encodeURIComponent(evidenceTarget.segment_id)}`);
    const audio = document.getElementById('meeting-recording');
    if (audio instanceof HTMLAudioElement) audio.currentTime = evidenceTarget.start_seconds;
    setEvidenceTarget(null);
  }, [evidenceTarget, meeting]);
  function navigateEvidence(ref: EvidenceRef) { setEvidenceNotice(''); setTranscriptSearch(''); setEvidenceTarget({ segment_id: ref.segment_id, start_seconds: ref.start_seconds }); }
  const processing = ['uploaded', 'transcribing', 'extracting'].includes(meeting?.capture?.state || '');
  useEffect(() => { if (!processing) return; const timer = setInterval(() => { if (!document.hidden) void refresh(); }, 5000); return () => clearInterval(timer); }, [id, processing]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { const timer = setTimeout(() => { void api.get<Person[]>('/meetings/people-search', { params: { q: search } }).then(setPeople).catch(() => undefined); }, 250); return () => clearTimeout(timer); }, [search]);
  useEffect(() => { if (meeting?.capture?.intelligence.summary && !initialized) { setSelected(Object.entries(meeting.capture.intelligence).flatMap(([key, value]) => Array.isArray(value) && key in labels ? value.map((_, i) => `${key}:${i}`) : [])); setInitialized(true); } }, [meeting, initialized]);
  useEffect(() => () => { if (player.startsWith('blob:')) URL.revokeObjectURL(player); }, [player]);
  async function action(work: () => Promise<unknown>) { setBusy(true); setError(''); try { await work(); await refresh(); } catch (err) { setError(err instanceof ApiError && err.status === 409 ? 'This review has changed. Reload the meeting and review the latest details before saving.' : "Couldn't save this change. Check the details and retry."); } finally { setBusy(false); } }
  async function play() { await action(async () => { const session = await meetingSession(); const response = await fetch(`${env.NEXT_PUBLIC_API_BASE_URL.replace(/\/$/, '')}/meetings/${id}/recording`, { headers: { Authorization: `Bearer ${session.access_token}` } }); if (!response.ok) throw new Error('Recording expired'); const url = response.headers.get('content-type')?.includes('application/json') ? (await response.json()).url : URL.createObjectURL(await response.blob()); setPlayer(url); }); }
  if (!meeting) return <ResponsivePageContainer><Link href="/meetings">Back to meetings</Link><p role={error ? 'alert' : 'status'} className="mt-6">{error || 'Loading meeting...'}</p>{error && <Button className="mt-4" onClick={() => void refresh()}>Try again</Button>}</ResponsivePageContainer>;
  const capture = meeting.capture; const intelligence = capture?.intelligence; const speakers = [...new Set(capture?.transcript_segments.map(s => s.speaker_local_id) || [])];
  const speakerName = (speaker?: string | null) => { const mapping = speaker ? capture?.speaker_mappings[speaker] : undefined; return mapping?.kind === 'me' ? 'You' : mapping?.kind === 'person' ? people.find(p => p.id === mapping.person_id)?.name || 'Saved person' : 'Unknown'; };
  const reviewing = capture?.state === 'awaiting_review'; const candidates = Object.entries(intelligence || {}).filter(([key, value]) => key in labels && Array.isArray(value)) as [string, Candidate[]][];
  const executiveSummary = intelligence?.executive_summary || intelligence?.summary || meeting.ai_summary || 'Your meeting summary will appear here when processing finishes.';
  const reviewToken = meeting.review_token || '';
  return <MeetingEvidenceNavigation.Provider value={navigateEvidence}><ResponsivePageContainer>
    <Link href="/meetings" className="text-sm text-muted-foreground">← Back to meetings</Link>
    <h1 className="mt-5 break-words text-2xl font-semibold sm:text-3xl">{meeting.title}</h1><p className="mt-2 text-sm text-muted-foreground">{new Date(meeting.meeting_date).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' })} · {meeting.duration_minutes} min · Meeting timezone: {String(meeting.metadata?.timezone || 'Unknown')} · {meeting.location || 'Location unknown'}</p>
    <MeetingPreparation key={id} meetingId={id} />
    {capture && <p className="mt-4" role="status">{statusLabel(capture.state)}</p>}{error && <p className="mt-4 text-sm text-red-500" role="alert">{error}</p>}
    {capture?.state === 'failed' && <Button className="mt-4" disabled={busy} onClick={() => void action(() => meetingApi.retry(id))}>Retry processing</Button>}
    {error && <Button variant="outline" className="mt-3" disabled={busy} onClick={() => void refresh(true)}>Reload meeting</Button>}
    {reviewing && !reviewToken && <p role="alert" className="mt-3 text-sm">Review is unavailable on this server version. Reload after the app and server have been updated together.</p>}
    <section className="mt-6 rounded-xl border border-border bg-card p-4 sm:p-6"><h2 className="font-semibold">At a glance</h2><p className="mt-2 text-xs text-muted-foreground">AI draft — verify important claims against the transcript.</p><p className="mt-3 whitespace-pre-wrap break-words text-base leading-relaxed">{executiveSummary.length > 300 ? executiveSummary.slice(0, 300).trimEnd() + '…' : executiveSummary}</p>{executiveSummary.length > 300 && <details className="mt-3"><summary className="min-h-11 cursor-pointer py-2 text-sm font-medium">Full executive summary</summary><p className="whitespace-pre-wrap text-base leading-relaxed">{executiveSummary}</p></details>}</section>
    {reviewing && candidates.some(([, values]) => values.length) && <a href="#meeting-review" className="mt-4 inline-flex min-h-12 items-center rounded-xl bg-primary px-4 font-medium text-primary-foreground" onClick={() => { const details = document.getElementById('meeting-candidates'); if (details instanceof HTMLDetailsElement) details.open = true; }}>Review follow-ups</a>}
    {evidenceNotice && <p role="alert" className="mt-3 rounded-xl border p-3 text-sm">{evidenceNotice}</p>}
    {!!speakers.length && <section className="mt-6 space-y-4 rounded-xl border border-border bg-card p-4 sm:p-6"><h2 className="font-semibold">People</h2><p className="text-sm text-muted-foreground">Tell us who spoke. Voices in each part of a long recording are kept separate until you name them.</p>
      {reviewing && <><label className="block text-sm">Search your people<input className="mt-2 w-full rounded-md border border-input bg-background p-3" value={search} onChange={e => setSearch(e.target.value)} placeholder="Search a name" /></label><div className="flex flex-wrap gap-2"><input aria-label="New person name" className="min-w-0 flex-1 rounded-md border border-input bg-background p-3 text-sm" value={newName} onChange={e => setNewName(e.target.value)} placeholder="Add a new person" /><Button variant="outline" disabled={busy || !newName.trim()} onClick={() => void action(async () => { const person = await api.post<Person>('/people', { name: newName.trim() }); setPeople(current => [...current, person]); setNewName(''); })}>Add person</Button></div></>}
      {speakers.map((speaker, index) => { const mapping = capture?.speaker_mappings[speaker]; return <div key={speaker} className="space-y-2 border-t border-border pt-3"><label className="block text-sm">Speaker {index + 1} · part {Number(speaker.match(/^c(\d+)/)?.[1] || 0) + 1}{reviewing ? <select className="mt-2 min-h-12 w-full rounded-md border border-input bg-background p-3" aria-label={`Map speaker ${index + 1}`} disabled={busy || !reviewToken} value={mapping?.kind === 'person' ? mapping.person_id || '' : mapping?.kind || 'unknown'} onChange={e => { const value = e.target.value; void action(() => meetingApi.map(id, speaker, { kind: value === 'me' || value === 'unknown' ? value : 'person', person_id: value === 'me' || value === 'unknown' ? null : value }, reviewToken)); }}><option value="unknown">Leave unknown</option><option value="me">This is me</option>{mapping?.kind === 'person' && !people.some(p => p.id === mapping.person_id) && <option value={mapping.person_id || ''}>Saved person</option>}{people.map(person => <option key={person.id} value={person.id}>{person.name}</option>)}</select> : <p className="mt-2 text-muted-foreground">{mapping?.kind === 'me' ? 'You' : mapping?.kind === 'person' ? <Link href={`/people/${mapping.person_id}`}>{people.find(p => p.id === mapping.person_id)?.name || 'View person'}</Link> : 'Unknown'}</p>}</label></div>; })}
    </section>}
    {candidates.some(([, values]) => values.length) && <section id="meeting-review" className="mt-6 scroll-mt-20 space-y-4 rounded-xl border border-border bg-card p-4 sm:p-6"><h2 className="font-semibold">Decisions and actions</h2><p className="text-sm text-muted-foreground">{reviewing ? 'Review these suggestions before saving them to your people and plans.' : 'Selected details saved with their source evidence.'}</p>{(['decisions', 'action_items', 'commitments', 'follow_ups'] as const).map(key => { const values = intelligence?.[key] as Candidate[] | undefined; const count = values?.filter((_item, index) => !capture?.confirmed_at || capture.receipt?.selected?.includes(`${key}:${index}`)).length || 0; return !!count && <p key={key} className="text-sm">{count} {count === 1 ? ({ decisions: 'decision', action_items: 'next step', commitments: 'promise', follow_ups: 'follow-up' } as Record<string, string>)[key] : labels[key].toLowerCase()}</p>; })}
      <details id="meeting-candidates"><summary className="min-h-11 cursor-pointer py-3 text-sm font-medium">Review details</summary><div className="space-y-6">{candidates.map(([key, values]) => !!values.length && <div key={key}><h3 className="font-semibold">{labels[key]}</h3>{values.map((item, index) => <div key={index} className="mt-3 rounded-md border border-border p-3 text-sm">{reviewing ? <label className="flex items-start gap-3"><input type="checkbox" className="mt-1 h-4 w-4 shrink-0" checked={selected.includes(`${key}:${index}`)} onChange={e => setSelected(current => e.target.checked ? [...current, `${key}:${index}`] : current.filter(k => k !== `${key}:${index}`))} /><span className="break-words">{item.description}</span></label> : <p className="break-words">{item.description}</p>}{capture?.confirmed_at && !capture.receipt?.selected?.includes(`${key}:${index}`) && <p className="mt-2 text-muted-foreground">Not saved</p>}{(item.from_speaker || item.to_speaker) && <p className="mt-2 text-muted-foreground">{speakerName(item.from_speaker)} → {speakerName(item.to_speaker)}</p>}{item.interpretation && <p className="mt-2 text-muted-foreground">Interpretation — check carefully</p>}{item.due_at && <p className="mt-2">Due: {new Date(item.due_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}</p>}<blockquote className="mt-2 break-words border-l-2 border-border pl-3 text-muted-foreground">{item.evidence_text}</blockquote>{item.condition && <p className="mt-2">Condition: {item.condition}</p>}<EvidenceLinks evidence={item.evidence} /></div>)}</div>)}</div></details>
      {reviewing && <Button className="min-h-12 w-full sm:w-auto" disabled={busy || !reviewToken} onClick={() => void action(() => meetingApi.confirm(id, selected, reviewToken))}>{busy ? 'Saving...' : selected.length === candidates.reduce((n, [, values]) => n + values.length, 0) ? 'Save all' : 'Save selected'}</Button>}{capture?.confirmed_at && <p className="text-sm">Saved to your people and plans ✓</p>}
    </section>}
    {reviewing && !candidates.some(([, values]) => values.length) && <Button className="mt-6 min-h-12" disabled={busy || !reviewToken} onClick={() => void action(() => meetingApi.confirm(id, [], reviewToken))}>Save meeting</Button>}
    <MeetingOutputs key={id} meeting={meeting} refresh={refresh} />
    <details className="mt-6 rounded-xl border border-border bg-card p-4 sm:p-6"><summary className="min-h-11 cursor-pointer font-semibold">View transcript</summary><label className="mt-4 block text-sm">Search transcript<input className="mt-2 min-h-12 w-full rounded border bg-background p-3" value={transcriptSearch} onChange={e => setTranscriptSearch(e.target.value)} /></label><div className="mt-4 max-h-[36rem] space-y-4 overflow-auto">{capture?.transcript_segments.length ? capture.transcript_segments.filter(s => (s.text || '').toLocaleLowerCase().includes(transcriptSearch.toLocaleLowerCase())).map((s, i) => <article tabIndex={-1} id={`segment-${s.segment_id}`} key={s.segment_id || i} className="scroll-mt-6 rounded border p-3"><p className="text-xs text-muted-foreground">{s.segment_id} · {speakerName(s.speaker_local_id)} ({s.speaker_local_id}) · {Number(s.start_offset || 0).toFixed(1)}s</p><p className="mt-2 whitespace-pre-wrap break-words text-sm">{s.text}</p></article>) : <p className="whitespace-pre-wrap break-words text-sm">{meeting.transcript_text || 'The final transcript is not ready yet.'}</p>}</div></details>
    {capture && !capture.audio_deleted_at && <details className="mt-6 rounded-xl border border-border bg-card p-4 sm:p-6"><summary className="cursor-pointer font-semibold">Play recording</summary><p className="mt-3 text-sm text-muted-foreground">{capture.retained_until ? `Available until ${new Date(capture.retained_until).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}.` : 'Available while processing.'}</p><Button className="mt-3" variant="outline" disabled={busy} onClick={() => void play()}>Load private recording</Button>{player && <audio id="meeting-recording" className="mt-3 w-full max-w-full" controls src={player} />}</details>}
    <Button className="mt-8" variant="ghost" disabled={busy} onClick={() => { if (window.confirm('Delete this meeting and its recording?')) void action(async () => { await meetingApi.remove(id); router.push('/meetings'); }); }}>Delete meeting</Button>
  </ResponsivePageContainer></MeetingEvidenceNavigation.Provider>;
}

'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api/browser-client';
import { ApiError } from '@/lib/api/errors';
import { Button } from '@/components/ui/button';
import type { EvidenceRef, Meeting } from '@/lib/meetings/types';

type NoteRevision = { version: number; markdown: string; updated_at: string };
type Notes = { version: number; markdown: string; author?: string; revisions?: NoteRevision[] };

export function EvidenceLinks({ evidence = [] }: { evidence?: EvidenceRef[] }) {
  return <div className="mt-2 flex flex-wrap gap-2">{evidence.map((ref, i) => <a key={`${ref.segment_id}-${i}`} className="inline-flex min-h-11 items-center rounded border px-3 text-xs underline" href={`#segment-${encodeURIComponent(ref.segment_id)}`} onClick={() => {
    const segment = document.getElementById(`segment-${ref.segment_id}`);
    const details = segment?.closest('details');
    if (details) details.open = true;
    const audio = document.getElementById('meeting-recording');
    if (audio instanceof HTMLAudioElement) audio.currentTime = ref.start_seconds;
  }}>Source {ref.segment_id} · {Math.floor(ref.start_seconds / 60)}:{String(Math.floor(ref.start_seconds % 60)).padStart(2, '0')}</a>)}</div>;
}

function notesFromMetadata(meeting: Meeting): Notes | null {
  const value = meeting.metadata?.meeting_notes;
  if (value && typeof value === 'object' && 'version' in value && 'markdown' in value && typeof value.version === 'number' && typeof value.markdown === 'string') return { version: value.version, markdown: value.markdown };
  return null;
}

function aiNotes(meeting: Meeting) {
  const sections = meeting.capture?.intelligence.discussion_sections || [];
  return sections.map(s => `## ${s.title}\n${s.key_points.length ? s.key_points.map(p => `- ${p.text}`).join('\n') : `- ${s.summary}`}\n${s.evidence.map(r => `[Source ${r.segment_id} @ ${r.start_seconds}s](/meetings/${meeting.id}#segment-${encodeURIComponent(r.segment_id)})`).join(' ')}`).join('\n\n') || meeting.capture?.intelligence.summary || '';
}

export function MeetingOutputs({ meeting, refresh }: { meeting: Meeting; refresh: () => Promise<void> }) {
  const [notes, setNotes] = useState(() => notesFromMetadata(meeting) || { version: 0, markdown: aiNotes(meeting) });
  const [dirty, setDirty] = useState(false);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [minutes, setMinutes] = useState('');
  const [title, setTitle] = useState(meeting.title);
  const [purpose, setPurpose] = useState(String(meeting.metadata?.purpose || ''));
  const [agenda, setAgenda] = useState(String(meeting.metadata?.agenda || ''));
  const [zone, setZone] = useState(String(meeting.metadata?.timezone || ''));
  const [reviewDirty, setReviewDirty] = useState(false);
  const [reviewVersion, setReviewVersion] = useState(Number(meeting.metadata?.review_version || 0));
  const [projects, setProjects] = useState<{ id: string; name: string }[]>([]);
  const [ventures, setVentures] = useState<{ id: string; name: string }[]>([]);
  const [projectId, setProjectId] = useState(String(meeting.metadata?.project_id || ''));
  const [ventureId, setVentureId] = useState(meeting.venture_id || '');
  const data = meeting.capture?.intelligence;
  useEffect(() => {
    if (!dirty) { const incoming = notesFromMetadata(meeting) || { version: 0, markdown: aiNotes(meeting) }; setNotes(current => incoming.version >= current.version ? incoming : current); }
    if (!reviewDirty) {
      setTitle(meeting.title); setPurpose(String(meeting.metadata?.purpose || '')); setAgenda(String(meeting.metadata?.agenda || '')); setZone(String(meeting.metadata?.timezone || ''));
      setReviewVersion(Number(meeting.metadata?.review_version || 0));
      setProjectId(String(meeting.metadata?.project_id || '')); setVentureId(meeting.venture_id || '');
    }
  }, [meeting, dirty, reviewDirty]);
  useEffect(() => {
    let active = true;
    Promise.allSettled([api.get<{ items: { id: string; name: string }[] }>('/projects?limit=100'), api.get<{ items: { id: string; name: string }[] }>('/ventures?limit=100')]).then(results => {
      if (!active) return;
      if (results[0].status === 'fulfilled') setProjects(results[0].value.items || []);
      if (results[1].status === 'fulfilled') setVentures(results[1].value.items || []);
    });
    return () => { active = false; };
  }, []);
  useEffect(() => {
    if (!meeting.capture) return;
    let active = true;
    api.get<string>(`/meetings/${meeting.id}/export/markdown`, { params: { kind: 'minutes' } }).then(value => { if (active && typeof value === 'string') setMinutes(value); }).catch(() => { if (active) setMinutes('Minutes could not be loaded. Refresh to retry.'); });
    return () => { active = false; };
  }, [meeting.id, meeting.capture?.confirmed_at, meeting.metadata?.review_version, meeting.capture?.state, meeting.capture?.intelligence, meeting.capture?.speaker_mappings]); // eslint-disable-line react-hooks/exhaustive-deps
  async function perform(work: () => Promise<void>) {
    setBusy(true); setMessage('');
    try { await work(); } catch (error) { setMessage(error instanceof ApiError && error.status === 409 ? 'Conflict: your edit is not saved. Copy it, reload the saved version, and compare before retrying.' : 'This change was not saved. Retry when connected.'); } finally { setBusy(false); }
  }
  if (!meeting.capture) return null;
  return <>
    <section className="mt-6 space-y-3 rounded-xl border bg-card p-4 sm:p-6"><h2 className="font-semibold">Purpose and agenda</h2>
      <p className="text-sm text-muted-foreground">{meeting.capture.confirmed_at ? 'Reviewed meeting details' : 'AI suggestions remain proposals until you apply and save them.'}</p>
      {data?.suggested_title && <div className="break-words text-sm">Suggested title: {data.suggested_title.text}<EvidenceLinks evidence={data.suggested_title.evidence} /></div>}
      {data?.purpose && <div className="break-words text-sm">Suggested purpose: {data.purpose.text}<EvidenceLinks evidence={data.purpose.evidence} /></div>}
      {data?.agenda_items?.map((item, i) => <div className="text-sm" key={i}>Proposed agenda ({item.source}): {item.text}<EvidenceLinks evidence={item.evidence} /></div>)}
      {!meeting.capture.confirmed_at && <details><summary className="min-h-11 cursor-pointer py-3">Edit meeting details</summary><div className="space-y-3">
        <label className="block text-sm">Title<input className="mt-1 min-h-12 w-full rounded border bg-background p-3" value={title} onChange={e => { setTitle(e.target.value); setReviewDirty(true); }} /></label>
        <label className="block text-sm">Purpose<textarea className="mt-1 w-full rounded border bg-background p-3" value={purpose} onChange={e => { setPurpose(e.target.value); setReviewDirty(true); }} /></label>
        <label className="block text-sm">Agenda<textarea className="mt-1 w-full rounded border bg-background p-3" value={agenda} onChange={e => { setAgenda(e.target.value); setReviewDirty(true); }} /></label>
        <label className="block text-sm">Meeting timezone<input placeholder="Unknown, or Asia/Dhaka" className="mt-1 min-h-12 w-full rounded border bg-background p-3" value={zone} onChange={e => { setZone(e.target.value); setReviewDirty(true); }} /></label>
        <label className="block text-sm">Linked project<select className="mt-1 min-h-12 w-full rounded border bg-background p-3" value={projectId} onChange={e => { setProjectId(e.target.value); setReviewDirty(true); }}><option value="">Ignore / no project link</option>{projectId && !projects.some(p => p.id === projectId) && <option value={projectId}>Current project</option>}{projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
        <label className="block text-sm">Linked venture<select className="mt-1 min-h-12 w-full rounded border bg-background p-3" value={ventureId} onChange={e => { setVentureId(e.target.value); setReviewDirty(true); }}><option value="">Ignore / no venture link</option>{ventureId && !ventures.some(v => v.id === ventureId) && <option value={ventureId}>Current venture</option>}{ventures.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}</select></label>
        <p className="text-sm text-muted-foreground">Create a missing project or venture explicitly in Work, then return to link it. Mentions alone create no records.</p>
        <Button disabled={busy || !title.trim()} onClick={() => void perform(async () => { await api.put(`/meetings/${meeting.id}/review`, { expected_version: reviewVersion, title, purpose, agenda, timezone: zone || null, project_id: projectId || null, venture_id: ventureId || null }); setReviewDirty(false); await refresh(); setMessage('Meeting details reviewed.'); })}>Save reviewed details</Button>
      </div></details>}
      <p className="whitespace-pre-wrap break-words text-sm">{String(meeting.metadata?.purpose || 'Purpose not reviewed.')}<br />{String(meeting.metadata?.agenda || 'Agenda not provided.')}</p>
    </section>
    {!!data?.discussion_sections?.length && <section className="mt-6 space-y-5 rounded-xl border bg-card p-4 sm:p-6"><h2 className="font-semibold">Detailed summary</h2><p className="text-sm text-muted-foreground">AI draft — check claims against their source.</p>
      {data.discussion_sections.filter(s => !['secondary', 'side'].includes(s.kind)).map(s => <article key={s.id}><h3 className="font-medium">{s.title}</h3><p className="mt-2 whitespace-pre-wrap break-words text-sm leading-relaxed">{s.summary}</p><ul className="mt-2 list-inside list-disc text-sm">{s.key_points.map((p, i) => <li className="break-words" key={i}>{p.text}<EvidenceLinks evidence={p.evidence} /></li>)}</ul><EvidenceLinks evidence={s.evidence} /></article>)}
      {data.discussion_sections.some(s => ['secondary', 'side'].includes(s.kind)) && <div><h3 className="font-semibold">Other important discussions</h3>{data.discussion_sections.filter(s => ['secondary', 'side'].includes(s.kind)).map(s => <article key={s.id} className="mt-4"><h4 className="font-medium">{s.title}</h4><p className="mt-2 whitespace-pre-wrap break-words text-sm leading-relaxed">{s.summary}</p>{s.key_points.map((p, i) => <div className="mt-2 break-words text-sm" key={i}>{p.text}<EvidenceLinks evidence={p.evidence} /></div>)}<EvidenceLinks evidence={s.evidence} /></article>)}</div>}
    </section>}
    <section className="mt-6 space-y-3 rounded-xl border bg-card p-4 sm:p-6"><h2 className="font-semibold">Meeting notes</h2><p className="text-sm text-muted-foreground">{notes.version ? `Your notes · version ${notes.version}` : 'AI draft · not saved'}{dirty ? ' · Unsaved edits' : ''}. Editing notes does not confirm tasks or promises.</p>
      <textarea aria-label="Meeting notes" className="min-h-64 w-full rounded border bg-background p-3 text-sm" value={notes.markdown} onChange={e => { setNotes(n => ({ ...n, markdown: e.target.value })); setDirty(true); }} />
      <div className="flex flex-wrap gap-2"><Button disabled={busy || !dirty} onClick={() => void perform(async () => { const saved = await api.put<Notes>(`/meetings/${meeting.id}/notes`, { expected_version: notes.version, markdown: notes.markdown }); setNotes(saved); setDirty(false); await refresh(); setMessage('Notes saved.'); })}>Save notes</Button>
        <Button variant="outline" onClick={() => void perform(async () => { await navigator.clipboard.writeText(notes.markdown); setMessage('Notes copied.'); })}>Copy notes</Button>
        <Button variant="outline" onClick={() => void perform(async () => { const saved = await api.get<Notes>(`/meetings/${meeting.id}/notes`); if (window.confirm('Replace the editor with the latest saved notes? Copy unsaved edits first.')) { setNotes(saved); setDirty(false); } })}>Reload saved notes</Button>
      </div>
      <details><summary className="min-h-11 cursor-pointer py-3">Compare saved note revisions</summary><Button variant="outline" onClick={() => void perform(async () => { const saved = await api.get<Notes>(`/meetings/${meeting.id}/notes`); setNotes(n => ({ ...n, revisions: saved.revisions })); })}>Load history</Button>{notes.revisions?.map(r => <details key={r.version} className="mt-3"><summary className="min-h-11 cursor-pointer py-3">Version {r.version} · {r.updated_at}</summary><pre className="whitespace-pre-wrap break-words text-sm">{r.markdown}</pre></details>)}</details>
      {message && <p role="status" className="break-words text-sm">{message}</p>}
    </section>
    <section className="mt-6 rounded-xl border bg-card p-4 sm:p-6"><h2 className="font-semibold">Minutes</h2><pre className="mt-3 whitespace-pre-wrap break-words font-sans text-sm leading-relaxed">{minutes || 'Loading meeting minutes...'}</pre></section>
    <div className="mt-6 flex flex-wrap gap-2">{(['notes', 'minutes', 'detailed', 'all'] as const).map(kind => <Button key={kind} variant="outline" disabled={busy} onClick={() => void perform(async () => { const text = await api.get<string>(`/meetings/${meeting.id}/export/markdown`, { params: { kind } }); const url = URL.createObjectURL(new Blob([text], { type: 'text/markdown;charset=utf-8' })); const anchor = document.createElement('a'); anchor.href = url; anchor.download = `meeting-${meeting.id}-${kind}.md`; anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); setMessage('Downloaded saved content. Unsaved edits are excluded.'); })}>Download {kind} Markdown</Button>)}</div>
  </>;
}

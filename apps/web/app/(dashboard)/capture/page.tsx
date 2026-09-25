'use client';

import { useState } from 'react';
import { usePeople } from '@/hooks/usePeople';
import Link from 'next/link';
import { api } from '@/lib/api/browser-client';
import { VoiceInputButton } from '@/components/chat/voice-input-button';
import { PhotoTextInput } from '@/components/capture/photo-text-input';

type Proposal = {
  person_name: string | null; organization_name: string | null; project_name: string | null;
  venture_name: string | null; role: string | null; where_met: string | null;
  when_met: string | null; summary: string; commitment: string | null;
  due_at: string | null; direction: 'owed_by_me' | 'owed_to_me' | 'unspecified';
  topics: string[];
};
type Draft = { draft_id: string; proposal: Proposal; mode: string };

export default function CapturePage() {
  const [text, setText] = useState('');
  const { people } = usePeople();
  const [personId, setPersonId] = useState('');
  const [source, setSource] = useState<'manual' | 'voice' | 'image_text'>('manual');
  const [draft, setDraft] = useState<Draft | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [saved, setSaved] = useState(false);
  const [records, setRecords] = useState<{ type: string; id: string }[]>([]);
  const fields: [Exclude<keyof Proposal, 'topics'>, string][] = [
    ['person_name', 'Person'], ['organization_name', 'Organization'], ['role', 'Role'],
    ['where_met', 'Where you met'], ['project_name', 'Existing project'],
    ['venture_name', 'Existing venture'], ['commitment', 'Commitment'],
  ];
  async function run(action: () => Promise<void>) {
    setBusy(true); setMessage(''); setSaved(false);
    try { await action(); } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Could not save. Your text is still here.');
    } finally { setBusy(false); }
  }
  return <div className="mx-auto max-w-2xl space-y-6">
    <div><h1 className="text-3xl font-semibold">Capture context</h1>
      <p className="mt-2 text-muted-foreground">Save a conversation, meeting note, or something you promised. Review the connections before saving.</p></div>
    <label className="block space-y-2"><span>What happened?</span>
      <textarea aria-label="Capture text" rows={7} value={text} maxLength={16000}
        onChange={event => { setText(event.target.value); setDraft(null); setPersonId(''); }}
        className="w-full rounded-lg border bg-background p-3" placeholder="Met Ahmed at an event. We discussed fundraising and I promised to send a deck." /></label>
    <div className="flex flex-wrap items-center gap-3">
      <VoiceInputButton value={text} onChange={value => { setText(value); setDraft(null); setSource('voice'); }} disabled={busy} />
      <button disabled={busy || !text.trim()} onClick={() => run(async () => {
        setDraft(await api.post<Draft>('/capture/propose', { text, source }, { timeoutMs: 45000 }));
      })} className="min-h-11 rounded-lg bg-primary px-5 text-primary-foreground disabled:opacity-50">{busy ? 'Working…' : 'Review capture'}</button>
      <Link href="/documents" className="underline">Upload a document</Link>
    </div>
    <PhotoTextInput disabled={busy} onText={value => { setText(previous => [previous, value].filter(Boolean).join('\n\n')); setDraft(null); setSource('image_text'); }} />
    {draft && <section aria-label="Review capture" className="space-y-4 rounded-xl border p-4">
      <h2 className="text-xl font-semibold">Check before saving</h2>
      {draft.mode === 'manual_review' && <p className="text-sm">AI extraction is unavailable. Add the details below; your note can still be saved.</p>}
      <label className="block space-y-1"><span>Link to an existing person (optional)</span>
        <select aria-label="Existing person" value={personId} onChange={event => {
          setPersonId(event.target.value);
          const person = people.find(item => item.id === event.target.value);
          if (person) setDraft({ ...draft, proposal: { ...draft.proposal, person_name: person.name } });
        }} className="min-h-11 w-full rounded border bg-background px-3">
          <option value="">Match by reviewed name</option>
          {people.map(person => <option key={person.id} value={person.id}>{person.name}{person.company ? ` · ${person.company}` : ''} · {person.id.slice(0, 8)}</option>)}
        </select><p className="text-sm text-muted-foreground">Choose a record if multiple contacts share this name.</p>
      </label>
      <p className="text-sm text-muted-foreground">Existing identity facts are kept. Review company changes on the person’s profile. Dates such as “Friday” need your confirmation below.</p>
      <div className="grid gap-4 sm:grid-cols-2">{fields.map(([key, label]) => <label key={key} className="space-y-1 text-sm">
        <span>{label}</span><input className="min-h-11 w-full rounded border bg-background px-3" value={draft.proposal[key] || ''}
          onChange={event => setDraft({ ...draft, proposal: { ...draft.proposal, [key]: event.target.value || null } })} />
      </label>)}</div>
      <label className="block space-y-1"><span>Topics discussed (comma separated)</span><input className="min-h-11 w-full rounded border bg-background px-3"
        value={(draft.proposal.topics || []).join(', ')} onChange={event => setDraft({ ...draft, proposal: { ...draft.proposal, topics: event.target.value.split(',').slice(0, 12) } })} /></label>
      <label className="block space-y-1"><span>When you met (your device timezone)</span><input type="datetime-local" className="min-h-11 rounded border bg-background px-3"
        value={localDateTime(draft.proposal.when_met)} onChange={event => setDraft({ ...draft, proposal: { ...draft.proposal, when_met: event.target.value ? new Date(event.target.value).toISOString() : null } })} /></label>
      <label className="block space-y-1"><span>Summary</span><textarea rows={3} className="w-full rounded border bg-background p-3"
        value={draft.proposal.summary} onChange={event => setDraft({ ...draft, proposal: { ...draft.proposal, summary: event.target.value } })} /></label>
      <label className="block space-y-1"><span>Who made the commitment?</span><select className="min-h-11 w-full rounded border bg-background px-3"
        value={draft.proposal.direction} onChange={event => setDraft({ ...draft, proposal: { ...draft.proposal, direction: event.target.value as Proposal['direction'] } })}>
        <option value="unspecified">Not specified</option><option value="owed_by_me">I did — also create a task</option><option value="owed_to_me">They did</option>
      </select></label>
      <label className="block space-y-1"><span>Due date and time (your device timezone)</span><input type="datetime-local" className="min-h-11 rounded border bg-background px-3"
        value={localDateTime(draft.proposal.due_at)}
        onChange={event => setDraft({ ...draft, proposal: { ...draft.proposal, due_at: event.target.value ? new Date(event.target.value).toISOString() : null } })} /></label>
      <button disabled={busy || !draft.proposal.summary.trim()} className="min-h-11 rounded-lg bg-primary px-5 text-primary-foreground disabled:opacity-50"
        onClick={() => run(async () => {
          const result = await api.post<{records: {type: string; id: string}[]}>(`/capture/${draft.draft_id}/confirm`, { confirmed: true, proposal: draft.proposal, person_id: personId || null });
          setRecords(result.records);
          setText(''); setDraft(null); setPersonId(''); setSource('manual'); setSaved(true); setMessage('Saved. Your context and confirmed connections are ready. Search indexing runs separately.');
        })}>Confirm and save</button>
    </section>}
    {message && <p role={saved ? 'status' : 'alert'} className="rounded border p-3">{message}</p>}
    {saved && <nav aria-label="Saved context" className="flex flex-wrap gap-4">{records.map(record => <Link key={record.id} className="underline" href={record.type === 'person' ? `/people/${record.id}` : `/sources/${record.type}/${record.id}`}>Open {record.type}</Link>)}</nav>}
  </div>;
}

function localDateTime(value: string | null) {
  if (!value) return '';
  const date = new Date(value);
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
}

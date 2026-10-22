'use client';

import { useEffect, useRef, useState } from 'react';
import { usePeople } from '@/hooks/usePeople';
import Link from 'next/link';
import { api } from '@/lib/api/browser-client';
import { VoiceInputButton } from '@/components/chat/voice-input-button';
import { PhotoTextInput } from '@/components/capture/photo-text-input';
import type { CapturePhoto } from '@/lib/capture-photo';
import { createClient } from '@/lib/supabase/client';

type Proposal = {
  person_name: string | null; organization_name: string | null; project_name: string | null;
  venture_name: string | null; role: string | null; where_met: string | null;
  when_met: string | null; summary: string; commitment: string | null;
  due_at: string | null; direction: 'owed_by_me' | 'owed_to_me' | 'unspecified';
  topics: string[];
  email?: string | null; phone?: string | null; linkedin_url?: string | null;
};
type Draft = { draft_id: string; proposal: Proposal; mode: string };

export default function CapturePage() {
  const [text, setText] = useState('');
  const [personId, setPersonId] = useState('');
  const [source, setSource] = useState<'manual' | 'voice' | 'image_text'>('manual');
  const [draft, setDraft] = useState<Draft | null>(null);
  const { people } = usePeople({ enabled: Boolean(draft) });
  const [draftKey, setDraftKey] = useState<string | null>(null);
  const [draftNotice, setDraftNotice] = useState('');
  useEffect(() => {
    let active = true;
    void createClient().auth.getSession().then(({data:{session}}) => {
      if (!active) return;
      if (!session?.user.id) { setDraftNotice('Draft recovery is unavailable. Keep this tab open until you save.'); return; }
      const key = `second-brain:capture:${session.user.id}`;
      try { const savedText = sessionStorage.getItem(key); if (savedText) setText(previous => previous || savedText.slice(0,16000)); setDraftKey(key); }
      catch { setDraftNotice('Draft recovery is unavailable in this browser. Keep this tab open until you save.'); }
    }).catch(() => { if (active) setDraftNotice('Draft recovery is unavailable. Keep this tab open until you save.'); });
    return () => { active = false; };
  }, []);
  useEffect(() => {
    if (!draftKey) return;
    try { if (text) sessionStorage.setItem(draftKey,text); else sessionStorage.removeItem(draftKey); }
    catch { setDraftNotice('Draft recovery is unavailable. Keep this tab open until you save.'); }
  }, [draftKey,text]);
  function updateText(value: string) {
    // Save in the input event: a fast reload must not outrun a React effect.
    if (draftKey) {
      try { if (value) sessionStorage.setItem(draftKey,value); else sessionStorage.removeItem(draftKey); }
      catch { setDraftNotice('Draft recovery is unavailable. Keep this tab open until you save.'); }
    }
    setText(value);
  }
  const [busy, setBusy] = useState(false);
  const [photoBusy, setPhotoBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [saved, setSaved] = useState(false);
  const [records, setRecords] = useState<{ type: string; id: string }[]>([]);
  const [photos, setPhotos] = useState<CapturePhoto[]>([]);
  const uploads = useRef(new Map<string, string>());
  const photoRef = useRef(photos); photoRef.current = photos;
  useEffect(() => () => photoRef.current.forEach(photo => URL.revokeObjectURL(photo.preview)), []);
  const [occurredAt, setOccurredAt] = useState('');
  const [createNew, setCreateNew] = useState(false);
  const zone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
  const fields: [Exclude<keyof Proposal, 'topics'>, string][] = [
    ['person_name', 'Person'], ['organization_name', 'Organization'], ['role', 'Role'],
    ['where_met', 'Where you met'], ['project_name', 'Existing project'],
    ['venture_name', 'Existing venture'], ['commitment', 'Commitment'],
    ['email', 'Email on card'], ['phone', 'Phone with country code (+…)'], ['linkedin_url', 'Professional profile URL'],
  ];
  async function run(action: () => Promise<void>) {
    setBusy(true); setMessage(''); setSaved(false);
    try { await action(); } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Could not save. Your text is still here.');
    } finally { setBusy(false); }
  }
  return <div className="mx-auto max-w-2xl space-y-6">
    <div><h1 className="text-2xl sm:text-3xl font-semibold">Capture</h1>
      <p className="mt-2 text-base text-muted-foreground">What do you want to remember? Review the details before saving.</p></div>
    {!draftKey && !draftNotice && <p role="status" className="text-sm text-muted-foreground">Preparing private draft recovery…</p>}
    <label className="block space-y-2"><span>What happened?</span>
      <textarea aria-label="Capture text" rows={5} value={text} maxLength={16000} disabled={!draftKey && !draftNotice}
        onChange={event => { updateText(event.target.value); setDraft(null); setPersonId(''); }}
        className="w-full rounded-lg border bg-background p-3" placeholder="Met Ahmed at an event. We discussed fundraising and I promised to send a deck." /></label>
    <div className="flex flex-wrap items-center gap-3">
      <VoiceInputButton value={text} onChange={value => { updateText(value); setDraft(null); setSource('voice'); }} disabled={busy || (!draftKey && !draftNotice)} />
      <button disabled={busy || photoBusy || !text.trim()} onClick={() => run(async () => {
        const proposed = await api.post<Draft>('/capture/propose', { text, source, timezone: zone }, { timeoutMs: 45000 });
        setDraft(proposed);
        setOccurredAt(localDateTime(proposed.proposal.when_met || new Date().toISOString()));
      })} className="min-h-11 rounded-lg bg-primary px-5 text-primary-foreground disabled:opacity-50">{busy ? 'Working…' : 'Review capture'}</button>
      <Link href="/documents" className="inline-flex min-h-11 items-center underline">Upload a document</Link>
    </div>
    <details className="rounded-xl border px-3"><summary className="flex min-h-11 cursor-pointer items-center">Add a photo or business card</summary><div className="pb-3"><PhotoTextInput onBusy={setPhotoBusy} disabled={busy || photos.length >= 2} onPhoto={photo => { setPhotos(previous => [...previous, photo]); setSource('image_text'); }} onText={value => { setText(previous => [previous, value].filter(Boolean).join('\n\n').slice(0, 16000)); setDraft(null); setSource('image_text'); }} /></div></details>
    {draftNotice&&<p role="status" className="text-sm text-muted-foreground">{draftNotice}</p>}
    {!!photos.length && <div className="flex flex-wrap gap-4">{photos.map(photo => <figure className="max-w-full space-y-2" key={photo.requestId}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={photo.preview} alt={photo.kind === 'business_card' ? 'Business card preview' : 'Moment preview'} className="max-h-40 max-w-full rounded-lg" />
      <figcaption className="text-sm">{photo.kind === 'business_card' ? 'Business card' : 'Moment'} · {Math.ceil(photo.blob.size / 1024)} KB</figcaption>
      <button disabled={busy} className="min-h-11 underline" onClick={async () => {
        setBusy(true); setMessage('');
        try {
          for (const [key, id] of Array.from(uploads.current.entries())) {
            if (key.endsWith(':' + photo.requestId)) { await api.delete(`/capture/media/${id}`); uploads.current.delete(key); }
          }
          URL.revokeObjectURL(photo.preview); setPhotos(previous => previous.filter(item => item !== photo));
        } catch { setMessage('Could not remove the uploaded photo. Retry before saving.'); }
        finally { setBusy(false); }
      }}>Remove photo</button>
    </figure>)}</div>}
    {draft && <section aria-label="Review capture" className="space-y-4 rounded-xl border p-4">
      <h2 className="text-xl font-semibold">Check before saving</h2>
      {draft.mode === 'manual_review' && <p className="text-sm">AI extraction is unavailable. Add the details below; your note can still be saved.</p>}
      <label className="block space-y-1"><span>Link to an existing person (optional)</span>
        <select aria-label="Existing person" value={createNew ? 'new' : personId} onChange={event => {
          setCreateNew(event.target.value === 'new'); setPersonId(event.target.value === 'new' ? '' : event.target.value);
          const person = people.find(item => item.id === event.target.value);
          if (person) setDraft({ ...draft, proposal: { ...draft.proposal, person_name: person.name } });
        }} className="min-h-11 w-full rounded border bg-background px-3">
          <option value="">Match by reviewed name</option>
          <option value="new">Create a separate new person</option>
          {people.map(person => <option key={person.id} value={person.id}>{person.name}{person.company ? ` · ${person.company}` : ''} · {person.id.slice(0, 8)}</option>)}
        </select><p className="text-sm text-muted-foreground">Choose a record if multiple contacts share this name.</p>
      </label>
      <label className="block space-y-1"><span>When this happened ({zone})</span><input aria-label="Event time" type="datetime-local" value={occurredAt} onChange={event => setOccurredAt(event.target.value)} className="min-h-11 max-w-full rounded border bg-background p-2" /></label>
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
      <button disabled={busy || photoBusy || !draft.proposal.summary.trim()} className="min-h-11 rounded-lg bg-primary px-5 text-primary-foreground disabled:opacity-50"
        onClick={() => run(async () => {
          const mediaIds: string[] = [];
          for (const photo of photos) {
            const form = new FormData(); form.set('file', photo.blob, photo.blob.type === 'image/webp' ? 'photo.webp' : 'photo.jpg');
            form.set('kind', photo.kind); form.set('request_id', photo.requestId);
            const media = await api.post<{id: string}>(`/capture/${draft.draft_id}/media`, form, {timeoutMs: 45000});
            uploads.current.set(draft.draft_id + ':' + photo.requestId, media.id);
            mediaIds.push(media.id);
          }
          const result = await api.post<{records: {type: string; id: string}[]}>(`/capture/${draft.draft_id}/confirm`, { confirmed: true, proposal: draft.proposal, person_id: personId || null,
            create_new_person: createNew, timezone: zone, occurred_at: occurredAt ? new Date(occurredAt).toISOString() : null, media_ids: mediaIds,
            event_type: photos.some(p => p.kind === 'business_card') ? 'business_card_scan' : photos.length ? 'moment' : 'manual_capture' });
          setRecords(result.records);
          photos.forEach(photo => URL.revokeObjectURL(photo.preview)); uploads.current.clear(); setPhotos([]); setCreateNew(false);
          updateText(''); setDraft(null); setPersonId(''); setSource('manual'); setSaved(true); setMessage('Saved. Your context and confirmed connections are ready. Search indexing runs separately.');
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

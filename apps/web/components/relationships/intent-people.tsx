'use client';
import { useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api/browser-client';
import { displayDate, type Evidence } from '@/lib/relationships';
import { OutreachControls } from './outreach-controls';

type Match = {person_id: string; name: string; company: string | null; recorded_role: string | null;
  last_interaction: string | null; relationship_context: string | null; confidence: string;
  evidence: (Evidence & {excerpt: string})[]; suggested_action: string};

export function IntentPeople() {
  const [query, setQuery] = useState('');
  const [matches, setMatches] = useState<Match[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState('');
  const [draft, setDraft] = useState('');
  return <section className="space-y-4 rounded-xl border p-4 sm:p-6">
    <h2 className="text-xl font-semibold">Who in your network may help?</h2>
    <form className="flex flex-wrap gap-3" onSubmit={async event => {
      event.preventDefault(); setBusy(true); setError(''); setSelected('');
      try { setMatches(await api.post<Match[]>('/relationships/intent', {query}, {timeoutMs: 45000})); }
      catch (error) { setError(error instanceof Error ? error.message : 'Could not search saved context.'); }
      finally { setBusy(false); }
    }}><label className="min-w-0 flex-1"><span className="sr-only">What are you working on?</span><input className="min-h-11 w-full rounded-lg border bg-background px-3" value={query} maxLength={500} onChange={event => setQuery(event.target.value)} placeholder="Fundraising, UAE accounting, finding testers…" /></label><button disabled={busy || query.trim().length < 3} className="min-h-11 rounded-lg border px-4 disabled:opacity-50">{busy ? 'Finding evidence…' : 'Find people'}</button></form>
    {matches?.length === 0 && <p>No supporting records found. Capture relevant conversations before asking again.</p>}
    {matches?.map(person => <article key={person.person_id} className="space-y-3 rounded-lg border p-4">
      <Link className="font-semibold underline" href={`/people/${person.person_id}`} onClick={() => { void api.post(`/relationships/people/${person.person_id}/observations`, {event: 'intent_result_opened'}).catch(() => undefined); }}>{person.name}</Link>
      <p className="text-sm">{[person.recorded_role, person.company, person.relationship_context].filter(Boolean).join(' · ')}</p>
      <p className="text-sm text-muted-foreground">Last recorded contact: {displayDate(person.last_interaction)}</p>
      {person.evidence.map(item => <p key={item.id} className="break-words text-sm">{item.excerpt.slice(0, 450)} <Link className="underline" href={item.uri}>Evidence</Link></p>)}
      <p className="text-sm text-muted-foreground">{person.confidence}</p><p className="text-sm">{person.suggested_action}</p>
      <button className="min-h-11 rounded-lg border px-3" disabled={busy} onClick={async () => {
        setBusy(true); setError('');
        try { const result = await api.post<{draft: string}>(`/relationships/people/${person.person_id}/outreach/draft`); setSelected(person.person_id); setDraft(result.draft); }
        catch (error) { setError(error instanceof Error ? error.message : 'Could not prepare draft.'); }
        finally { setBusy(false); }
      }}>Draft message</button>
      {selected === person.person_id && <div className="space-y-3"><label className="block">Review your message<textarea aria-label="Intent outreach draft" className="mt-2 w-full rounded border bg-background p-3" value={draft} maxLength={4000} rows={4} onChange={event => setDraft(event.target.value)} /></label><OutreachControls personId={person.person_id} draft={draft} onChanged={() => setSelected('')} /></div>}
    </article>)}
    {error && <p role="alert">{error}</p>}
  </section>;
}

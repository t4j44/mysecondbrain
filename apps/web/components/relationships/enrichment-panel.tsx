'use client';

import { useCallback, useEffect, useState } from 'react';
import { api } from '@/lib/api/browser-client';
import { displayDate } from '@/lib/relationships';

type Claim = {id: string; field: string; value: string; source_url: string; source_type: string; source_quote: string; researched_at: string; confidence_reason: string; verification_state: string; current_value: string | null; conflict: boolean; identity_basis: string};
type Research = {source_id: string; source_url: string; text: string; name_mentioned: boolean; candidates: {field: string; value: string}[]; notice: string};

export function EnrichmentPanel({personId, onChanged}: {personId: string; onChanged: () => void}) {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [research, setResearch] = useState<Research | null>(null);
  const [url, setUrl] = useState('');
  const [field, setField] = useState('company');
  const [value, setValue] = useState('');
  const [quote, setQuote] = useState('');
  const [identity, setIdentity] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [removeId, setRemoveId] = useState<string | null>(null);
  const path = `/relationships/people/${personId}`;
  const load = useCallback(async () => { setClaims(await api.get<Claim[]>(`${path}/claims`)); }, [path]);
  useEffect(() => { void load().catch(error => setError(error instanceof Error ? error.message : 'Could not load public sources.')); }, [load]);
  async function run(action: () => Promise<void>) {
    setBusy(true); setError('');
    try { await action(); } catch (error) { setError(error instanceof Error ? error.message : 'Could not save this review.'); }
    finally { setBusy(false); }
  }
  const input = 'mt-1 min-h-11 w-full rounded border bg-background p-2';
  const button = 'min-h-11 rounded border px-3 py-2 text-sm disabled:opacity-50';
  return <section className="space-y-4 rounded-xl border border-[#301642] bg-[#0a0510] p-4 sm:p-6">
    <h2 className="text-xl font-semibold">Public professional context</h2>
    <p className="text-sm text-slate-400">Optional research from a public company page, personal site, or article. Your own knowledge takes precedence. Nothing updates your profile until you approve it.</p>
    <details><summary className="min-h-11 cursor-pointer py-2">Review a public source</summary>
      <div className="space-y-4 pt-2"><label className="block text-sm">Public page URL<input type="url" className={input} value={url} onChange={event => { setUrl(event.target.value); setResearch(null); setConfirmed(false); }} placeholder="https://company.example/team/person" /></label>
        <p className="text-xs text-slate-400">Use a direct public HTTPS address without sign-in tokens or query parameters. Login walls, access checks, redirects, and restricted crawling are not bypassed.</p>
        <button className={button} disabled={busy || !url.trim()} onClick={() => run(async () => { setResearch(await api.post<Research>(`${path}/research`, {source_url: url}, {timeoutMs: 35000})); setQuote(''); setIdentity(''); setConfirmed(false); })}>{busy ? 'Working…' : 'Read public page'}</button>
        {research && <div className="space-y-4 rounded border p-3"><a className="break-all text-sm underline" href={research.source_url} target="_blank" rel="noopener noreferrer">Open original source</a><p className="text-sm">{research.notice}</p>{!research.name_mentioned && <p className="text-sm text-amber-400">This page does not mention the saved name. Check carefully that it refers to this person.</p>}
          <details><summary className="cursor-pointer py-2">Read extracted public text</summary><p className="max-h-72 overflow-auto whitespace-pre-wrap break-words text-sm text-slate-300">{research.text || 'No readable public text found.'}</p></details>
          {!!research.candidates.length && <div className="space-y-2"><p className="text-sm">Possible professional facts from page metadata:</p>{research.candidates.map((candidate, i) => <button key={i} className={button + ' mr-2'} onClick={() => { setField(candidate.field); setValue(candidate.value); }}>{candidate.field}: {candidate.value}</button>)}</div>}
          <label className="block text-sm">Professional field<select className={input} value={field} onChange={event => setField(event.target.value)}>{['company', 'role', 'industry', 'location', 'professional_context'].map(item => <option value={item} key={item}>{item.replace('_', ' ')}</option>)}</select></label>
          <label className="block text-sm">Claim value<input maxLength={255} className={input} value={value} onChange={event => setValue(event.target.value)} /></label>
          <label className="block text-sm">Exact source quote supporting this value<textarea maxLength={1000} rows={3} className={input} value={quote} onChange={event => setQuote(event.target.value)} /></label>
          <label className="block text-sm">How did you confirm it is the same person?<input maxLength={500} className={input} value={identity} onChange={event => setIdentity(event.target.value)} placeholder="Matching role and company, or another professional identifier" /></label>
          <label className="flex min-h-11 items-center gap-3 text-sm"><input type="checkbox" checked={confirmed} onChange={event => setConfirmed(event.target.checked)} />I checked identity beyond the name and reviewed the source.</label>
          <button className={button} disabled={busy || !confirmed || !value.trim() || quote.trim().length < 10 || identity.trim().length < 10} onClick={() => run(async () => {
            await api.post(`${path}/claims`, {source_id: research.source_id, confirmed_identity: true, identity_basis: identity, field, value, source_quote: quote}); await load(); setValue(''); setQuote(''); setConfirmed(false);
          })}>Propose for review</button>
        </div>}
      </div>
    </details>
    {!claims.length && <p className="text-sm text-slate-400">No public claims saved. Private relationship notes are sufficient to use Second Brain.</p>}
    {claims.map(claim => <article className="space-y-3 rounded border p-4" key={claim.id}>
      <div className="flex flex-wrap justify-between gap-2"><h3 className="font-medium">{claim.field.replace('_', ' ')}: {claim.value}</h3><span className="text-xs text-slate-400">{claim.verification_state}</span></div>
      {claim.conflict && <p className="rounded border border-amber-600 p-3 text-sm">Your profile says: <strong>{claim.current_value}</strong>. This public source says: <strong>{claim.value}</strong>. Keep your current fact or explicitly update it below.</p>}
      <blockquote className="border-l-2 pl-3 text-sm">{claim.source_quote}</blockquote><a className="break-all text-sm underline" href={claim.source_url} target="_blank" rel="noopener noreferrer">Review source</a>
      <p className="text-xs text-slate-400">Observed {displayDate(claim.researched_at)} · {claim.source_type.replace('_', ' ')}. {claim.confidence_reason}</p><p className="text-xs text-slate-400">Identity checked using: {claim.identity_basis}</p>
      <div className="flex flex-wrap gap-2">
        {claim.verification_state === 'proposed' && <button className={button} disabled={busy} onClick={() => run(async () => { await api.post(`${path}/claims/${claim.id}/review`, {confirmed: true, decision: 'verify'}); await load(); })}>Verify source; keep my profile</button>}
        {claim.field !== 'professional_context' && claim.value !== claim.current_value && claim.verification_state !== 'rejected' && <button className={button} disabled={busy} onClick={() => run(async () => { await api.post(`${path}/claims/${claim.id}/review`, {confirmed: true, decision: 'apply', expected_current: claim.current_value}); await load(); onChanged(); })}>Approve profile update</button>}
        {claim.verification_state !== 'rejected' && <button className={button} disabled={busy} onClick={() => run(async () => { await api.post(`${path}/claims/${claim.id}/review`, {confirmed: true, decision: 'reject'}); await load(); })}>Reject claim</button>}
        <button className={button} disabled={busy} onClick={() => setRemoveId(claim.id)}>Remove source</button>
      </div>
      {removeId === claim.id && <div className="space-y-2 border-t pt-3"><p className="text-sm">Remove this claim and its searchable evidence? Values you approved into your profile remain editable through Edit contact. To correct a claim, remove it and propose the corrected quote.</p><button className={button} disabled={busy} onClick={() => run(async () => { await api.delete(`${path}/claims/${claim.id}`); setRemoveId(null); await load(); })}>Confirm removal</button><button className={button + ' ml-2'} onClick={() => setRemoveId(null)}>Cancel</button></div>}
    </article>)}
    {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
  </section>;
}

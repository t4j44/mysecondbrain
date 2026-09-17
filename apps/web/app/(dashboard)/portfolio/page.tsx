'use client';
import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api/browser-client';
type Source = { id: string; entity_type: string; title: string };
type Draft = { id: string; title: string; body: string; sources: { id: string; kind: string; excerpt: string }[] };
type Publication = { id: string; title: string; revoked: boolean };
export default function PortfolioPage() {
  const [query, setQuery] = useState(''); const [results, setResults] = useState<Source[]>([]);
  const [selected, setSelected] = useState<Source[]>([]); const [title, setTitle] = useState('My work case study');
  const [drafts, setDrafts] = useState<Draft[]>([]); const [draft, setDraft] = useState<Draft | null>(null);
  const [publications, setPublications] = useState<Publication[]>([]);
  const [busy, setBusy] = useState(false); const [message, setMessage] = useState('');
  const [approved, setApproved] = useState(false); const [share, setShare] = useState('');
  const load = useCallback(async () => {
    const [a, b] = await Promise.all([api.get<{ items: Draft[] }>('/portfolio/drafts'), api.get<{ items: Publication[] }>('/portfolio/publications')]);
    setDrafts(a.items); setPublications(b.items);
  }, []);
  useEffect(() => { load().catch(error => setMessage(error.message)); }, [load]);
  async function run(action: () => Promise<void>) {
    setBusy(true); setMessage(''); try { await action(); }
    catch (error) { setMessage(error instanceof Error ? error.message : 'Request failed.'); } finally { setBusy(false); }
  }
  return <div className="mx-auto max-w-3xl space-y-6">
    <h1 className="text-3xl font-semibold">Evidence portfolio</h1>
    <p>Choose real records, review a case study, then publish only the text you approve. Saved claims are self-reported unless you have independent supporting evidence.</p>
    <section className="space-y-3 rounded-xl border p-4"><h2 className="text-xl font-semibold">Choose evidence</h2>
      <form className="flex gap-2" onSubmit={event => { event.preventDefault(); run(async () => {
        const data = await api.post<{ results: Source[] }>('/ai/search', { query }); setResults(data.results);
      }); }}><input aria-label="Find portfolio evidence" value={query} onChange={event => setQuery(event.target.value)} className="min-h-11 min-w-0 flex-1 rounded border bg-background px-3" placeholder="Find a project or work note" />
        <button disabled={busy || !query.trim()} className="min-h-11 rounded border px-4">Search</button></form>
      {results.map(source => <label key={`${source.entity_type}-${source.id}`} className="flex min-h-11 items-center gap-3">
        <input type="checkbox" checked={selected.some(item => item.id === source.id && item.entity_type === source.entity_type)} onChange={event => {
          setSelected(event.target.checked ? [...selected, source] : selected.filter(item => item.id !== source.id || item.entity_type !== source.entity_type));
        }} /><span>{source.title} · {source.entity_type}</span></label>)}
      <p>{selected.length} selected (maximum 10)</p>
      <label className="block">Title<input value={title} onChange={event => setTitle(event.target.value)} maxLength={255} className="mt-1 min-h-11 w-full rounded border bg-background px-3" /></label>
      <button disabled={busy || !selected.length || selected.length > 10 || !title.trim()} className="min-h-11 rounded bg-primary px-4 text-primary-foreground" onClick={() => run(async () => {
        const data = await api.post<Draft>('/portfolio/drafts', { title, sources: selected.map(item => ({ kind: item.entity_type, id: item.id })) }, { timeoutMs: 60000 });
        setDraft(data); setApproved(false); await load();
      })}>Create private draft</button>
    </section>
    {drafts.length > 0 && <section className="space-y-2"><h2 className="text-xl font-semibold">Saved drafts</h2>{drafts.map(item => <button key={item.id} className="mr-2 min-h-11 rounded border px-3" onClick={() => { setDraft(item); setApproved(false); setShare(''); }}>{item.title}</button>)}</section>}
    {draft && <section className="space-y-4 rounded-xl border p-4"><h2 className="text-xl font-semibold">Review the exact public text</h2>
      <input aria-label="Public title" value={draft.title} onChange={event => { setDraft({ ...draft, title: event.target.value }); setApproved(false); }} className="min-h-11 w-full rounded border bg-background px-3" />
      <textarea aria-label="Public case study text" rows={14} maxLength={20000} value={draft.body} onChange={event => { setDraft({ ...draft, body: event.target.value }); setApproved(false); }} className="w-full rounded border bg-background p-3" />
      <details><summary className="cursor-pointer py-3">Private supporting records (not published automatically)</summary>
        {draft.sources.map((item, index) => <div key={`${item.kind}-${item.id}`} className="mb-3"><Link className="underline" href={`/sources/${item.kind}/${item.id}`}>[{index + 1}] Open private source</Link><p className="whitespace-pre-wrap text-sm">{item.excerpt}</p></div>)}
      </details>
      <button disabled={busy || !draft.title.trim() || !draft.body.trim()} className="min-h-11 rounded border px-4" onClick={() => run(async () => {
        await api.patch(`/portfolio/drafts/${draft.id}`, { title: draft.title, body: draft.body });
        await load(); setMessage('Private draft saved. Published copies keep their approved text.');
      })}>Save private draft</button>
      <label className="flex items-start gap-3"><input type="checkbox" checked={approved} onChange={event => setApproved(event.target.checked)} className="mt-1" /><span>I reviewed this exact text, removed private details, and approve sharing it with anyone who has the link.</span></label>
      <button disabled={busy || !approved} className="min-h-11 rounded bg-primary px-4 text-primary-foreground" onClick={() => run(async () => {
        const result = await api.post<{ share_path: string }>(`/portfolio/drafts/${draft.id}/publish`, { title: draft.title, body: draft.body, confirmed_public: true });
        setShare(window.location.origin + result.share_path); setApproved(false); await load();
      })}>Publish reviewed copy</button>
      {share && <p className="break-all">Save your share link: <a className="underline" href={share} target="_blank" rel="noreferrer">{share}</a></p>}
    </section>}
    {publications.length > 0 && <section className="space-y-3"><h2 className="text-xl font-semibold">Published copies</h2>{publications.map(item => <div key={item.id} className="flex flex-wrap items-center justify-between gap-2 rounded border p-3"><span>{item.title} · {item.revoked ? 'Revoked' : 'Public via link'}</span>{!item.revoked && <button disabled={busy} className="min-h-11 rounded border px-3" onClick={() => run(async () => { await api.delete(`/portfolio/publications/${item.id}`); await load(); setShare(''); })}>Revoke link</button>}</div>)}</section>}
    {message && <p role="status" className="rounded border p-3">{message}</p>}
  </div>;
}

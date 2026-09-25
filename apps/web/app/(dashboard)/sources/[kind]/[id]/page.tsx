'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api/browser-client';

export default function SourcePage() {
  const { kind, id } = useParams<{ kind: string; id: string }>();
  const [source, setSource] = useState<{ title: string; text: string; updated_at: string } | null>(null);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [people, setPeople] = useState<{id: string; title: string; uri: string; reason: string}[]>([]);
  const [connectionError, setConnectionError] = useState('');
  useEffect(() => {
    let active = true;
    api.get<{ title: string; text: string; updated_at: string }>(`/sources/${encodeURIComponent(kind)}/${encodeURIComponent(id)}`)
      .then(data => { if (active) setSource(data); }).catch(error => { if (active) setMessage(error.message); });
    return () => { active = false; };
  }, [kind, id]);
  useEffect(() => {
    setPeople([]); setConnectionError('');
    if (!['project', 'venture', 'meeting', 'document', 'organization', 'person', 'task', 'commitment'].includes(kind)) return;
    let active = true;
    api.get<{id: string; title: string; uri: string; reason: string}[]>(`/relationships/records/${encodeURIComponent(kind)}/${encodeURIComponent(id)}/people`)
      .then(rows => { if (active) setPeople(rows); }).catch(() => { if (active) setConnectionError('Related people could not be loaded.'); });
    return () => { active = false; };
  }, [kind, id]);
  return <article className="mx-auto max-w-3xl space-y-5">
    <Link href="/assistant" className="underline">Back to Ask</Link>
    <h1 className="text-2xl font-semibold">{source?.title || 'Source record'}</h1>
    {source ? <><p className="text-sm text-muted-foreground">Private record · Updated {new Date(source.updated_at).toLocaleString()}</p>
      <div className="whitespace-pre-wrap break-words rounded-xl border p-5">{source.text}</div>
      <button className="min-h-11 rounded border px-4" disabled={busy} onClick={async () => {
        setBusy(true); try {
          await api.post(`/sources/${encodeURIComponent(kind)}/${encodeURIComponent(id)}/index`);
          setMessage('Indexing queued. This does not change the original record.');
        } catch (error) { setMessage(error instanceof Error ? error.message : 'Could not queue indexing.'); }
        finally { setBusy(false); }
      }}>Retry search indexing</button></> : !message && <p role="status">Loading source…</p>}
    {message && <p role="status">{message}</p>}
    {!!people.length && <section className="space-y-3 rounded-xl border p-4"><h2 className="text-xl font-semibold">Connected people</h2>{people.map(person => <div key={person.id}><Link className="underline" href={person.uri}>{person.title}</Link><p className="mt-1 text-sm text-muted-foreground">{person.reason}</p></div>)}</section>}
    {connectionError && <p role="alert" className="text-sm">{connectionError}</p>}
  </article>;
}

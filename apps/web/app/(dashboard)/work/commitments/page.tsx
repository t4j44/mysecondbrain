'use client';

import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';
import { api } from '@/lib/api/browser-client';
import { PageHeader } from '@/components/shared/page-header';

type Commitment = { id: string; description: string; direction: string; due_at: string | null; from_person_id: string | null; to_person_id: string | null };
export default function CommitmentsPage() {
  const [rows, setRows] = useState<Commitment[]>([]); const [error, setError] = useState(''); const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    setLoading(true); setError('');
    try { setRows(await api.get<Commitment[]>('/commitments', { params: { commitment_status: 'open' } })); }
    catch (err) { setError(err instanceof Error ? err.message : 'Could not load commitments.'); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  return <div className="mx-auto max-w-3xl space-y-5"><Link href="/work" className="text-sm underline">Back to Work</Link>
    <PageHeader title="Open commitments" description="Promises from your saved conversations. Open a person to review context and record an outcome." />
    {loading && <p role="status">Loading commitments…</p>}
    {error && <div role="alert">{error}<button onClick={load} className="ml-3 min-h-11 underline">Retry</button></div>}
    {!loading && !error && rows.length === 0 && <p>No open commitments. <Link href="/capture" className="underline">Capture a conversation</Link> to record one.</p>}
    {rows.map(row => <article key={row.id} className="rounded-xl border p-5"><p className="text-sm text-muted-foreground">{row.direction === 'owed_by_me' ? 'I promised' : row.direction === 'owed_to_me' ? 'They promised' : 'Direction not recorded'}</p>
      <h2 className="mt-1 font-semibold">{row.description}</h2><p className="mt-2 text-sm">{row.due_at ? `Due ${new Date(row.due_at).toLocaleString()}` : 'No due date recorded'}</p>
      <div className="mt-3 flex flex-wrap gap-4"><Link className="min-h-11 py-2 text-primary underline" href={`/sources/commitment/${row.id}`}>View source</Link>
        {(row.to_person_id || row.from_person_id) && <Link className="min-h-11 py-2 text-primary underline" href={`/people/${row.to_person_id || row.from_person_id}`}>View person and follow up</Link>}</div>
    </article>)}
  </div>;
}

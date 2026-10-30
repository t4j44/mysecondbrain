'use client';

import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';
import { api } from '@/lib/api/browser-client';
import { PageHeader } from '@/components/shared/page-header';
import { Button } from '@/components/ui/button';
import { CommitmentCard, type Commitment } from '@/components/relationships/commitment-card';

export default function CommitmentsPage() {
  const [rows, setRows] = useState<Commitment[]>([]); const [error, setError] = useState(''); const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const load = useCallback(async () => {
    setLoading(true); setError('');
    try { setRows(await api.get<Commitment[]>('/commitments', { params: { commitment_status: 'active' } })); }
    catch { setError('Your promises could not be loaded. Try again.'); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  return <div className="mx-auto max-w-3xl space-y-5"><Link href="/work" className="text-sm underline">Back to Work</Link>
    <PageHeader title="Your promises" description="A clear next step for each commitment." />
    {message && <p role="status" className="rounded-lg border bg-card p-3 text-sm">{message}</p>}
    {loading && <p role="status">Loading commitments…</p>}
    {error && <div role="alert">{error}<Button variant="outline" onClick={() => void load()} className="ml-3">Retry</Button></div>}
    {!loading && !error && rows.length === 0 && <p>No open commitments. <Link href="/capture" className="underline">Capture a conversation</Link> to record one.</p>}
    {!loading && !error && rows.map(row => <CommitmentCard key={`${row.id}:${row.revision}`} row={row} onReload={load} onSaved={async notice => { setMessage(notice); await load(); }} />)}
  </div>;
}

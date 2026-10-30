'use client';
import { useState } from 'react';
import { api } from '@/lib/api/browser-client';
import type { Evidence } from '@/lib/relationships';

export function ConnectionEditor({personId, onChanged}: {personId: string; onChanged: () => void}) {
  const [kind, setKind] = useState('project'); const [query, setQuery] = useState('');
  const [options, setOptions] = useState<Evidence[]>([]); const [selected, setSelected] = useState('');
  const [reason, setReason] = useState(''); const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  const input = 'mt-1 min-h-11 w-full rounded border bg-background p-2';
  return <details className="mt-4 border-t pt-3"><summary className="min-h-11 cursor-pointer py-2 text-sm">Connect a saved work item or person</summary><div className="space-y-3 text-sm">
    <label className="block">Connect to<select className={input} value={kind} onChange={event => { setKind(event.target.value); setOptions([]); setSelected(''); }}>{['project', 'venture', 'meeting', 'document', 'organization', 'person', 'task', 'commitment'].map(value => <option key={value}>{value}</option>)}</select></label>
    <label className="block">Find a saved record<input className={input} value={query} maxLength={100} onChange={event => setQuery(event.target.value)} /></label>
    <button className="min-h-11 rounded border px-3" disabled={busy} onClick={async () => { setBusy(true); setError(''); try { const rows = await api.get<Evidence[]>('/relationships/link-options', {params: {kind, query}}); setOptions(rows.filter(item => item.id !== personId)); setSelected(''); if (!rows.length) setError('No saved records found. Add the record in Work first.'); } catch (error) { setError(error instanceof Error ? error.message : 'Could not search.'); } finally { setBusy(false); } }}>Find records</button>
    {!!options.length && <><label className="block">Choose record<select className={input} value={selected} onChange={event => setSelected(event.target.value)}><option value="">Select a record</option>{options.map(item => <option key={item.id} value={item.id}>{item.title}</option>)}</select></label><label className="block">What is the connection?<input className={input} value={reason} maxLength={500} onChange={event => setReason(event.target.value)} placeholder="Reviewed our Saudi market research with this person" /></label><p className="text-xs text-slate-400">This is a connection you are recording. It does not imply endorsement or availability.</p><button className="min-h-11 rounded border px-3" disabled={busy || !selected || reason.trim().length < 5} onClick={async () => {
      setBusy(true); setError(''); try { await api.post(`/relationships/people/${personId}/connections`, {confirmed: true, kind, record_id: selected, reason}); setSelected(''); setReason(''); onChanged(); } catch (error) { setError(error instanceof Error ? error.message : 'Could not save connection.'); } finally { setBusy(false); }
    }}>Confirm connection</button></>}
    {error && <p role="alert">{error}</p>}
  </div></details>;
}

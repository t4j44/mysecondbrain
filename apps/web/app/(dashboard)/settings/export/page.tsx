'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api/browser-client';
type Export = { id: string; status: string; created_at: string };
export default function SettingsExportPage() {
  const [items, setItems] = useState<Export[]>([]); const [busy, setBusy] = useState(false); const [message, setMessage] = useState('');
  async function load() { const result = await api.get<{ items: Export[] }>('/exports'); setItems(result.items); }
  useEffect(() => { load().catch(error => setMessage(error.message)); }, []);
  async function run(action: () => Promise<void>) { setBusy(true); setMessage(''); try { await action(); await load(); } catch (error) { setMessage(error instanceof Error ? error.message : 'Export failed.'); } finally { setBusy(false); } }
  return <div className="space-y-5"><h1 className="text-2xl font-semibold">Export your records</h1>
    <p>Create a Markdown copy of active people, organizations, projects, ventures, interactions, meetings, memories, tasks, commitments, and extracted document text. Original attachments and other tables are not included.</p>
    <div className="flex flex-wrap gap-3"><button disabled={busy} className="min-h-11 rounded bg-primary px-4 text-primary-foreground" onClick={() => run(async () => {
      await api.post('/exports', { export_type: 'full', include_attachments: false }, { timeoutMs: 60000 }); setMessage('Export queued. Refresh to check completion.');
    })}>Create Markdown export</button><button disabled={busy} className="min-h-11 rounded border px-4" onClick={() => run(async () => {})}>Refresh status</button></div>
    {items.map(item => <div key={item.id} className="flex flex-wrap items-center justify-between gap-3 rounded border p-4"><span>{new Date(item.created_at).toLocaleString()} · {item.status}</span>
      {item.status === 'completed' && <button disabled={busy} className="min-h-11 rounded border px-4" onClick={() => run(async () => {
        const content = await api.get<string>(`/exports/${item.id}/download`, { timeoutMs: 45000 });
        const url = URL.createObjectURL(new Blob([content], { type: 'text/markdown;charset=utf-8' }));
        const link = document.createElement('a'); link.href = url; link.download = 'second-brain-export.md'; link.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      })}>Download</button>}</div>)}
    {message && <p role="status">{message}</p>}
  </div>;
}

'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api/browser-client';
type Document = { id: string; filename: string; processing_status: string; error_state?: string };
export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const fileInput = useRef<HTMLInputElement>(null);
  const load = useCallback(async () => {
    const data = await api.get<{ items: Document[] }>('/documents'); setDocuments(data.items);
  }, []);
  useEffect(() => { load().catch(error => setMessage(error.message)); }, [load]);
  async function run(action: () => Promise<void>) {
    setBusy(true); setMessage('');
    try { await action(); await load(); }
    catch (error) { setMessage(error instanceof Error ? error.message : 'Request failed. Try again.'); }
    finally { setBusy(false); }
  }
  return <div className="mx-auto max-w-3xl space-y-6">
    <h1 className="text-3xl font-semibold">Documents</h1>
    <p>Upload PDF, DOCX, PPTX, XLSX, text, Markdown, CSV, JSON, or HTML (up to 50 MB). Text is extracted on the server; minimized text is sent for search indexing. For a photo or scanned PDF, add its readable text through <Link className="underline" href="/capture">Capture</Link>.</p>
    <form className="flex flex-wrap items-center gap-3 rounded-xl border p-4" onSubmit={event => {
      event.preventDefault(); const file = fileInput.current?.files?.[0]; if (!file) return;
      run(async () => { const body = new FormData(); body.append('file', file);
        await api.post('/documents', body, { timeoutMs: 60000 });
        if (fileInput.current) fileInput.current.value = '';
        setMessage('File saved. Search indexing may take a few minutes.');
      });
    }}>
      <label className="min-w-0 flex-1">Choose a file<input ref={fileInput} required type="file" accept=".pdf,.docx,.pptx,.xlsx,.txt,.md,.csv,.json,.html" className="mt-2 block max-w-full text-sm" /></label>
      <button disabled={busy} className="min-h-11 rounded bg-primary px-4 text-primary-foreground">Upload</button>
    </form>
    <button disabled={busy} className="min-h-11 rounded border px-4" onClick={() => run(async () => {})}>Refresh status</button>
    {message && <p role="status" className="rounded border p-3">{message}</p>}
    {!documents.length && <p>Your uploaded files will appear here.</p>}
    <ul className="space-y-3">{documents.map(doc => <li key={doc.id} className="space-y-3 rounded-xl border p-4">
      <Link href={`/sources/document/${doc.id}`} className="break-words font-semibold underline">{doc.filename}</Link>
      <p className="text-sm">Indexing: {doc.processing_status}{doc.error_state ? ` Â· ${doc.error_state}` : ''}</p>
      <div className="flex flex-wrap gap-3">
        <button disabled={busy} className="min-h-11 rounded border px-3" onClick={() => run(async () => {
          await api.post(`/sources/document/${doc.id}/index`); setMessage('Retry queued.');
        })}>Retry indexing</button>
        <button disabled={busy} className="min-h-11 rounded border px-3" onClick={() => run(async () => {
          await api.delete(`/documents/${doc.id}`); setMessage('Removed from your library and search.');
        })}>Remove from library</button>
      </div>
    </li>)}</ul>
  </div>;
}

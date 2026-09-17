'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api/browser-client';
import { env } from '@/lib/env';
type Credential = { credential_id: string; client_name: string; key_prefix: string; status: string; scopes: string[] };
export default function AIAccessPage() {
  const [items, setItems] = useState<Credential[]>([]); const [name, setName] = useState('');
  const [canWrite, setCanWrite] = useState(false); const [secret, setSecret] = useState('');
  const [busy, setBusy] = useState(false); const [message, setMessage] = useState('');
  const endpoint = env.NEXT_PUBLIC_API_BASE_URL.replace(/\/api\/v1\/?$/, '') + '/mcp';
  async function load() { setItems(await api.get<Credential[]>('/mcp/credentials')); }
  useEffect(() => { load().catch(error => setMessage(error.message)); }, []);
  async function run(action: () => Promise<void>) { setBusy(true); setMessage(''); try { await action(); await load(); }
    catch (error) { setMessage(error instanceof Error ? error.message : 'Request failed.'); } finally { setBusy(false); } }
  return <div className="max-w-2xl space-y-5"><h1 className="text-2xl font-semibold">AI assistant access</h1>
    <p>MCP lets compatible AI tools retrieve the same saved context. Create a separate key for each client. Retrieved information is then subject to that client&apos;s data policy.</p>
    <p className="break-all">Streamable HTTP endpoint: <code>{endpoint}</code></p>
    <p>Use a client that supports a custom bearer token. Configure its Authorization header with your key. Native hosted connectors may require OAuth and are not verified in this beta.</p>
    <form className="space-y-3 rounded-xl border p-4" onSubmit={event => { event.preventDefault(); run(async () => {
      const result = await api.post<Credential & { plaintext_key: string }>('/mcp/credentials', {
        client_name: name, client_type: 'streamable_http', scopes: canWrite ? ['mcp:read', 'mcp:write'] : ['mcp:read'],
      }); setSecret(result.plaintext_key); setName('');
    }); }}><label className="block">Client name<input required value={name} maxLength={100} onChange={event => setName(event.target.value)} className="mt-1 min-h-11 w-full rounded border bg-background px-3" placeholder="My Claude client" /></label>
      <label className="flex items-start gap-3"><input type="checkbox" checked={canWrite} onChange={event => setCanWrite(event.target.checked)} className="mt-1" /><span>Also allow this client to create and update records. Leave off for read-only access.</span></label>
      <button disabled={busy || !name.trim()} className="min-h-11 rounded bg-primary px-4 text-primary-foreground">Create client key</button>
    </form>
    {secret && <section className="space-y-3 rounded border p-4"><p>Copy this key into your client&apos;s secret configuration. It is shown once and is not saved in browser storage.</p>
      <input type="password" readOnly aria-label="New MCP key" value={secret} className="min-h-11 w-full rounded border bg-background px-3" />
      <div className="flex gap-3"><button className="min-h-11 rounded border px-4" onClick={() => navigator.clipboard.writeText(secret).then(() => setMessage('Key copied.')).catch(() => setMessage('Clipboard unavailable. Select and copy the key manually.'))}>Copy key</button><button className="min-h-11 rounded border px-4" onClick={() => setSecret('')}>Hide key</button></div></section>}
    {items.map(item => <div key={item.credential_id} className="space-y-2 rounded border p-4"><p>{item.client_name} · {item.key_prefix}… · {item.status}</p><p className="break-words text-sm">{item.scopes.join(', ')}</p>
      {item.status === 'active' && <button disabled={busy} className="min-h-11 rounded border px-4" onClick={() => run(async () => { await api.post(`/mcp/credentials/${item.credential_id}/revoke`); setSecret(''); })}>Revoke access</button>}</div>)}
    {message && <p role="status">{message}</p>}
  </div>;
}

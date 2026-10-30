'use client';
import { useCallback, useEffect, useState } from 'react';
import { api } from '@/lib/api/browser-client';
import { displayDate } from '@/lib/relationships';

type Connection = {id: string; client_name: string; scopes: string[]; last_used_at: string | null; expires_at: string; revoked_at: string | null};

export function OAuthConnections() {
  const [items, setItems] = useState<Connection[]>([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState('');
  const load = useCallback(async () => setItems(await api.get<Connection[]>('/mcp/oauth/connections')), []);
  useEffect(() => { void load().catch(error => setError(error.message)); }, [load]);
  return <section className="space-y-3 rounded-xl border p-4"><h2 className="text-xl font-semibold">OAuth connections</h2>
    <p className="text-sm">Connect from your AI client using the MCP endpoint, sign in, then approve selected permissions. Hosted ChatGPT and Claude acceptance remains unverified until staging checks pass.</p>
    {!items.length && <p className="text-sm text-muted-foreground">No OAuth clients connected.</p>}
    {items.map(item => <article key={item.id} className="space-y-2 border-t pt-3"><p className="font-medium">{item.client_name} · {item.revoked_at ? 'Revoked' : new Date(item.expires_at) < new Date() ? 'Expired' : 'Connected'}</p><p className="break-words text-sm">{item.scopes.join(', ')}</p><p className="text-sm">Last used: {displayDate(item.last_used_at)}</p>
      {!item.revoked_at && <button className="min-h-11 rounded border px-3" disabled={!!busy} onClick={async () => {
        setBusy(item.id); setError('');
        try { await api.delete(`/mcp/oauth/connections/${item.id}`); await load(); }
        catch (error) { setError(error instanceof Error ? error.message : 'Could not revoke. Retry.'); }
        finally { setBusy(''); }
      }}>Revoke OAuth access</button>}
    </article>)}{error && <p role="alert">{error}</p>}
  </section>;
}

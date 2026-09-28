'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { createClient } from '@/lib/supabase/client';
import { oauthApi } from '@/lib/api/browser-client';

type Details = {client_name: string; client_id: string; redirect_uri: string; scopes: string[]; resource: string};
const descriptions: Record<string, string> = {
  'mcp:people:read': 'Read your contacts and organizations', 'mcp:memory:read': 'Read saved notes and context',
  'mcp:projects:read': 'Read projects and ventures', 'mcp:tasks:read': 'Read tasks',
  'mcp:relationships:read': 'Read relationship history', 'mcp:calendar:read': 'Read saved meetings',
  'mcp:sessions:write': 'Save AI work sessions', 'mcp:memory:write': 'Create or update memories',
  'mcp:people:write': 'Create or update people', 'mcp:tasks:write': 'Create or update tasks',
  'mcp:decisions:write': 'Save decisions', 'mcp:projects:write': 'Create or update projects',
  'mcp:content:draft': 'Generate content drafts', offline_access: 'Stay connected with rotating refresh tokens (up to 30 days)',
};

export default function ConsentPage() {
  const [details, setDetails] = useState<Details | null>(null);
  const [request, setRequest] = useState('');
  const [scopes, setScopes] = useState<string[]>([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let active = true;
    void (async () => {
      const value = new URLSearchParams(window.location.hash.slice(1)).get('request') || sessionStorage.getItem('mcp-consent-request') || '';
      if (!/^[A-Za-z0-9_-]{43}$/.test(value)) throw new Error('Start this connection from your AI client.');
      sessionStorage.setItem('mcp-consent-request', value);
      window.history.replaceState(null, '', '/oauth/consent');
      const {data: {session}} = await createClient().auth.getSession();
      if (!session) { window.location.href = '/login?redirect=%2Foauth%2Fconsent'; return; }
      const info = await oauthApi.post<Details>('/oauth/consent/details', {request: value});
      if (active) { setRequest(value); setDetails(info); setScopes(info.scopes.filter(scope => scope.endsWith(':read'))); }
    })().catch(error => { if (active) setError(error instanceof Error ? error.message : 'Could not load consent.'); });
    return () => { active = false; };
  }, []);
  async function decide(approve: boolean) {
    setBusy(true); setError('');
    try {
      const result = await oauthApi.post<{redirect_to: string}>('/oauth/consent/decision', {request, confirmed: true, approve, scopes});
      sessionStorage.removeItem('mcp-consent-request');
      window.location.assign(result.redirect_to);
    } catch (error) { setError(error instanceof Error ? error.message : 'Could not save your decision.'); setBusy(false); }
  }
  return <main className="mx-auto min-h-screen max-w-xl space-y-5 px-4 py-10">
    <h1 className="text-2xl font-semibold">Connect your AI to Second Brain</h1>
    {details ? <>
      <p><strong>{details.client_name}</strong> is requesting access to your private context.</p>
      <p className="break-all text-sm text-muted-foreground">Client names are supplied by the requesting app. Check its callback: {details.redirect_uri}</p>
      <p className="text-sm">Only approve a connection you started. The receiving AI has its own data policy. This beta is unsuitable for highly sensitive or confidential information.</p>
      <fieldset className="space-y-3 rounded-xl border p-4"><legend className="px-2 font-medium">Choose permissions</legend>
        {details.scopes.map(scope => <label key={scope} className="flex min-h-11 items-start gap-3"><input className="mt-1" type="checkbox" disabled={busy} checked={scopes.includes(scope)} onChange={event => setScopes(previous => event.target.checked ? [...previous, scope] : previous.filter(item => item !== scope))} /><span className="min-w-0">{descriptions[scope] || scope}<span className="block break-all text-xs text-muted-foreground">{scope}</span></span></label>)}
      </fieldset>
      {scopes.some(scope => scope.endsWith(':write')) && <p className="rounded border p-3 text-sm">Write access lets this AI change the selected kinds of records. Approve only the permissions needed for your workflow. It cannot send messages for you.</p>}
      <p className="text-sm">Read permissions are selected first. To save a complete work session, select session, task, decision, memory and people write permissions. You can revoke this connection in Settings.</p>
      <div className="flex flex-wrap gap-3"><button className="min-h-11 rounded-lg bg-primary px-5 text-primary-foreground disabled:opacity-50" disabled={busy || !scopes.some(s => s !== 'offline_access')} onClick={() => decide(true)}>Approve selected access</button><button className="min-h-11 rounded-lg border px-5" disabled={busy} onClick={() => decide(false)}>Deny</button></div>
    </> : !error && <p role="status">Loading requested permissions…</p>}
    {error && <p role="alert" className="rounded border p-3">{error}</p>}
    <Link className="inline-block min-h-11 py-2 underline" href="/settings/ai-access">Manage AI access</Link>
  </main>;
}

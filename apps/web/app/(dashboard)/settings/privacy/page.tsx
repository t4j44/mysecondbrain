'use client';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api/browser-client';
import { createClient } from '@/lib/supabase/client';
import { env } from '@/lib/env';

export default function PrivacyPage() {
  const [mode, setMode] = useState('Loading');
  const [confirmation, setConfirmation] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [closing, setClosing] = useState(false);
  useEffect(() => {
    api.get<{status: string}>('/account/deletion-status').then(receipt => {
      if (receipt.status !== 'not_requested') {
        setClosing(true);
        setMode('Account closing');
        setMessage('Deletion status: ' + receipt.status);
        return;
      }
      return api.get<{ai_data_mode: string}>('/account/privacy').then(x => setMode(x.ai_data_mode));
    }).catch(e => setMessage(e.message));
  }, []);
  async function download() {
    setBusy(true);
    try {
      const {data: {session}} = await createClient().auth.getSession();
      const res = await fetch(env.NEXT_PUBLIC_API_BASE_URL.replace(/\/$/, '') + '/account/export', {headers: {Authorization: `Bearer ${session?.access_token}`}});
      if (!res.ok) throw new Error('Export could not be created. Please retry.');
      const url = URL.createObjectURL(await res.blob()); const link = document.createElement('a');
      link.href=url; link.download='second-brain-account.zip'; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
      setMessage('Downloaded JSON, CSV and Markdown. Original attachment bytes are separate.');
    } catch (e) { setMessage(e instanceof Error ? e.message : 'Export failed'); }
    finally { setBusy(false); }
  }
  return <div className="mx-auto max-w-2xl space-y-6"><h1 className="text-3xl font-semibold">Privacy &amp; Data</h1>
    <section className="rounded-xl border p-4 space-y-3"><h2 className="text-xl">AI data mode: {mode}</h2>
      <p>Free mode minimizes identifying text before sending relevant excerpts to Gemini. Redaction can miss details. Do not submit highly sensitive or confidential information.</p>
      <div className="flex flex-wrap gap-4"><Link className="underline" href="/settings/integrations">Connected integrations</Link><Link className="underline" href="/portfolio">Public portfolio links</Link></div>
    </section>
    <section className="rounded-xl border p-4 space-y-3"><h2 className="text-xl">Export your records</h2><p>Download portable JSON, CSV and Markdown, including archived records. Credentials are excluded. This archive does not contain original uploaded files.</p><button disabled={busy || closing} onClick={download} className="min-h-11 rounded border px-4">Download account export</button></section>
    <form className="rounded-xl border border-destructive p-4 space-y-3" onSubmit={async e => {e.preventDefault();setBusy(true);try {await api.post('/account/delete',{confirmation});setClosing(true);setMessage('Account access is blocked. Cleanup is queued. Keep this page open to check completion.');}catch(e){setMessage(e instanceof Error?e.message:'Deletion request failed');}finally{setBusy(false);}}}>
      <h2 className="text-xl">Delete my data and account</h2><p>This permanently removes your private records, files, indexes, credentials and public portfolio pages. Download an export first. Copies already exported to Google or saved by other people remain there. Provider backups expire under their retention policies.</p>
      <label className="block">Type DELETE MY ACCOUNT<input value={confirmation} onChange={e=>setConfirmation(e.target.value)} className="mt-2 min-h-11 w-full rounded border bg-background px-3" autoComplete="off" /></label>
      <button disabled={busy || closing || confirmation !== 'DELETE MY ACCOUNT'} className="min-h-11 rounded bg-destructive px-4 text-destructive-foreground">Permanently delete account</button>
    </form>
    {closing && <button className="min-h-11 rounded border px-4" onClick={async()=>{try{const x=await api.get<{status:string}>('/account/deletion-status');setMessage('Deletion status: '+x.status);if(x.status==='completed')await createClient().auth.signOut();}catch(e){setMessage(e instanceof Error?e.message:'Check failed');}}}>Check deletion status</button>}
    {message && <p role="status">{message}</p>}
  </div>;
}

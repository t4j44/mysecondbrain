'use client';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api/browser-client';
export default function SettingsOverviewPage() {
  const [counts, setCounts] = useState<Record<string, number> | null>(null);
  useEffect(() => { api.get<{ counts: Record<string, number> }>('/beta/value').then(value => setCounts(value.counts)).catch(() => setCounts(null)); }, []);
  const [outcome, setOutcome] = useState('useful'); const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false); const [message, setMessage] = useState('');
  return <div className="max-w-2xl space-y-6"><h1 className="text-2xl font-semibold">Settings and beta feedback</h1>
    <p>This is an early closed beta. Your canonical records stay in the private database. Free-tier AI receives minimized text; redaction can miss details. Avoid highly sensitive or confidential information.</p>
    <div className="flex flex-wrap gap-4"><Link href="/settings/privacy" className="underline">Privacy &amp; Data</Link><Link href="/settings/integrations" className="underline">Google connections</Link><Link href="/settings/export" className="underline">Export records</Link><Link href="/portfolio" className="underline">Portfolio</Link><Link href="/settings/ai-access" className="underline">AI assistant access</Link></div>
    {counts && <section className="rounded-xl border p-4"><h2 className="text-xl font-semibold">Your beta activity</h2>
      <p className="mt-2">{counts.capture_confirmed} captures saved · {counts.beta_retrieval} searches · {counts.beta_source_opened} source checks</p>
      <p className="mt-1 text-sm text-muted-foreground">Activity counts help you reflect on use. They do not prove answer accuracy or time saved.</p>
    </section>}
    <form className="space-y-4 rounded-xl border p-4" onSubmit={async event => {
      event.preventDefault(); setBusy(true); setMessage('');
      try { await api.post('/beta/feedback', { outcome, note }); setNote(''); setMessage('Feedback saved privately. Thank you for testing.'); }
      catch (error) { setMessage(error instanceof Error ? error.message : 'Feedback could not be saved.'); }
      finally { setBusy(false); }
    }}><h2 className="text-xl font-semibold">Did this help with real work?</h2>
      <label className="block">Outcome<select value={outcome} onChange={event => setOutcome(event.target.value)} className="mt-1 min-h-11 w-full rounded border bg-background px-3"><option value="useful">Useful</option><option value="not_useful">Not useful yet</option><option value="incorrect">Incorrect result</option><option value="bug">Something broke</option></select></label>
      <label className="block">What happened? (optional)<textarea rows={4} maxLength={2000} value={note} onChange={event => setNote(event.target.value)} className="mt-1 w-full rounded border bg-background p-3" /></label>
      <p className="text-sm text-muted-foreground">This feedback is private. It does not give permission to publish your words as a testimonial.</p>
      <button disabled={busy} className="min-h-11 rounded bg-primary px-4 text-primary-foreground">Save feedback</button>
    </form>{message && <p role="status">{message}</p>}
  </div>;
}

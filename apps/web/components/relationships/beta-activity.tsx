'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api/browser-client';
type Activity = {weeks: {week_start: string; active: boolean; followups_completed: number; suggestions_served: number; ask_answers: number}[]; willingness_to_pay: string | null; notice: string};
export function BetaActivity() {
  const [data, setData] = useState<Activity | null>(null); const [choice, setChoice] = useState('unsure'); const [busy, setBusy] = useState(false); const [message, setMessage] = useState('');
  useEffect(() => { api.get<Activity>('/relationships/activity').then(value => { setData(value); setChoice(value.willingness_to_pay || 'unsure'); }).catch(() => setMessage('Relationship activity could not be loaded.')); }, []);
  return <section className="space-y-4 rounded-xl border p-4"><h2 className="text-xl font-semibold">Relationship value</h2><p className="text-sm text-muted-foreground">Success means a follow-up you completed and recorded. Seeing a suggestion is not a successful outcome.</p>
    {data && <><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr><th className="p-2">Week (UTC)</th><th className="p-2">Active</th><th className="p-2">Completed follow-ups</th><th className="p-2">Supported Ask answers</th></tr></thead><tbody>{data.weeks.map(week => <tr key={week.week_start} className="border-t"><td className="p-2">{week.week_start}</td><td className="p-2">{week.active ? 'Yes' : 'No'}</td><td className="p-2">{week.followups_completed}</td><td className="p-2">{week.ask_answers}</td></tr>)}</tbody></table></div><p className="text-xs text-muted-foreground">{data.notice}</p></>}
    <form className="space-y-3 border-t pt-4" onSubmit={async event => { event.preventDefault(); setBusy(true); setMessage(''); try { await api.post('/relationships/willingness-to-pay', {response: choice}); setMessage('Interest saved. No subscription or payment was created.'); } catch (error) { setMessage(error instanceof Error ? error.message : 'Could not save interest.'); } finally { setBusy(false); } }}>
      <label className="block text-sm">If this reliably helped your relationships, would you pay $5/month?<select className="mt-2 min-h-11 w-full rounded border bg-background p-2" value={choice} onChange={event => setChoice(event.target.value)}><option value="unsure">I need more evidence</option><option value="yes">Yes</option><option value="no">No</option></select></label><p className="text-xs text-muted-foreground">A research question only. This is not a paid plan or payment authorization.</p><button disabled={busy} className="min-h-11 rounded border px-4">Save my answer</button>
    </form>{message && <p role="status" className="text-sm">{message}</p>}
  </section>;
}

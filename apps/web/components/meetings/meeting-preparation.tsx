'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { BookOpen, CheckSquare2, Users } from 'lucide-react';
import { api } from '@/lib/api/browser-client';
import { Button } from '@/components/ui/button';

type Source = { id: string; title: string; uri: string };
type PersonCard = { person: Source; notes: string; saved_role: string; saved_company: string;
  last_interaction: { source: Source; summary: string; date: string } | null;
  commitments: { source: Source; description: string; status: string; direction: string; due_at: string | null }[];
  more_commitments: boolean };
type Preparation = { generated_at: string; people: PersonCard[]; more_people: boolean; basis: string };
const status: Record<string, string> = { open: 'Open', in_progress: 'Working', waiting: 'Waiting', snoozed: 'Snoozed' };

export function MeetingPreparation({ meetingId }: { meetingId: string }) {
  const [data, setData] = useState<Preparation | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const sequence = useRef(0);
  useEffect(() => { setData(null); setBusy(false); setError(''); return () => { sequence.current += 1; }; }, [meetingId]);
  async function load() {
    const request = ++sequence.current;
    setBusy(true); setError(''); setData(null);
    try { const result = await api.get<Preparation>(`/meetings/${encodeURIComponent(meetingId)}/preparation`); if (request === sequence.current) setData(result); }
    catch { if (request === sequence.current) setError('Preparation could not be loaded. The meeting may have changed. Try again.'); }
    finally { if (request === sequence.current) setBusy(false); }
  }
  return <section className="mt-6 space-y-3 rounded-xl border bg-card p-4 sm:p-6" aria-labelledby="preparation-title">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <h2 id="preparation-title" className="flex items-center gap-2 font-semibold"><Users aria-hidden="true" className="h-5 w-5" />Prepare for the conversation</h2>
      <Button variant="outline" disabled={busy} onClick={() => void load()}>{busy ? 'Loading preparation…' : data ? 'Reload preparation' : 'Prepare meeting'}</Button>
    </div>
    {!data && !error && <p className="text-sm text-muted-foreground">People, recent context and open promises—with links to your records.</p>}
    {error && <p role="alert" className="text-sm">{error}</p>}
    {data && <>
      {data.people.length === 0 && <p className="text-sm">No saved participants are linked to this meeting yet. Add or confirm people before preparing.</p>}
      <div className="grid gap-3 lg:grid-cols-2">
        {data.people.map(card => <article key={card.person.id} className="min-w-0 space-y-3 rounded-xl border p-4">
          <div><Link className="inline-flex min-h-11 items-center break-words text-base font-medium underline underline-offset-4" href={card.person.uri}>{card.person.title}</Link>
            {(card.saved_role || card.saved_company) && <p className="break-words text-sm text-muted-foreground">Saved profile: {[card.saved_role, card.saved_company].filter(Boolean).join(' · ')}</p>}
          </div>
          {card.notes && <div className="text-sm"><p className="break-words">{card.notes}</p><Link className="inline-flex min-h-11 items-center underline" href={card.person.uri}>Profile source</Link></div>}
          {card.last_interaction && <details className="rounded-lg bg-muted/40 px-3">
            <summary className="min-h-11 cursor-pointer py-3 text-sm"><BookOpen className="mr-2 inline h-4 w-4" aria-hidden="true" />Last saved conversation</summary>
            <p className="break-words text-sm">{card.last_interaction.summary}</p>
            <Link className="inline-flex min-h-11 items-center text-sm underline" href={card.last_interaction.source.uri}>View source · {new Date(card.last_interaction.date).toLocaleDateString()}</Link>
          </details>}
          {card.commitments.length > 0 ? <div className="space-y-2">
            <h3 className="flex items-center gap-2 text-sm font-medium"><CheckSquare2 className="h-4 w-4" aria-hidden="true" />Open promises</h3>
            {card.commitments.map(promise => <div key={promise.source.id} className="rounded-lg bg-muted/40 px-3 py-2">
              <Link className="inline-flex min-h-11 items-center break-words text-sm underline underline-offset-4" href={promise.source.uri}>{promise.description}</Link>
              <p className="text-xs text-muted-foreground">{promise.direction === 'owed_by_me' ? 'You owe' : promise.direction === 'owed_to_me' ? 'Owed to you' : 'Direction not recorded'} · {status[promise.status] || 'Review status'}{promise.due_at ? ` · Due ${new Date(promise.due_at).toLocaleDateString()}` : ' · No deadline recorded'}</p>
            </div>)}
            {card.more_commitments && <Link className="inline-flex min-h-11 items-center text-sm underline" href={card.person.uri}>More promises on this profile</Link>}
          </div> : <p className="text-sm text-muted-foreground">No open promises recorded.</p>}
        </article>)}
      </div>
      {data.more_people && <p className="text-sm">Showing five linked people. See the participant list for everyone.</p>}
      <p className="text-xs text-muted-foreground">{data.basis} Refreshed {new Date(data.generated_at).toLocaleTimeString()}.</p>
    </>}
  </section>;
}

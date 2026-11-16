'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api/browser-client';
import { displayDate, type HomeData } from '@/lib/relationships';
import { FollowupCard } from '@/components/relationships/followup-card';
import { IntentPeople } from '@/components/relationships/intent-people';
import { RequestError } from '@/components/shared/request-error';
import { ArrowRight, UserPlus, Mic, FileText } from 'lucide-react';

export default function HomePage() {
  const [data, setData] = useState<HomeData | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    setError(null); setLoading(true);
    try { setData(await api.get<HomeData>('/relationships/home')); }
    catch (failure) { setError(failure); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  return <div className="mx-auto max-w-5xl space-y-6">
    <header className="space-y-2"><h1 className="text-[27px] font-semibold leading-tight tracking-tight sm:text-3xl">Today</h1><p className="text-sm text-muted-foreground">Your next steps, from the context you saved.</p></header>
    <section aria-label="Quick actions" className="grid gap-3 sm:grid-cols-3">
      <Link href="/capture" className="group flex min-h-28 items-start gap-3 rounded-2xl bg-primary p-4 text-primary-foreground sm:min-h-40 sm:flex-col sm:p-5"><FileText className="h-5 w-5 shrink-0" aria-hidden="true" /><div className="min-w-0 flex-1"><h2 className="font-semibold">Capture a note</h2><p className="mt-1 text-sm leading-relaxed">Save a thought, a file or something to remember.</p></div><ArrowRight className="h-4 w-4 shrink-0 self-end" aria-hidden="true" /></Link>
      <Link href="/meetings?capture=1" className="group flex min-h-28 items-start gap-3 rounded-2xl border bg-card p-4 hover:bg-accent sm:min-h-40 sm:flex-col sm:p-5"><Mic className="h-5 w-5 shrink-0 text-primary" aria-hidden="true" /><div className="min-w-0 flex-1"><h2 className="font-semibold">Record or upload a meeting</h2><p className="mt-1 text-sm leading-relaxed text-muted-foreground">Keep the conversation and review its next steps.</p></div><ArrowRight className="h-4 w-4 shrink-0 self-end text-muted-foreground" aria-hidden="true" /></Link>
      <Link href="/people/new" className="group flex min-h-28 items-start gap-3 rounded-2xl border bg-card p-4 hover:bg-accent sm:min-h-40 sm:flex-col sm:p-5"><UserPlus className="h-5 w-5 shrink-0 text-primary" aria-hidden="true" /><div className="min-w-0 flex-1"><h2 className="font-semibold">Add a person</h2><p className="mt-1 text-sm leading-relaxed text-muted-foreground">Remember who they are and how you met.</p></div><ArrowRight className="h-4 w-4 shrink-0 self-end text-muted-foreground" aria-hidden="true" /></Link>
    </section>
    {!!error && <RequestError error={error} onRetry={()=>void load()} />}
    {loading && <p role="status" className="min-h-24 text-muted-foreground">Loading your saved context…</p>}
    {data && !loading && !error && <>
      <section className="space-y-3"><div className="flex flex-wrap items-center justify-between gap-2"><h2 className="text-lg font-semibold">Needs your attention</h2><Link className="inline-flex min-h-11 items-center text-sm underline" href="/work/commitments">All promises</Link></div>
        {data.followups.length ? <div className="grid gap-3 lg:grid-cols-2">{data.followups.slice(0,3).map(item=><FollowupCard key={item.key} item={item} onChanged={load} />)}</div> : <div className="rounded-2xl border border-dashed bg-card/40 p-4"><p className="font-medium">No follow-ups due in this view.</p><p className="mt-1 text-sm text-muted-foreground">When you save a commitment, your next steps will appear here.</p></div>}
      </section>
      {!!data.meetings.length && <section className="space-y-3"><h2 className="text-xl font-semibold">Upcoming conversations</h2>{data.meetings.map(item=><article key={item.id} className="rounded-xl border p-4"><Link className="inline-flex min-h-11 items-center font-medium underline" href={item.uri}>{item.title}</Link><p className="text-sm text-muted-foreground">{displayDate(item.date)}</p><div className="flex flex-wrap gap-2">{item.people.map(person=><Link key={person.id} className="inline-flex min-h-11 items-center text-sm underline" href={person.uri}>{person.title}</Link>)}</div></article>)}</section>}
      {!!data.recent_activity.length && <section className="space-y-3"><h2 className="text-xl font-semibold">Recent context</h2>{data.recent_activity.slice(0,4).map(item=><article key={item.id} className="rounded-xl border p-4"><div className="flex flex-wrap justify-between gap-2"><Link className="inline-flex min-h-11 items-center font-medium underline" href={`/people/${item.person_id}`}>{item.name}</Link><time className="text-sm text-muted-foreground">{displayDate(item.date)}</time></div><p className="my-2 whitespace-pre-wrap text-base leading-relaxed">{item.summary||item.title}</p><Link className="inline-flex min-h-11 items-center text-sm underline" href={item.uri}>Review conversation</Link></article>)}</section>}
      <details className="rounded-xl border px-4"><summary className="flex min-h-12 cursor-pointer items-center font-medium">Explore your people and work</summary><div className="space-y-5 pb-4">
        <IntentPeople />
        {!!data.projects.length&&<section className="space-y-3"><h2 className="text-lg font-semibold">People connected to your work</h2>{data.projects.map(project=><article key={project.id} className="space-y-2 border-t pt-3"><Link className="inline-flex min-h-11 items-center font-medium underline" href={project.uri}>{project.title}</Link>{project.people.map(person=><div key={person.person_id}><Link className="inline-flex min-h-11 items-center underline" href={`/people/${person.person_id}`}>{person.name}</Link><p className="text-sm text-muted-foreground">{person.reason}</p><Link className="inline-flex min-h-11 items-center text-sm underline" href={person.evidence.uri}>Recorded connection</Link></div>)}</article>)}</section>}
        {!!data.opportunities.length&&<section className="space-y-3"><h2 className="text-lg font-semibold">Offers worth revisiting</h2>{data.opportunities.map(item=><article key={item.evidence.id} className="border-t pt-3"><Link className="inline-flex min-h-11 items-center underline" href={`/people/${item.person_id}`}>{item.name}</Link><p className="text-sm">{item.reason}</p><Link className="inline-flex min-h-11 items-center text-sm underline" href={item.evidence.uri}>Review source</Link></article>)}</section>}
        <p className="text-sm text-muted-foreground">{data.limits} Suggestions reflect saved records. Review sources before acting.</p>
      </div></details>
    </>}
  </div>;
}

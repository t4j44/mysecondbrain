'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api/browser-client';
import { displayDate, type HomeData } from '@/lib/relationships';
import { FollowupCard } from '@/components/relationships/followup-card';
import { IntentPeople } from '@/components/relationships/intent-people';
import { RequestError } from '@/components/shared/request-error';
import { ArrowRight, Users, MessageCircle, Sparkles } from 'lucide-react';

export default function HomePage() {
  const [data, setData] = useState<HomeData | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  const [dismissed, setDismissed] = useState(false);
  const load = useCallback(async () => {
    setError(null); setLoading(true);
    try { setData(await api.get<HomeData>('/relationships/home')); }
    catch (failure) { setError(failure); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  return <div className="mx-auto max-w-5xl space-y-6">
    <header className="space-y-2"><h1 className="text-[27px] font-semibold leading-tight tracking-tight sm:text-3xl">Today</h1><p className="text-sm text-muted-foreground">Your next steps, from the context you saved.</p></header>
    <Link href="/capture" className="flex min-h-14 items-center justify-between rounded-2xl bg-primary px-5 font-semibold text-primary-foreground shadow-sm"><span className="inline-flex items-center gap-2"><Sparkles className="h-5 w-5" /> Capture something</span><ArrowRight className="h-5 w-5" /></Link>
    <div className="grid grid-cols-3 gap-2"><Link href="/people" className="flex min-h-16 flex-col items-center justify-center gap-1 rounded-xl border bg-card text-xs font-medium"><Users className="h-5 w-5 text-primary" />People</Link><Link href="/work/commitments" className="flex min-h-16 flex-col items-center justify-center gap-1 rounded-xl border bg-card text-xs font-medium"><ArrowRight className="h-5 w-5 text-primary" />Promises</Link><Link href="/assistant" className="flex min-h-16 flex-col items-center justify-center gap-1 rounded-xl border bg-card text-xs font-medium"><MessageCircle className="h-5 w-5 text-primary" />Ask memory</Link></div>
    {!!error && <RequestError error={error} onRetry={()=>void load()} />}
    {loading && <p role="status" className="min-h-24 text-muted-foreground">Loading your saved context…</p>}
    {data && !loading && !error && <>
      {!data.activation.first_activated_at && !dismissed && <section className="space-y-2 rounded-2xl border bg-card p-4 sm:p-5">
        <div className="flex items-start justify-between gap-3"><div><h2 className="text-base font-semibold">Get started in 3 steps</h2><p className="mt-1 text-xs text-muted-foreground">Add one connection to unlock useful follow-ups.</p></div><button type="button" onClick={()=>setDismissed(true)} className="min-h-11 min-w-11 text-sm text-muted-foreground">Dismiss</button></div>
        <ol className="divide-y"><li><Link className="flex min-h-12 items-center gap-3 py-3" href="/people/new"><span className="text-primary">1</span>Add a person</Link></li><li><Link className="flex min-h-12 items-center gap-3 py-3" href="/capture"><span className="text-primary">2</span>Record how you met</Link></li><li><Link className="flex min-h-12 items-center gap-3 py-3" href="/work/commitments"><span className="text-primary">3</span>Create or review a follow-up</Link></li></ol>
      </section>}
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

'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api/browser-client';
import { displayDate, type HomeData } from '@/lib/relationships';
import { FollowupCard } from '@/components/relationships/followup-card';

export default function HomePage() {
  const [data, setData] = useState<HomeData | null>(null);
  const [error, setError] = useState('');
  const load = useCallback(async () => {
    setError('');
    try { setData(await api.get<HomeData>('/relationships/home')); }
    catch (error) { setError(error instanceof Error ? error.message : 'Could not load your relationships.'); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  return <div className="mx-auto max-w-6xl space-y-8">
    <header className="flex flex-wrap items-start justify-between gap-4"><div><h1 className="text-3xl font-semibold">What deserves your attention?</h1><p className="mt-2 text-muted-foreground">Your people, promises, and next conversations.</p></div><Link className="inline-flex min-h-11 items-center rounded-lg bg-primary px-4 text-primary-foreground" href="/capture">Capture a conversation</Link></header>
    {error && <div role="alert" className="rounded-xl border p-4"><p>{error}</p><button className="mt-3 min-h-11 underline" onClick={load}>Retry</button></div>}
    {!data && !error && <p role="status">Loading your relationship context…</p>}
    {data && <>
      {!data.activation.first_activated_at && <section className="space-y-3 rounded-xl border p-5"><h2 className="text-xl font-semibold">Build context that can help you</h2><p className="text-sm text-muted-foreground">Start with one project and a few people you already know. Record how you met, recent conversations, and any promises.</p><div className="grid gap-2 sm:grid-cols-2">{Object.entries(data.activation.targets).map(([key, target]) => <Link key={key} className="flex min-h-11 items-center justify-between gap-3 rounded border p-3 text-sm" href={key === 'people' ? '/people/new' : key === 'projects' ? '/projects' : key === 'ask_answers' ? '/assistant' : '/capture'}><span>{({people: 'Add your first people', interactions: 'Record recent interactions', projects: 'What are you working on?', commitments: 'Save a promise or follow-up', ask_answers: 'Ask your first network question'} as Record<string, string>)[key]}</span><span>{Math.min(data.activation.counts[key], target)}/{target}</span></Link>)}</div></section>}
      {!data.recent_activity.length && !data.followups.length && <section className="rounded-xl border bg-card p-6"><h2 className="text-xl font-semibold">Start with someone you know</h2><p className="mt-2 text-muted-foreground">Add a person, a recent conversation, and what you promised. Your next steps will appear here from those records.</p><div className="mt-4 flex flex-wrap gap-4"><Link className="underline" href="/people/new">Add a person</Link><Link className="underline" href="/work">What are you working on?</Link><Link className="underline" href="/capture">Record a conversation</Link></div></section>}
      <section className="space-y-4"><div className="flex flex-wrap items-center justify-between gap-2"><h2 className="text-xl font-semibold">People to follow up with</h2><Link className="text-sm underline" href="/work/commitments">All promises</Link></div>
        {data.followups.length ? <div className="grid gap-4 lg:grid-cols-2">{data.followups.map(item => <FollowupCard key={item.key} item={item} onChanged={load} />)}</div> : <p className="text-muted-foreground">No due promises or cooling relationships in the current view. Capture a follow-up when one comes up.</p>}
      </section>
      <div className="grid gap-8 lg:grid-cols-2">
        <section className="space-y-3"><h2 className="text-xl font-semibold">Upcoming conversations</h2>{!data.meetings.length && <p className="text-muted-foreground">No upcoming meetings recorded. <Link className="underline" href="/meetings">Add a meeting</Link></p>}{data.meetings.map(item => <article key={item.id} className="space-y-2 rounded-xl border p-4"><Link className="font-medium underline" href={item.uri}>{item.title}</Link><p className="text-sm text-muted-foreground">{displayDate(item.date)}</p><div className="flex flex-wrap gap-3">{item.people.map(person => <Link key={person.id} className="text-sm underline" href={person.uri}>{person.title}</Link>)}</div></article>)}</section>
        <section className="space-y-3"><h2 className="text-xl font-semibold">People connected to your work</h2>{!data.projects.length && <p className="text-muted-foreground">Add your first <Link className="underline" href="/projects">project</Link>, then link a conversation to it in Capture.</p>}{data.projects.map(project => <article key={project.id} className="space-y-3 rounded-xl border p-4"><Link className="font-medium underline" href={project.uri}>{project.title}</Link>{project.people.map(person => <div key={person.person_id}><Link className="underline" href={`/people/${person.person_id}`}>{person.name}</Link><p className="mt-1 text-sm text-muted-foreground">{person.reason}</p><Link className="text-xs underline" href={person.evidence.uri}>Recorded connection</Link></div>)}{!project.people.length && <p className="text-sm text-muted-foreground">No people linked through conversations yet.</p>}</article>)}</section>
      </div>
      {!!data.opportunities.length && <section className="space-y-3"><h2 className="text-xl font-semibold">Offers worth revisiting</h2><p className="text-sm text-muted-foreground">These notes mention an offer, introduction, or opportunity. Review the source before acting.</p>{data.opportunities.map(item => <article key={item.evidence.id} className="rounded-xl border p-4"><Link className="font-medium underline" href={`/people/${item.person_id}`}>{item.name}</Link><p className="my-2">{item.reason}</p><Link className="text-sm underline" href={item.evidence.uri}>Review source</Link></article>)}</section>}
      <section className="space-y-3"><h2 className="text-xl font-semibold">Recent relationship activity</h2>{!data.recent_activity.length && <p className="text-muted-foreground">Your recorded conversations and follow-up outcomes will appear here.</p>}{data.recent_activity.map(item => <article key={item.id} className="rounded-xl border p-4"><div className="flex flex-wrap justify-between gap-2"><Link className="font-medium underline" href={`/people/${item.person_id}`}>{item.name}</Link><time className="text-sm text-muted-foreground">{displayDate(item.date)}</time></div><p className="my-2 whitespace-pre-wrap">{item.summary || item.title}</p><Link className="text-sm underline" href={item.uri}>View interaction</Link></article>)}</section>
      <p className="text-xs text-muted-foreground">{data.limits} Suggestions reflect saved records, not everything that happened outside Second Brain.</p>
    </>}
  </div>;
}

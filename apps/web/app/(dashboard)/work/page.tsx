'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { workNavigation } from '@/lib/navigation';
import { PageHeader } from '@/components/shared/page-header';
import { RequestError } from '@/components/shared/request-error';
import { api } from '@/lib/api/browser-client';
import { displayDate, type HomeData } from '@/lib/relationships';
import type { ListResponse } from '@/lib/api/domains';

type WorkTask = { id:string; title:string; due_date?:string|null; status:string };
export default function WorkPage() {
  const [home,setHome]=useState<HomeData|null>(null);
  const [tasks,setTasks]=useState<WorkTask[]>([]);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState<unknown>(null);
  const load=useCallback(async()=>{
    setLoading(true);setError(null);
    const results=await Promise.allSettled([api.get<HomeData>('/relationships/home'),api.get<ListResponse<WorkTask>>('/tasks',{params:{limit:5}})]);
    if(results[0].status==='fulfilled')setHome(results[0].value);else setError(results[0].reason);
    if(results[1].status==='fulfilled')setTasks(results[1].value.items||[]);else setError(results[1].reason);
    setLoading(false);
  },[]);
  useEffect(()=>{void load();},[load]);
  return <div className="mx-auto max-w-5xl space-y-6">
    <PageHeader title="Work" description="Tasks, promises and projects in one place." actions={<Link className="inline-flex min-h-11 items-center rounded-xl bg-primary px-4 text-sm font-semibold text-primary-foreground" href="/tasks">View tasks</Link>} />
    {!!error&&<RequestError error={error} onRetry={()=>void load()} />}
    {loading&&<p role="status" className="min-h-24 text-muted-foreground">Loading your work…</p>}
    {!loading&&!!tasks.length&&<section><h2 className="mb-3 text-xl font-semibold">Recent tasks</h2><div className="divide-y rounded-xl border px-4">{tasks.map(task=><Link key={task.id} href="/tasks" className="flex min-h-14 flex-wrap items-center justify-between gap-2 py-3"><span>{task.title}</span><span className="text-sm text-muted-foreground">{task.status}{task.due_date?` · ${displayDate(task.due_date)}`:''}</span></Link>)}</div></section>}
    {!loading&&home&&!!home.followups.length&&<section className="space-y-3"><h2 className="text-xl font-semibold">Follow-ups to review</h2>{home.followups.slice(0,3).map(item=><Link key={item.key} href={`/people/${item.person_id}`} className="block min-h-14 rounded-xl border p-4"><span className="font-medium">{item.name}</span><span className="mt-1 block text-xs leading-relaxed text-muted-foreground">{item.why_now}</span></Link>)}</section>}
    {!loading&&home&&!!home.meetings.length&&<section className="space-y-3"><h2 className="text-xl font-semibold">Upcoming meetings</h2>{home.meetings.slice(0,3).map(item=><Link key={item.id} href={item.uri} className="flex min-h-14 flex-wrap items-center justify-between gap-2 rounded-xl border p-4"><span>{item.title}</span><span className="text-sm text-muted-foreground">{displayDate(item.date)}</span></Link>)}</section>}
    {!loading&&!error&&!tasks.length&&!home?.followups.length&&!home?.meetings.length&&<p className="text-muted-foreground">No tasks or upcoming conversations in this view. Add a task above to get started.</p>}
    <section><h2 className="mb-3 text-lg font-semibold">Explore work</h2><div className="grid gap-2 sm:grid-cols-2">{workNavigation.map(item=><Link key={item.href} href={item.href} className="flex min-h-20 items-center justify-between gap-3 rounded-2xl border bg-card p-4"><span className="min-w-0"><span className="block font-medium">{item.title}</span><span className="mt-1 block text-sm text-muted-foreground">{item.description}</span></span><ArrowRight aria-hidden="true" className="h-4 w-4 shrink-0 text-primary" /></Link>)}</div></section>
    <Link href="/assistant" className="inline-flex min-h-11 items-center text-sm text-primary underline">Find people connected to your work</Link>
  </div>;
}

'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api/browser-client';
import { displayDate, type Profile } from '@/lib/relationships';
import { FollowupCard } from './followup-card';

export function PersonContext({personId}: {personId: string}) {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [error, setError] = useState('');
  const load = useCallback(async () => {
    setError('');
    try { setProfile(await api.get<Profile>(`/relationships/people/${personId}`)); }
    catch (error) { setError(error instanceof Error ? error.message : 'Could not load relationship context.'); }
  }, [personId]);
  useEffect(() => { void load(); }, [load]);
  if (error) return <div role="alert" className="rounded-xl border p-4">{error}<button className="ml-3 min-h-11 underline" onClick={load}>Retry</button></div>;
  if (!profile) return <p role="status">Loading relationship history…</p>;
  const section = 'space-y-3 rounded-xl border border-[#301642] bg-[#0a0510] p-4 sm:p-6';
  return <div className="mb-6 space-y-6">
    <section className={section}><div className="flex flex-wrap items-center justify-between gap-2"><h2 className="text-xl font-semibold">Relationship brief</h2><span className="rounded-full border px-3 py-1 text-sm">{profile.recency.label}</span></div>
      {profile.brief.map((item, index) => <p key={index}>{item.text} <Link className="text-sm underline" href={item.evidence.uri}>Source</Link></p>)}
      <p className="text-sm text-slate-400">{profile.recency.explanation}</p><details className="text-sm text-slate-400"><summary className="cursor-pointer">How this label is calculated</summary><p className="mt-2">{profile.recency.rule}</p></details>
      <dl className="grid gap-3 text-sm sm:grid-cols-2"><div><dt className="text-slate-400">Where we met</dt><dd>{profile.person.where_met || profile.timeline.at(-1)?.location || 'Not recorded'}</dd></div><div><dt className="text-slate-400">When we met</dt><dd>{displayDate(profile.person.when_met || profile.first_interaction)}</dd></div><div><dt className="text-slate-400">First recorded interaction</dt><dd>{displayDate(profile.first_interaction)}</dd></div><div><dt className="text-slate-400">Last recorded interaction</dt><dd>{displayDate(profile.last_interaction)}</dd></div></dl>
    </section>
    <section className="space-y-3"><h2 className="text-xl font-semibold">Why this person may matter now</h2>{profile.followups.map(item => <FollowupCard key={item.key} item={item} onChanged={load} />)}{!profile.followups.length && <p className="text-sm text-slate-400">No due follow-up in the current records. The work and history below may provide context for your next conversation.</p>}</section>
    <section className={section}><h2 className="text-xl font-semibold">Promises and follow-ups</h2>{(['owed_by_me', 'owed_to_me', 'unspecified'] as const).map(direction => <div key={direction}><h3 className="font-medium">{({owed_by_me: 'What I owe', owed_to_me: 'What they offered', unspecified: 'Direction not recorded'})[direction]}</h3>{profile.commitments.filter(item => item.direction === direction).map(item => <p className="mt-2 text-sm" key={item.id}><Link className="underline" href={item.uri}>{item.title}</Link> · {item.status} · {displayDate(item.due_at)}</p>)}{!profile.commitments.some(item => item.direction === direction) && <p className="mt-1 text-sm text-slate-400">None recorded.</p>}</div>)}
      {!!profile.tasks.length && <div><h3 className="font-medium">Linked tasks</h3>{profile.tasks.map(item => <p className="mt-2 text-sm" key={item.id}><Link className="underline" href={item.uri}>{item.title}</Link> · {item.status}</p>)}</div>}
    </section>
    <section className={section}><h2 className="text-xl font-semibold">Work and connections</h2>{profile.related.filter(item => !['interaction', 'memory', 'task', 'commitment'].includes(item.kind)).map(item => <div key={`${item.kind}:${item.id}`}><Link className="font-medium underline" href={item.uri}>{item.title}</Link><span className="ml-2 text-xs text-slate-400">{item.kind}</span><p className="mt-1 text-sm text-slate-400">{item.reason} <Link className="underline" href={item.evidence.uri}>Evidence</Link></p></div>)}{!profile.related.length && <p className="text-sm text-slate-400">No explicit connections yet. Link a project or venture when capturing your next conversation.</p>}
      {!!profile.affiliations.length && <div><h3 className="font-medium">Company history</h3>{profile.affiliations.map((role, index) => <p className="mt-2 text-sm" key={`${role.id}:${index}`}><Link className="underline" href={role.uri}>{role.title}</Link>{role.role ? ` · ${role.role}` : ''} · {role.current ? 'Current recorded affiliation' : 'Previous affiliation'}</p>)}</div>}
    </section>
    <section className={section}><div className="flex flex-wrap justify-between gap-3"><h2 className="text-xl font-semibold">Relationship timeline</h2><Link className="text-sm underline" href="/capture">Record a conversation</Link></div>{!!profile.topics.length && <p className="text-sm text-slate-400">Topics discussed: {profile.topics.join(', ')}</p>}{profile.timeline.map(item => <article className="border-l-2 border-[#301642] pl-4" key={item.id}><time className="text-xs text-slate-400">{displayDate(item.date)}{item.location ? ` · ${item.location}` : ''}</time><p className="my-2 whitespace-pre-wrap text-sm">{item.summary || item.title}</p><Link className="text-xs underline" href={item.uri}>Open interaction</Link></article>)}{!profile.timeline.length && <p className="text-sm text-slate-400">No interactions recorded.</p>}</section>
    <p className="text-xs text-slate-400">{profile.limits}</p>
  </div>;
}

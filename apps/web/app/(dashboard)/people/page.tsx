'use client';

import * as React from 'react';
import Link from 'next/link';
import { Search, Plus, ArrowUpRight } from 'lucide-react';
import { ResponsivePageContainer } from '@/components/shared/responsive-page-container';
import { PageHeader } from '@/components/shared/page-header';
import { LoadingState } from '@/components/shared/loading-state';
import { ErrorState } from '@/components/shared/error-state';
import { usePeople } from '@/hooks/usePeople';
import { api } from '@/lib/api/browser-client';
import type { Person } from '@/lib/api/domains';

const FILTER_TAGS = ['all', 'mentor', 'investor', 'peer', 'collaborator', 'lead', 'client', 'contact'];

export default function PeopleNetworkPage() {
  const [searchQuery, setSearchQuery] = React.useState('');
  const [debouncedSearch, setDebouncedSearch] = React.useState('');
  const [selectedTag, setSelectedTag] = React.useState('all');
  React.useEffect(() => { const timer = setTimeout(() => setDebouncedSearch(searchQuery), 300); return () => clearTimeout(timer); }, [searchQuery]);
  const { people, total, loading, loadingMore, hasMore, loadMore, error, refetch, createPerson } = usePeople({ search: debouncedSearch, tag: selectedTag, pageSize: 30 });
  const hasFilters = Boolean(debouncedSearch.trim()) || selectedTag !== 'all';
  const [quickAddInput, setQuickAddInput] = React.useState('');
  const [isAdding, setIsAdding] = React.useState(false);
  const [pendingFollowups, setPendingFollowups] = React.useState<string[]>([]);
  const [feedback, setFeedback] = React.useState<{ text: string; failed?: boolean; href?: string } | null>(null);
  const addingRef = React.useRef(false);

  async function handleQuickAdd(event: React.FormEvent) {
    event.preventDefault();
    if (!quickAddInput.trim() || addingRef.current) return;
    addingRef.current = true; setIsAdding(true); setFeedback(null);
    const text = quickAddInput.trim();
    const match = text.match(/^(?:met\s+)?(.+?)(?:,\s*(.+?))?\s+(?:at|@)\s+(.+?)(?:\s+-\s+(.*))?$/iu);
    try {
      const person = await createPerson({ name: match?.[1]?.trim() || text, role: match?.[2]?.trim(), company: match?.[3]?.trim(), notes: match?.[4]?.trim(), relationship_type: 'contact' });
      setQuickAddInput(''); setFeedback({ text: `${person.name} saved.`, href: `/people/${person.id}` });
    } catch { setFeedback({ text: 'Could not save this person. Your text is kept. Try again.', failed: true }); }
    finally { addingRef.current = false; setIsAdding(false); }
  }
  async function followUp(person: Person) {
    if (pendingFollowups.includes(person.id)) return;
    setPendingFollowups(previous => [...previous, person.id]); setFeedback(null);
    try {
      await api.post('/tasks', { title: `Follow up with ${person.name}`, priority:'high',person_id:person.id,due_date:new Date(Date.now()+86400000*2).toISOString() });
      setFeedback({ text: `Follow-up for ${person.name} saved, due in 2 days.`, href:'/tasks' });
    } catch { setFeedback({ text:'Could not save the follow-up. Try again.', failed:true }); }
    finally { setPendingFollowups(previous => previous.filter(id => id !== person.id)); }
  }
  return <ResponsivePageContainer>
    <PageHeader title="People" description="Find someone and pick up where you left off." actions={<Link href="/people/new" data-testid="person-create" className="inline-flex min-h-11 items-center gap-2 rounded-lg bg-primary px-4 text-primary-foreground"><Plus className="h-4 w-4" />Add person</Link>} />
    <label className="relative block"><span className="sr-only">Search people, companies and notes</span><Search aria-hidden="true" className="pointer-events-none absolute left-3 top-3.5 h-5 w-5 text-muted-foreground" />
      <input data-testid="people-search" type="search" maxLength={100} value={searchQuery} onChange={event => setSearchQuery(event.target.value)} placeholder="Search people, companies, notes…" className="min-h-12 w-full rounded-xl border bg-card py-3 pl-10 pr-3 text-base" />
    </label>
    <fieldset><legend className="sr-only">Filter by relationship</legend><div className="flex flex-wrap gap-2">{FILTER_TAGS.map(tag => <button key={tag} type="button" aria-pressed={selectedTag===tag} onClick={() => setSelectedTag(tag)} className={`min-h-11 rounded-lg border px-3 text-sm capitalize ${selectedTag===tag?'bg-primary text-primary-foreground':'bg-card text-muted-foreground hover:text-foreground'}`}>{tag==='all'?'Everyone':tag}</button>)}</div></fieldset>
    <details className="rounded-xl border bg-card px-4"><summary className="flex min-h-11 cursor-pointer items-center text-sm">Quick add from a short note</summary>
      <form onSubmit={handleQuickAdd} className="space-y-3 pb-4"><label className="block space-y-2"><span className="text-sm text-muted-foreground">Name, role @ company — optional note</span><input aria-label="Quick add person" value={quickAddInput} onChange={event=>setQuickAddInput(event.target.value)} maxLength={1000} placeholder="Farzana, Designer @ Studio" className="min-h-12 w-full rounded-lg border bg-background px-3 text-base" /></label>
        <button type="submit" disabled={!quickAddInput.trim()||isAdding} className="min-h-11 rounded-lg border px-4 disabled:opacity-50">{isAdding?'Saving…':'Save person'}</button></form>
    </details>
    {feedback && <p role={feedback.failed?'alert':'status'} className="rounded-lg border p-3 text-sm">{feedback.text} {feedback.href && <Link href={feedback.href} className="inline-flex min-h-11 items-center underline">View saved result</Link>}</p>}
    {error && <ErrorState error={error} onRetry={refetch} />}
    {loading ? <LoadingState rows={3} showHeader={false} /> : !people.length && !error ? <section className="space-y-2 py-6"><h2 className="text-lg font-medium">{hasFilters?'No matching people':'No people saved yet'}</h2><p className="text-muted-foreground">{hasFilters?'Try a different name or relationship filter.':'Start with Add person above, then save a conversation.'}</p>{hasFilters&&<button type="button" className="min-h-11 underline" onClick={()=>{setSearchQuery('');setSelectedTag('all');}}>Clear filters</button>}</section> : <div className="grid gap-3 lg:grid-cols-2">{people.map(person=><article key={person.id} data-testid="person-card" className="min-w-0 rounded-xl border bg-card p-4">
      <Link href={`/people/${person.id}`} className="flex min-h-11 min-w-0 items-start justify-between gap-3"><span className="min-w-0"><span className="block text-lg font-medium leading-snug">{person.name}</span><span className="mt-1 block text-sm text-muted-foreground">{[person.role,person.company].filter(Boolean).join(' · ')||'Contact'}</span></span><ArrowUpRight className="mt-1 h-5 w-5 shrink-0 text-primary" aria-hidden="true" /></Link>
      {person.notes&&<p className="mt-3 line-clamp-2 whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground">{person.notes}</p>}
      <div className="mt-3 flex flex-wrap items-center justify-between gap-2"><span className="text-sm capitalize text-muted-foreground">{person.relationship_type}</span><button type="button" disabled={pendingFollowups.includes(person.id)} onClick={()=>void followUp(person)} className="min-h-11 rounded-lg border px-3 text-sm text-primary disabled:opacity-50">{pendingFollowups.includes(person.id)?'Saving…':'Follow up in 2 days'}</button></div>
    </article>)}</div>}
    {!loading&&total>0&&<div className="flex flex-wrap items-center justify-between gap-3 py-3"><p role="status" className="text-sm text-muted-foreground">Showing {people.length} of {total} matching contacts</p>{hasMore&&<button type="button" disabled={loadingMore} onClick={()=>void loadMore()} className="min-h-11 rounded-lg border px-4 text-sm">{loadingMore?'Loading contacts…':'Load more contacts'}</button>}</div>}
  </ResponsivePageContainer>;
}

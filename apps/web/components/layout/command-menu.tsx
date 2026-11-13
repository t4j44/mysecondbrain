'use client';

import * as React from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Search, X } from 'lucide-react';
import { primaryNavigation, secondaryNavigation, workNavigation } from '@/lib/navigation';
import { api } from '@/lib/api/browser-client';

const destinations = Array.from(new Map([
  ...primaryNavigation, ...workNavigation, ...secondaryNavigation,
  { title: 'Capture', href: '/capture' }, { title: 'Organizations', href: '/organizations' },
  { title: 'AI connections', href: '/settings/ai-access' },
].map(item => [item.href, item])).values());
type SavedResult = { id: string; entity_type: string; title: string; snippet: string; segment_id?: string | null; start_seconds?: number | null };
function sourceHref(item: SavedResult) {
  const id = encodeURIComponent(item.id);
  if (item.entity_type === 'person') return `/people/${id}`;
  if (item.entity_type === 'meeting') return `/meetings/${id}${item.segment_id ? `#segment-${encodeURIComponent(item.segment_id)}` : ''}`;
  return `/sources/${encodeURIComponent(item.entity_type)}/${id}`;
}

export function CommandMenu() {
  const [open, setOpen] = React.useState(false);
  const [query, setQuery] = React.useState('');
  const [results, setResults] = React.useState<SavedResult[] | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState('');
  const request = React.useRef(0);
  const pathname = usePathname();
  function clearSearch(value = '') { request.current += 1; setQuery(value); setResults(null); setLoading(false); setError(''); }
  function changeOpen(value: boolean) { clearSearch(); setOpen(value); }
  React.useEffect(() => { request.current += 1; setOpen(false); setQuery(''); setResults(null); setLoading(false); setError(''); }, [pathname]);
  React.useEffect(() => {
    const listener = (event: KeyboardEvent) => {
      if (event.key === 'k' && (event.metaKey || event.ctrlKey)) { event.preventDefault(); clearSearch(); setOpen(previous => !previous); }
    };
    window.addEventListener('keydown', listener);
    return () => { request.current += 1; window.removeEventListener('keydown', listener); };
  }, []);
  async function search(event: React.FormEvent) {
    event.preventDefault();
    const term = query.trim();
    if (!term || loading) return;
    const current = ++request.current;
    setLoading(true); setResults(null); setError('');
    try {
      const data = await api.post<{ results: SavedResult[] }>('/ai/search', { query: term });
      if (current === request.current) setResults(data.results);
    } catch { if (current === request.current) setError('Could not search your saved context. Try again.'); }
    finally { if (current === request.current) setLoading(false); }
  }
  const pages = destinations.filter(item => item.title.toLowerCase().includes(query.trim().toLowerCase()));
  return <Dialog.Root open={open} onOpenChange={changeOpen}>
    <Dialog.Trigger asChild><button type="button" className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border bg-card text-muted-foreground hover:text-foreground xl:w-56 xl:justify-between xl:px-3" aria-label="Search"><Search className="h-5 w-5" aria-hidden="true" /><span className="hidden text-sm xl:inline">Search anything…</span><kbd className="hidden text-xs xl:inline">Ctrl K</kbd></button></Dialog.Trigger>
    <Dialog.Portal><Dialog.Overlay className="fixed inset-0 z-[200] bg-black/50" /><Dialog.Content aria-describedby={undefined} className="fixed inset-x-4 top-4 z-[201] mx-auto flex max-h-[calc(100dvh-2rem)] max-w-xl flex-col rounded-xl border bg-popover p-4 text-popover-foreground shadow-xl">
      <div className="mb-3 flex items-center justify-between gap-2"><Dialog.Title className="font-semibold">Search your workspace</Dialog.Title><Dialog.Close asChild><button type="button" aria-label="Close search" className="inline-flex h-11 w-11 items-center justify-center rounded-lg border"><X className="h-5 w-5" aria-hidden="true" /></button></Dialog.Close></div>
      <form onSubmit={search} className="flex flex-wrap gap-2">
        <label className="min-w-0 flex-[1_1_12rem]"><span className="sr-only">Search anything</span><input type="search" maxLength={500} value={query} onChange={event => clearSearch(event.target.value)} placeholder="A person, promise or conversation…" className="min-h-12 w-full rounded-lg border bg-background px-3 text-base" /></label>
        <button type="submit" disabled={!query.trim() || loading} className="min-h-12 rounded-lg bg-primary px-3 text-sm font-medium text-primary-foreground disabled:opacity-50">{loading ? 'Searching…' : 'Search saved context'}</button>
      </form>
      <div className="mt-3 min-h-0 space-y-4 overflow-y-auto">
        {loading && <p role="status" className="text-sm text-muted-foreground">Searching your saved sources…</p>}
        {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
        {results && <section aria-label="Saved context results"><h2 className="text-sm font-medium">Saved context</h2>{results.length ? results.map((item, index) => <Dialog.Close key={`${item.entity_type}:${item.id}:${index}`} asChild><Link href={sourceHref(item)} className="mt-2 block min-h-12 rounded-lg border p-3 hover:bg-muted"><span className="block font-medium">{item.title}</span><span className="mt-1 block text-xs text-muted-foreground">{item.entity_type.replaceAll('_', ' ')}{item.start_seconds != null ? ` · ${Math.floor(item.start_seconds / 60)}:${String(Math.floor(item.start_seconds % 60)).padStart(2, '0')}` : ''}</span><span className="mt-2 line-clamp-2 text-sm text-muted-foreground">{item.snippet}</span></Link></Dialog.Close>) : <p role="status" className="py-3 text-sm text-muted-foreground">No saved sources matched. Try another name or phrase.</p>}</section>}
        <nav aria-label="Page search results"><h2 className="mb-1 text-sm font-medium">Go to a page</h2>{pages.length ? pages.map(item => <Dialog.Close key={item.href} asChild><Link href={item.href} className="flex min-h-12 items-center rounded-lg px-3 text-sm hover:bg-muted">{item.title}</Link></Dialog.Close>) : <p className="py-3 text-sm text-muted-foreground">No matching pages.</p>}</nav>
      </div>
    </Dialog.Content></Dialog.Portal>
  </Dialog.Root>;
}

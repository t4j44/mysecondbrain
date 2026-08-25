'use client';

import * as React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Users, Search, Plus, ArrowUpRight, CheckSquare } from 'lucide-react';
import { ResponsivePageContainer } from '@/components/shared/responsive-page-container';
import { LoadingState } from '@/components/shared/loading-state';
import { ErrorState } from '@/components/shared/error-state';
import { EmptyState } from '@/components/shared/empty-state';
import { useToast } from '@/components/ui/use-toast';
import { usePeople } from '@/hooks/usePeople';
import { api } from '@/lib/api/browser-client';
import { formatApiError } from '@/lib/api/format-error';
import type { Person } from '@/lib/api/domains';

const FILTER_TAGS = ['all', 'mentor', 'investor', 'peer', 'collaborator', 'lead', 'client', 'contact'];

export default function PeopleNetworkPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { people, loading, error, refetch, createPerson } = usePeople();

  const [searchQuery, setSearchQuery] = React.useState('');
  const [selectedTag, setSelectedTag] = React.useState('all');
  const [quickAddInput, setQuickAddInput] = React.useState('');
  const [isAdding, setIsAdding] = React.useState(false);

  const parseQuickAdd = (text: string) => {
    const metMatch = text.match(
      /^(?:met\s+)?([a-zA-Z\s.-]+?)(?:,\s*([a-zA-Z\s]+?))?\s*(?:at|@)\s*([a-zA-Z0-9\s.-]+?)(?:\s*-\s*(.*))?$/i
    );
    if (metMatch) {
      return {
        name: metMatch[1]?.trim() || text,
        role: metMatch[2]?.trim() || undefined,
        company: metMatch[3]?.trim() || undefined,
        notes: metMatch[4]?.trim() || undefined,
      };
    }
    const parts = text.split(/[-@,]/);
    return {
      name: parts[0]?.trim() || text,
      company: parts[1]?.trim() || undefined,
      notes: text,
    };
  };

  const handleQuickAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!quickAddInput.trim()) return;

    setIsAdding(true);
    const text = quickAddInput.trim();
    setQuickAddInput('');
    const parsed = parseQuickAdd(text);

    try {
      const created = await createPerson({
        name: parsed.name,
        role: parsed.role,
        company: parsed.company,
        notes: parsed.notes,
        relationship_type: 'contact',
      });
      toast({
        title: 'Contact added',
        description: `${created.name}${created.company ? ` @ ${created.company}` : ''}`,
      });
    } catch (err) {
      toast({ variant: 'destructive', title: 'Add failed', description: formatApiError(err) });
    } finally {
      setIsAdding(false);
    }
  };

  const handleCreateFollowUp = async (person: Person) => {
    try {
      await api.post('/tasks', {
        title: `Follow up with ${person.name}${person.company ? ` (${person.company})` : ''}`,
        priority: 'high',
        person_id: person.id,
        due_date: new Date(Date.now() + 86400000 * 2).toISOString(),
      });
      toast({
        title: 'Follow-up task created',
        description: `Due in 2 days for ${person.name}`,
      });
    } catch (err) {
      toast({ variant: 'destructive', title: 'Task failed', description: formatApiError(err) });
    }
  };

  const filteredPeople = React.useMemo(() => {
    return people.filter((p) => {
      const q = searchQuery.toLowerCase();
      const matchesSearch =
        !q ||
        p.name.toLowerCase().includes(q) ||
        p.company?.toLowerCase().includes(q) ||
        p.role?.toLowerCase().includes(q) ||
        p.notes?.toLowerCase().includes(q);

      const matchesTag =
        selectedTag === 'all' || p.relationship_type.toLowerCase() === selectedTag.toLowerCase();

      return matchesSearch && matchesTag;
    });
  }, [people, searchQuery, selectedTag]);

  return (
    <ResponsivePageContainer>
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-[#251238]/80">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-mono text-[#00ff9d] uppercase tracking-widest font-bold">
              NETWORK
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-mono font-extrabold text-[#f7f4ea] tracking-tight uppercase mt-0.5">
            Relationship CRM
          </h1>
          <p className="text-xs text-muted-foreground font-sans mt-0.5">
            Search, add, and manage your network contacts
          </p>
        </div>

        <Link
          href="/people/new"
          data-testid="person-create"
          className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-[#00ff9d] text-[#0a0510] font-mono text-xs font-bold uppercase hover:bg-[#00e08a] transition-all min-h-[44px]"
        >
          <Plus className="h-4 w-4 stroke-[3]" />
          <span>New Contact</span>
        </Link>
      </div>

      <form onSubmit={handleQuickAdd} className="my-5">
        <div className="relative flex items-center">
          <input
            type="text"
            value={quickAddInput}
            onChange={(e) => setQuickAddInput(e.target.value)}
            placeholder="Quick add: Name, Role @ Company - note"
            className="w-full bg-[#0e0716] border border-[#3b1e5a] focus:border-[#00ff9d] text-sm text-[#f7f4ea] placeholder:text-muted-foreground/60 pl-4 pr-24 py-3.5 rounded-xl outline-none min-h-[44px]"
          />
          <button
            type="submit"
            disabled={!quickAddInput.trim() || isAdding}
            className="absolute right-2 px-4 py-2 rounded-lg bg-[#00ff9d] text-[#0a0510] font-mono text-xs font-bold uppercase hover:bg-[#00e08a] disabled:opacity-30 min-h-[36px]"
          >
            {isAdding ? 'Adding...' : 'Add'}
          </button>
        </div>
      </form>

      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            data-testid="people-search"
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search people, companies, notes..."
            className="w-full bg-[#12081d] border border-[#301642] focus:border-[#00ff9d] text-sm text-[#f7f4ea] pl-10 pr-4 py-2.5 rounded-xl outline-none min-h-[44px]"
          />
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
          {FILTER_TAGS.map((tag) => (
            <button
              key={tag}
              type="button"
              onClick={() => setSelectedTag(tag)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono uppercase whitespace-nowrap min-h-[36px] ${
                selectedTag === tag
                  ? 'bg-[#00ff9d] text-[#0a0510] font-bold'
                  : 'bg-[#12081d] text-muted-foreground border border-[#251238]'
              }`}
            >
              {tag}
            </button>
          ))}
        </div>
      </div>

      {error && <ErrorState error={error} onRetry={refetch} />}

      {loading ? (
        <LoadingState rows={3} showHeader={false} />
      ) : filteredPeople.length === 0 ? (
        <EmptyState
          icon={Users}
          title={people.length === 0 ? 'No contacts yet' : 'No matches'}
          description={
            people.length === 0
              ? 'Add your first contact using the quick bar above or the full form.'
              : 'Try a different search or filter.'
          }
          actionLabel={people.length === 0 ? 'Add Contact' : undefined}
          onAction={people.length === 0 ? () => router.push('/people/new') : undefined}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredPeople.map((person) => (
            <div
              key={person.id}
              data-testid="person-card"
              className="rounded-2xl border border-[#251238] bg-[#0a0510] hover:border-[#00ff9d]/50 p-5 transition-all flex flex-col justify-between gap-4"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center space-x-3">
                    <div className="h-10 w-10 rounded-xl bg-[#251238] border border-[#00ff9d]/30 text-[#00ff9d] font-mono font-bold text-sm flex items-center justify-center">
                      {person.name
                        .split(' ')
                        .map((n) => n[0])
                        .join('')
                        .slice(0, 2)}
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-[#f7f4ea]">{person.name}</h3>
                      <p className="text-xs text-muted-foreground">
                        {person.role || 'Contact'}
                        {person.company ? ` @ ${person.company}` : ''}
                      </p>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-[#251238] text-[#00ff9d]">
                    {person.relationship_type}
                  </span>
                </div>
                {person.notes && (
                  <p className="text-xs text-slate-300 mt-3 bg-[#12081d] p-3 rounded-xl border border-[#251238] line-clamp-3">
                    {person.notes}
                  </p>
                )}
              </div>

              <div className="pt-3 border-t border-[#251238] flex items-center justify-between gap-2">
                <button
                  type="button"
                  onClick={() => handleCreateFollowUp(person)}
                  className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-[#251238] hover:bg-[#3b1e5a] text-[#00ff9d] text-[11px] font-mono min-h-[36px]"
                >
                  <CheckSquare className="h-3 w-3" />
                  Follow-up
                </button>
                <Link
                  href={`/people/${person.id}`}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-[#12081d] border border-[#301642] text-[#f7f4ea] text-[11px] font-mono min-h-[36px]"
                >
                  View
                  <ArrowUpRight className="h-3 w-3 text-[#00ff9d]" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </ResponsivePageContainer>
  );
}

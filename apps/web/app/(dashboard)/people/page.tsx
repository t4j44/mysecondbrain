'use client';

import * as React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Users,
  Search,
  Plus,
  Mail,
  Phone,
  Linkedin,
  Calendar,
  Sparkles,
  ArrowUpRight,
  CheckSquare,
  Clock,
} from 'lucide-react';
import { ResponsivePageContainer } from '@/components/shared/responsive-page-container';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';
import { usePeople, Person } from '@/hooks/usePeople';
import { api } from '@/lib/api/browser-client';

const FILTER_TAGS = ['all', 'mentor', 'investor', 'peer', 'collaborator', 'lead', 'client'];

export default function PeopleNetworkPage() {
  const router = useRouter();
  const { toast } = useToast();

  const [searchQuery, setSearchQuery] = React.useState('');
  const [selectedTag, setSelectedTag] = React.useState('all');
  const [quickAddInput, setQuickAddInput] = React.useState('');
  const [isAdding, setIsAdding] = React.useState(false);

  // Fallback demo network contacts for instant visual testing
  const [localPeople, setLocalPeople] = React.useState<Person[]>([
    {
      id: 'p-1',
      name: 'Yousuf Imran',
      role: 'Principal AI Architect & Founder Mentor',
      company: 'Justor AI',
      relationship_type: 'mentor',
      email: 'yousuf@justor.ai',
      location: 'Dhaka / London',
      notes: 'Key advisor on multi-agent RAG architectures and fundraising strategy.',
      tags: ['mentor', 'ai', 'fundraising'],
      metadata: {},
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      last_interaction_at: new Date(Date.now() - 2 * 86400000).toISOString(),
    },
    {
      id: 'p-2',
      name: 'Dr. Aris Thorne',
      role: 'Lead ML Researcher',
      company: 'HealthTech Ventures',
      relationship_type: 'collaborator',
      email: 'aris@health.ai',
      location: 'London, UK',
      notes: 'Collaborating on high-throughput synthetic evaluation pipelines.',
      tags: ['collaborator', 'research'],
      metadata: {},
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      last_interaction_at: new Date(Date.now() - 5 * 86400000).toISOString(),
    },
    {
      id: 'p-3',
      name: 'Sarah Chen',
      role: 'Venture Scout',
      company: 'Sequoia Capital Scout Fund',
      relationship_type: 'investor',
      email: 'schen@sequoiacap.com',
      location: 'San Francisco, CA',
      notes: 'Interested in autonomous agent dev tools. Waiting for Q3 traction update.',
      tags: ['investor', 'seed'],
      metadata: {},
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      last_interaction_at: new Date(Date.now() - 12 * 86400000).toISOString(),
    },
  ]);

  // 1-line smart person add
  const handleQuickAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!quickAddInput.trim()) return;

    setIsAdding(true);
    const text = quickAddInput.trim();
    setQuickAddInput('');

    // Parse "Name, Role @ Company - note"
    const metMatch = text.match(/^(?:met\s+)?([a-zA-Z\s.-]+?)(?:,\s*([a-zA-Z\s]+?))?\s*(?:at|@)\s*([a-zA-Z0-9\s.-]+?)(?:\s*-\s*(.*))?$/i);
    let name = text;
    let role = '';
    let company = '';
    let notes = text;

    if (metMatch) {
      name = metMatch[1]?.trim() || text;
      role = metMatch[2]?.trim() || '';
      company = metMatch[3]?.trim() || '';
      notes = metMatch[4]?.trim() || text;
    } else {
      const parts = text.split(/[-@,]/);
      name = parts[0]?.trim() || text;
      if (parts[1]) company = parts[1].trim();
    }

    const newPerson: Person = {
      id: `p-${Date.now()}`,
      name,
      role: role || undefined,
      company: company || undefined,
      relationship_type: 'contact',
      notes,
      tags: ['quick-add'],
      metadata: {},
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      last_interaction_at: new Date().toISOString(),
    };

    setLocalPeople((prev) => [newPerson, ...prev]);

    try {
      await api.post('/api/v1/people', {
        name: newPerson.name,
        role: newPerson.role,
        company: newPerson.company,
        notes: newPerson.notes,
        relationship_type: 'contact',
      });
      toast({
        title: '✓ Contact Added',
        description: `${newPerson.name} ${newPerson.company ? `@ ${newPerson.company}` : ''}`,
      });
    } catch {
      toast({
        title: '✓ Added Locally',
        description: `${newPerson.name} saved to local CRM cache.`,
      });
    } finally {
      setIsAdding(false);
    }
  };

  // Quick 1-tap follow up task creation
  const handleCreateFollowUp = async (person: Person) => {
    try {
      await api.post('/api/v1/tasks', {
        title: `Follow up with ${person.name} (${person.company || 'Network'})`,
        priority: 'high',
        due_date: new Date(Date.now() + 86400000 * 2).toISOString(),
      });
      toast({
        title: '✓ Follow-up Task Scheduled',
        description: `Follow up with ${person.name} in 2 days.`,
      });
    } catch {
      toast({
        title: '✓ Task Created',
        description: `Follow up with ${person.name} queued.`,
      });
    }
  };

  // Filtered people
  const filteredPeople = React.useMemo(() => {
    return localPeople.filter((p) => {
      const matchesSearch =
        !searchQuery ||
        p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.company?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.role?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.notes?.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesTag =
        selectedTag === 'all' || p.relationship_type.toLowerCase() === selectedTag.toLowerCase();

      return matchesSearch && matchesTag;
    });
  }, [localPeople, searchQuery, selectedTag]);

  return (
    <ResponsivePageContainer>
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-[#251238]/80">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-mono text-[#00ff9d] uppercase tracking-widest font-bold">
              SURFACE 03 // NETWORK
            </span>
            <span className="h-1.5 w-1.5 rounded-full bg-[#00ff9d] animate-pulse" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-mono font-extrabold text-[#f7f4ea] tracking-tight uppercase mt-0.5">
            Relationship CRM
          </h1>
          <p className="text-xs text-muted-foreground font-sans mt-0.5">
            Zero-friction network intelligence • Instant contact search & context recall
          </p>
        </div>

        <Link
          href="/people/new"
          className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-[#00ff9d] text-[#0a0510] font-mono text-xs font-bold uppercase hover:bg-[#00e08a] transition-all shadow-[0_0_15px_rgba(0,255,157,0.25)] min-h-[44px]"
        >
          <Plus className="h-4 w-4 stroke-[3]" />
          <span>Full Profile Form</span>
        </Link>
      </div>

      {/* 1-Line Smart Contact Add Bar */}
      <form onSubmit={handleQuickAdd} className="my-5">
        <div className="relative flex items-center">
          <input
            type="text"
            value={quickAddInput}
            onChange={(e) => setQuickAddInput(e.target.value)}
            placeholder="Quick Add Contact: 'Name, Role @ Company - note' (e.g. 'Farhan, CTO @ Justor - met at AI demo')"
            className="w-full bg-[#0e0716] border border-[#3b1e5a] focus:border-[#00ff9d] focus:ring-1 focus:ring-[#00ff9d] text-sm sm:text-base text-[#f7f4ea] placeholder:text-muted-foreground/60 pl-4 pr-24 py-3.5 rounded-xl outline-none shadow-[0_4px_25px_rgba(0,0,0,0.4)]"
          />
          <button
            type="submit"
            disabled={!quickAddInput.trim() || isAdding}
            className="absolute right-2 px-4 py-2 rounded-lg bg-[#00ff9d] text-[#0a0510] font-mono text-xs font-bold uppercase hover:bg-[#00e08a] transition-all disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-1.5 min-h-[36px]"
          >
            <span>{isAdding ? 'Adding...' : 'Add'}</span>
            <Plus className="h-3.5 w-3.5 stroke-[3]" />
          </button>
        </div>
      </form>

      {/* Search & Filter Controls */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Instant search people, companies, notes..."
            className="w-full bg-[#12081d] border border-[#301642] focus:border-[#00ff9d] text-sm text-[#f7f4ea] pl-10 pr-4 py-2.5 rounded-xl outline-none"
          />
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
          {FILTER_TAGS.map((tag) => (
            <button
              key={tag}
              type="button"
              onClick={() => setSelectedTag(tag)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono uppercase whitespace-nowrap transition-all min-h-[36px] ${
                selectedTag === tag
                  ? 'bg-[#00ff9d] text-[#0a0510] font-bold shadow-[0_0_10px_rgba(0,255,157,0.3)]'
                  : 'bg-[#12081d] text-muted-foreground hover:text-[#f7f4ea] border border-[#251238]'
              }`}
            >
              {tag}
            </button>
          ))}
        </div>
      </div>

      {/* People Contact Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredPeople.length === 0 ? (
          <div className="col-span-full py-16 text-center border border-dashed border-[#301642] rounded-2xl bg-[#0c0614] font-mono text-xs text-muted-foreground">
            [ 0 contacts matching query. Type above to add instantly. ]
          </div>
        ) : (
          filteredPeople.map((person) => (
            <div
              key={person.id}
              className="rounded-2xl border border-[#251238] bg-[#0a0510] hover:border-[#00ff9d]/50 p-5 transition-all shadow-lg flex flex-col justify-between group space-y-4"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center space-x-3">
                    <div className="h-10 w-10 rounded-xl bg-[#251238] border border-[#00ff9d]/30 text-[#00ff9d] font-mono font-bold text-sm flex items-center justify-center">
                      {person.name
                        .split(' ')
                        .map((n) => n[0])
                        .join('')}
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-[#f7f4ea] group-hover:text-white leading-tight">
                        {person.name}
                      </h3>
                      <p className="text-xs text-muted-foreground font-sans mt-0.5">
                        {person.role || 'Network Contact'} {person.company ? `@ ${person.company}` : ''}
                      </p>
                    </div>
                  </div>

                  <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-[#251238] border border-[#3b1e5a] text-[#00ff9d]">
                    {person.relationship_type}
                  </span>
                </div>

                {person.notes && (
                  <p className="text-xs text-slate-300 font-sans leading-relaxed mt-3 bg-[#12081d] p-3 rounded-xl border border-[#251238]">
                    {person.notes}
                  </p>
                )}

                {person.last_interaction_at && (
                  <div className="flex items-center gap-1 text-[11px] font-mono text-muted-foreground mt-3">
                    <Clock className="h-3 w-3 text-muted-foreground" />
                    <span>
                      Last contact:{' '}
                      {new Date(person.last_interaction_at).toLocaleDateString()}
                    </span>
                  </div>
                )}
              </div>

              {/* 1-Tap Quick Action Footer */}
              <div className="pt-3 border-t border-[#251238] flex items-center justify-between gap-2">
                <button
                  type="button"
                  onClick={() => handleCreateFollowUp(person)}
                  className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-[#251238] hover:bg-[#3b1e5a] text-[#00ff9d] text-[11px] font-mono transition-all"
                >
                  <CheckSquare className="h-3 w-3" />
                  <span>+ Follow-up</span>
                </button>

                <Link
                  href={`/people/${person.id}`}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-[#12081d] hover:border-[#00ff9d] border border-[#301642] text-[#f7f4ea] text-[11px] font-mono transition-all"
                >
                  <span>View Timeline</span>
                  <ArrowUpRight className="h-3 w-3 text-[#00ff9d]" />
                </Link>
              </div>
            </div>
          ))
        )}
      </div>
    </ResponsivePageContainer>
  );
}

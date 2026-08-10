'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Briefcase, Plus, Search, FolderGit2, CheckSquare } from 'lucide-react';
import LayoutShell from '../../components/layout/Sidebar';
import { Card, Button, StatusBadge } from '../../components/ui/CustomUi';
import { mockApi } from '../../lib/mockApi';
import { Venture } from '../../types/execution';

export default function VenturesPage() {
  const [loading, setLoading] = useState(true);
  const [ventures, setVentures] = useState<Venture[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'paused' | 'exited' | 'archived'>('active');

  const loadVentures = async () => {
    setLoading(true);
    try {
      // Fetch including archived to let filters handle it
      const data = await mockApi.getVentures(true);
      setVentures(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVentures();
    window.addEventListener('second-brain-data-updated', loadVentures);
    return () => window.removeEventListener('second-brain-data-updated', loadVentures);
  }, []);

  const filteredVentures = ventures.filter(v => {
    const matchesSearch = v.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
      v.slug.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (v.mission && v.mission.toLowerCase().includes(searchQuery.toLowerCase()));
      
    const matchesStatus = statusFilter === 'all' || v.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  return (
    <LayoutShell>
      <div className="space-y-6">
        {/* Header Section */}
        <div className="flex flex-col sm:flex-row justify-between sm:items-center p-5 bg-terminal-panel border border-terminal-border rounded-xl gap-4">
          <div className="space-y-1">
            <span className="text-[10px] uppercase font-mono tracking-wider text-terminal-accent font-semibold flex items-center gap-1">
              <Briefcase size={12} /> Venture Portfolio
            </span>
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white font-mono uppercase">
              Initiatives & Ventures
            </h1>
            <p className="text-xs text-terminal-muted">
              Define the master initiatives and guiding missions scaling across the Second Brain.
            </p>
          </div>
          <Link href="/ventures/new">
            <Button variant="primary" className="flex items-center gap-1.5 self-start sm:self-auto">
              <Plus size={16} />
              <span className="font-mono text-xs">CREATE VENTURE</span>
            </Button>
          </Link>
        </div>

        {/* Filter Toolbar */}
        <div className="flex flex-col md:flex-row gap-4 justify-between bg-terminal-panel/40 p-4 border border-terminal-border rounded-xl">
          {/* Search bar */}
          <div className="flex items-center bg-terminal-panel border border-terminal-border rounded-lg px-3 py-2 w-full md:max-w-xs font-mono text-xs">
            <Search className="text-terminal-muted mr-2 w-4 h-4 flex-shrink-0" />
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="Search ventures by keyword..."
              className="bg-transparent text-terminal-fg placeholder-terminal-muted outline-none border-none w-full"
            />
          </div>

          {/* Status Tabs */}
          <div className="flex overflow-x-auto gap-1 bg-slate-950/40 p-1 rounded-lg border border-terminal-border self-start font-mono text-xs">
            {(['all', 'active', 'paused', 'exited', 'archived'] as const).map(status => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={`px-3 py-1.5 rounded transition-all capitalize ${
                  statusFilter === status
                    ? 'bg-terminal-accent text-terminal-panel font-semibold shadow-md shadow-terminal-accent/10'
                    : 'text-terminal-muted hover:text-terminal-fg hover:bg-white/5'
                }`}
              >
                {status}
              </button>
            ))}
          </div>
        </div>

        {/* Grid Stream */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-pulse">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-44 bg-terminal-panel border border-terminal-border rounded-xl" />
            ))}
          </div>
        ) : filteredVentures.length === 0 ? (
          <div className="py-16 text-center border border-terminal-border border-dashed rounded-xl">
            <Briefcase className="w-10 h-10 text-terminal-muted mx-auto mb-3" />
            <p className="text-sm text-terminal-muted font-mono">
              {searchQuery 
                ? 'No ventures match your filter criteria.'
                : 'Create your first venture to define a mission and organize related projects.'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {filteredVentures.map(venture => (
              <Card 
                key={venture.id}
                className="flex flex-col justify-between space-y-4 hover:border-terminal-accent/30 group"
                header={
                  <div className="flex items-center justify-between w-full">
                    <Link href={`/ventures/${venture.id}`}>
                      <h3 className="font-mono font-bold text-sm text-white group-hover:text-terminal-accent transition-colors cursor-pointer truncate max-w-[180px]">
                        {venture.name}
                      </h3>
                    </Link>
                    <StatusBadge status={venture.status} />
                  </div>
                }
              >
                <div className="space-y-2">
                  {venture.vision && (
                    <div className="text-[11px] font-mono text-terminal-muted">
                      <span className="text-terminal-accent">Vision:</span> {venture.vision}
                    </div>
                  )}
                  {venture.mission && (
                    <p className="text-xs text-terminal-fg leading-relaxed font-sans mt-1 line-clamp-2">
                      {venture.mission}
                    </p>
                  )}
                </div>

                <div className="flex items-center justify-between pt-3 border-t border-terminal-border/10 text-xs font-mono text-terminal-muted">
                  <div className="flex gap-4">
                    <span className="flex items-center gap-1">
                      <FolderGit2 size={13} /> {venture.project_count || 0} Projects
                    </span>
                    <span className="flex items-center gap-1">
                      <CheckSquare size={13} /> {venture.open_task_count || 0} Tasks
                    </span>
                  </div>
                  <Link href={`/ventures/${venture.id}`} className="text-terminal-accent hover:underline text-[10px]">
                    Workspace &rarr;
                  </Link>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </LayoutShell>
  );
}

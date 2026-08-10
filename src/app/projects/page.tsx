'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { FolderGit2, Plus, Search, Calendar, Briefcase, BarChart } from 'lucide-react';
import LayoutShell from '../../components/layout/Sidebar';
import { Card, Button, StatusBadge } from '../../components/ui/CustomUi';
import { mockApi } from '../../lib/mockApi';
import { Project } from '../../types/execution';

export default function ProjectsPage() {
  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState<Array<Project & { venture_name?: string; open_task_count?: number; blocked_task_count?: number }>>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'planning' | 'in_progress' | 'completed' | 'on_hold' | 'archived'>('in_progress');

  const loadProjects = async () => {
    setLoading(true);
    try {
      const data = await mockApi.getProjects(true); // Fetch including archived
      setProjects(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
    window.addEventListener('second-brain-data-updated', loadProjects);
    return () => window.removeEventListener('second-brain-data-updated', loadProjects);
  }, []);

  const filteredProjects = projects.filter(p => {
    const matchesSearch = p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (p.description && p.description.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (p.venture_name && p.venture_name.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesStatus = statusFilter === 'all' || p.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  return (
    <LayoutShell>
      <div className="space-y-6">
        {/* Header Section */}
        <div className="flex flex-col sm:flex-row justify-between sm:items-center p-5 bg-terminal-panel border border-terminal-border rounded-xl gap-4">
          <div className="space-y-1">
            <span className="text-[10px] uppercase font-mono tracking-wider text-terminal-accent font-semibold flex items-center gap-1">
              <FolderGit2 size={12} /> Execution Pipeline
            </span>
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white font-mono uppercase">
              Project Milestones
            </h1>
            <p className="text-xs text-terminal-muted">
              Track project progression grids, target execution deadlines, and task completeness rates.
            </p>
          </div>
          <Link href="/projects/new">
            <Button variant="primary" className="flex items-center gap-1.5 self-start sm:self-auto">
              <Plus size={16} />
              <span className="font-mono text-xs">CREATE PROJECT</span>
            </Button>
          </Link>
        </div>

        {/* Filters Panel */}
        <div className="flex flex-col md:flex-row gap-4 justify-between bg-terminal-panel/40 p-4 border border-terminal-border rounded-xl">
          {/* Search bar */}
          <div className="flex items-center bg-terminal-panel border border-terminal-border rounded-lg px-3 py-2 w-full md:max-w-xs font-mono text-xs">
            <Search className="text-terminal-muted mr-2 w-4 h-4 flex-shrink-0" />
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="Search projects..."
              className="bg-transparent text-terminal-fg placeholder-terminal-muted outline-none border-none w-full"
            />
          </div>

          {/* Status Tabs */}
          <div className="flex overflow-x-auto gap-1 bg-slate-950/40 p-1 rounded-lg border border-terminal-border self-start font-mono text-xs">
            {(['all', 'planning', 'in_progress', 'completed', 'on_hold', 'archived'] as const).map(status => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={`px-3 py-1.5 rounded transition-all capitalize whitespace-nowrap ${
                  statusFilter === status
                    ? 'bg-terminal-accent text-terminal-panel font-semibold shadow-md shadow-terminal-accent/10'
                    : 'text-terminal-muted hover:text-terminal-fg hover:bg-white/5'
                }`}
              >
                {status === 'in_progress' ? 'active' : status}
              </button>
            ))}
          </div>
        </div>

        {/* Projects Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-pulse">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-48 bg-terminal-panel border border-terminal-border rounded-xl" />
            ))}
          </div>
        ) : filteredProjects.length === 0 ? (
          <div className="py-16 text-center border border-terminal-border border-dashed rounded-xl">
            <FolderGit2 className="w-10 h-10 text-terminal-muted mx-auto mb-3" />
            <p className="text-sm text-terminal-muted font-mono">
              {searchQuery 
                ? 'No projects match your filter criteria.'
                : 'Create a project to turn a venture goal into structured execution.'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProjects.map(project => {
              const isCompleted = project.status === 'completed';
              return (
                <Card 
                  key={project.id}
                  className="flex flex-col justify-between space-y-4 hover:border-terminal-accent/30 group"
                  header={
                    <div className="flex items-center justify-between w-full">
                      <Link href={`/projects/${project.id}`}>
                        <h3 className="font-mono font-bold text-xs text-white group-hover:text-terminal-accent transition-colors cursor-pointer truncate max-w-[160px]">
                          {project.name}
                        </h3>
                      </Link>
                      <StatusBadge status={project.status} />
                    </div>
                  }
                >
                  <div className="space-y-2.5">
                    {/* Linked Venture name */}
                    <div className="flex items-center gap-1 text-[10px] font-mono text-terminal-muted">
                      <Briefcase size={12} />
                      Venture: <span className="text-terminal-fg">{project.venture_name}</span>
                    </div>

                    {project.description && (
                      <p className="text-xs text-terminal-fg leading-relaxed line-clamp-2 font-sans">
                        {project.description}
                      </p>
                    )}

                    {/* Progress tracking */}
                    <div className="space-y-1 pt-1">
                      <div className="flex justify-between text-[10px] font-mono">
                        <span className="text-terminal-muted">Progress</span>
                        <span className="text-terminal-accent font-bold">{project.progress}%</span>
                      </div>
                      <div className="w-full bg-slate-950/60 h-1.5 rounded-full overflow-hidden border border-terminal-border">
                        <div 
                          className={`h-full rounded-full transition-all duration-500 ${isCompleted ? 'bg-terminal-accent' : 'bg-purple-500'}`} 
                          style={{ width: `${project.progress}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-3 border-t border-terminal-border/10 text-[10px] font-mono text-terminal-muted">
                    <div className="flex gap-3">
                      {project.target_date && (
                        <span className="flex items-center gap-1">
                          <Calendar size={12} /> {project.target_date}
                        </span>
                      )}
                      <span>{project.open_task_count || 0} Tasks Left</span>
                    </div>
                    <Link href={`/projects/${project.id}`} className="text-terminal-accent hover:underline text-[9px]">
                      Workspace &rarr;
                    </Link>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </LayoutShell>
  );
}

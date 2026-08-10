'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter, useParams } from 'next/navigation';
import { Briefcase, ArrowLeft, Edit2, Archive, FolderGit2, CheckSquare, Target, Settings } from 'lucide-react';
import LayoutShell from '../../../components/layout/Sidebar';
import { Card, Button, StatusBadge, PriorityBadge } from '../../../components/ui/CustomUi';
import { mockApi } from '../../../lib/mockApi';
import { Venture, Project, Task } from '../../../types/execution';

export default function VentureDetailPage() {
  const router = useRouter();
  const params = useParams();
  const ventureId = params.ventureId as string;

  const [loading, setLoading] = useState(true);
  const [venture, setVenture] = useState<Venture | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [error, setError] = useState<string | null>(null);

  const loadVentureData = async () => {
    setLoading(true);
    try {
      const data = await mockApi.getVentureById(ventureId);
      setVenture(data);
      setProjects(data.projects);
      setTasks(data.tasks);
    } catch (e: any) {
      setError(e.message || 'Venture not found');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVentureData();
    window.addEventListener('second-brain-data-updated', loadVentureData);
    return () => window.removeEventListener('second-brain-data-updated', loadVentureData);
  }, [ventureId]);

  const handleArchive = async () => {
    if (!venture) return;
    if (!confirm(`Are you sure you want to archive ${venture.name}? This will also archive all linked projects and tasks.`)) return;

    try {
      await mockApi.archiveVenture(venture.id);
      window.dispatchEvent(new Event('second-brain-data-updated'));
      router.push('/ventures');
    } catch (e) {
      console.error(e);
    }
  };

  if (error) {
    return (
      <LayoutShell>
        <div className="py-16 text-center border border-terminal-border rounded-xl max-w-xl mx-auto space-y-4">
          <Briefcase className="w-12 h-12 text-terminal-alert mx-auto animate-pulse" />
          <h2 className="text-lg font-bold font-mono text-white">RECORD NOT FOUND</h2>
          <p className="text-xs text-terminal-muted">{error}</p>
          <Link href="/ventures">
            <Button size="sm">Back to Ventures</Button>
          </Link>
        </div>
      </LayoutShell>
    );
  }

  return (
    <LayoutShell>
      {loading ? (
        <div className="space-y-6 animate-pulse">
          <div className="h-20 bg-terminal-panel border border-terminal-border rounded-xl" />
          <div className="h-44 bg-terminal-panel border border-terminal-border rounded-xl" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="h-64 bg-terminal-panel border border-terminal-border rounded-xl" />
            <div className="h-64 bg-terminal-panel border border-terminal-border rounded-xl" />
          </div>
        </div>
      ) : venture ? (
        <div className="space-y-6">
          {/* Header Action Bar */}
          <div className="flex flex-col sm:flex-row justify-between sm:items-center p-5 bg-terminal-panel border border-terminal-border rounded-xl gap-4">
            <div className="space-y-1">
              <Link href="/ventures" className="inline-flex items-center gap-1 text-xs text-terminal-muted hover:text-terminal-accent font-mono transition-colors">
                <ArrowLeft size={12} /> BACK TO VENTURES
              </Link>
              <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white font-mono uppercase mt-1">
                {venture.name} Workspace
              </h1>
              <p className="text-[10px] text-terminal-muted font-mono">
                SLUG: <span className="text-terminal-fg">{venture.slug}</span> | CREATED: {new Date(venture.created_at).toLocaleDateString()}
              </p>
            </div>
            
            <div className="flex gap-2 self-start sm:self-auto">
              <Link href={`/ventures/${venture.id}/edit`}>
                <Button size="sm" className="flex items-center gap-1.5">
                  <Edit2 size={13} />
                  <span className="font-mono text-xs">EDIT</span>
                </Button>
              </Link>
              <Button size="sm" variant="destructive" onClick={handleArchive} className="flex items-center gap-1.5">
                <Archive size={13} />
                <span className="font-mono text-xs">ARCHIVE</span>
              </Button>
            </div>
          </div>

          {/* Vision & Mission Core */}
          <Card 
            header={
              <div className="flex items-center gap-2">
                <Target size={14} className="text-terminal-accent" />
                <span className="font-mono text-xs font-bold text-white uppercase tracking-wider">Mission Statement</span>
              </div>
            }
          >
            <div className="space-y-4 font-sans text-sm">
              {venture.vision && (
                <div className="p-3 bg-terminal-panel/50 border border-terminal-border rounded-lg">
                  <span className="font-mono text-[10px] text-terminal-accent uppercase tracking-wider block mb-1">Venture Vision</span>
                  <p className="text-terminal-fg italic">"{venture.vision}"</p>
                </div>
              )}
              {venture.mission ? (
                <div className="space-y-1">
                  <span className="font-mono text-[10px] text-terminal-muted uppercase tracking-wider block">Operational Mission</span>
                  <p className="text-terminal-fg leading-relaxed whitespace-pre-wrap">{venture.mission}</p>
                </div>
              ) : (
                <p className="text-terminal-muted italic text-xs">No mission defined. Click edit to set the guidance parameters.</p>
              )}
            </div>
          </Card>

          {/* Grid: Projects and Tasks */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Projects List Card */}
            <Card
              header={
                <div className="flex items-center justify-between w-full">
                  <div className="flex items-center gap-2">
                    <FolderGit2 size={14} className="text-terminal-accent" />
                    <span className="font-mono text-xs font-bold text-white uppercase tracking-wider">Linked Projects ({projects.length})</span>
                  </div>
                  <Link href={`/projects/new?ventureId=${venture.id}`}>
                    <Button size="sm" className="px-2.5 py-1 text-[10px] font-mono">
                      + ADD PROJECT
                    </Button>
                  </Link>
                </div>
              }
            >
              {projects.length === 0 ? (
                <p className="text-xs text-terminal-muted italic py-6 text-center font-mono">No active projects linked.</p>
              ) : (
                <div className="space-y-3">
                  {projects.map(proj => (
                    <Link
                      key={proj.id}
                      href={`/projects/${proj.id}`}
                      className="block p-3 rounded-lg border border-terminal-border bg-terminal-panel/20 hover:border-terminal-accent/30 transition-all space-y-2 group"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold text-white group-hover:text-terminal-accent transition-colors">
                          {proj.name}
                        </span>
                        <StatusBadge status={proj.status} />
                      </div>
                      <div className="space-y-1">
                        <div className="flex justify-between text-[10px] font-mono text-terminal-muted">
                          <span>Progress</span>
                          <span>{proj.progress}%</span>
                        </div>
                        <div className="w-full bg-terminal-panel h-1.5 rounded-full overflow-hidden border border-terminal-border">
                          <div className="bg-purple-500 h-full rounded-full" style={{ width: `${proj.progress}%` }} />
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </Card>

            {/* Tasks List Card */}
            <Card
              header={
                <div className="flex items-center justify-between w-full">
                  <div className="flex items-center gap-2">
                    <CheckSquare size={14} className="text-terminal-accent" />
                    <span className="font-mono text-xs font-bold text-white uppercase tracking-wider">Active Tasks ({tasks.filter(t => t.status !== 'done').length})</span>
                  </div>
                  <Link href={`/tasks`}>
                    <Button size="sm" className="px-2.5 py-1 text-[10px] font-mono">
                      GO TO BOARD
                    </Button>
                  </Link>
                </div>
              }
            >
              {tasks.length === 0 ? (
                <p className="text-xs text-terminal-muted italic py-6 text-center font-mono">No tasks found.</p>
              ) : (
                <div className="space-y-2.5">
                  {tasks.map(task => (
                    <div 
                      key={task.id}
                      className="p-3 rounded-lg border border-terminal-border/60 bg-terminal-panel/10 flex items-center justify-between gap-3 text-xs"
                    >
                      <div className="min-w-0">
                        <p className={`font-medium truncate ${task.status === 'done' ? 'line-through text-terminal-muted' : 'text-terminal-fg'}`}>
                          {task.title}
                        </p>
                        {task.due_date && (
                          <span className="text-[9px] text-terminal-muted font-mono block mt-0.5">
                            Due: {new Date(task.due_date).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <PriorityBadge priority={task.priority} />
                        <StatusBadge status={task.status} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        </div>
      ) : null}
    </LayoutShell>
  );
}

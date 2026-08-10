'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter, useParams } from 'next/navigation';
import { FolderGit2, ArrowLeft, Edit2, Archive, Calendar, CheckSquare, Square, Plus } from 'lucide-react';
import LayoutShell from '../../../components/layout/Sidebar';
import { Card, Button, StatusBadge, PriorityBadge } from '../../../components/ui/CustomUi';
import { mockApi } from '../../../lib/mockApi';
import { Project, Task } from '../../../types/execution';

export default function ProjectDetailPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = params.projectId as string;

  const [loading, setLoading] = useState(true);
  const [project, setProject] = useState<Project | null>(null);
  const [ventureName, setVentureName] = useState('Independent');
  const [tasks, setTasks] = useState<Task[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [updatingTaskId, setUpdatingTaskId] = useState<string | null>(null);

  const loadProjectData = async () => {
    setLoading(true);
    try {
      const data = await mockApi.getProjectById(projectId);
      setProject(data);
      setVentureName(data.venture_name);
      setTasks(data.tasks);
    } catch (e: any) {
      setError(e.message || 'Project not found');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjectData();
    window.addEventListener('second-brain-data-updated', loadProjectData);
    return () => window.removeEventListener('second-brain-data-updated', loadProjectData);
  }, [projectId]);

  const handleArchive = async () => {
    if (!project) return;
    if (!confirm(`Are you sure you want to archive ${project.name}? This will also archive all linked tasks.`)) return;

    try {
      await mockApi.archiveProject(project.id);
      window.dispatchEvent(new Event('second-brain-data-updated'));
      router.push('/projects');
    } catch (e) {
      console.error(e);
    }
  };

  const handleToggleTask = async (task: Task) => {
    setUpdatingTaskId(task.id);
    const newStatus = task.status === 'done' ? 'todo' : 'done';
    
    // Optimistic UI updates
    const prevStatus = task.status;
    task.status = newStatus;
    
    try {
      await mockApi.updateTaskStatus(task.id, newStatus);
      // Reload project details to show updated progress percentage!
      const data = await mockApi.getProjectById(projectId);
      setProject(data);
      setTasks(data.tasks);
    } catch (err) {
      console.error(err);
      task.status = prevStatus; // Rollback
    } finally {
      setUpdatingTaskId(null);
    }
  };

  if (error) {
    return (
      <LayoutShell>
        <div className="py-16 text-center border border-terminal-border rounded-xl max-w-xl mx-auto space-y-4">
          <FolderGit2 className="w-12 h-12 text-terminal-alert mx-auto animate-pulse" />
          <h2 className="text-lg font-bold font-mono text-white">RECORD NOT FOUND</h2>
          <p className="text-xs text-terminal-muted">{error}</p>
          <Link href="/projects">
            <Button size="sm">Back to Projects</Button>
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
          <div className="h-64 bg-terminal-panel border border-terminal-border rounded-xl" />
        </div>
      ) : project ? (
        <div className="space-y-6">
          {/* Header Action Bar */}
          <div className="flex flex-col sm:flex-row justify-between sm:items-center p-5 bg-terminal-panel border border-terminal-border rounded-xl gap-4">
            <div className="space-y-1">
              <Link href="/projects" className="inline-flex items-center gap-1 text-xs text-terminal-muted hover:text-terminal-accent font-mono transition-colors">
                <ArrowLeft size={12} /> BACK TO PROJECTS
              </Link>
              <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white font-mono uppercase mt-1">
                {project.name} Workspace
              </h1>
              <p className="text-[10px] text-terminal-muted font-mono">
                Venture: <span className="text-terminal-fg">{ventureName}</span> | Target Date: {project.target_date || 'None'}
              </p>
            </div>
            
            <div className="flex gap-2 self-start sm:self-auto">
              <Link href={`/projects/${project.id}/edit`}>
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

          {/* Details & Progress Card */}
          <Card
            header={
              <div className="flex items-center justify-between w-full">
                <span className="font-mono text-xs font-bold text-white uppercase tracking-wider">Project Specification</span>
                <StatusBadge status={project.status} />
              </div>
            }
          >
            <div className="space-y-4">
              {project.description && (
                <p className="text-sm text-terminal-fg leading-relaxed font-sans">{project.description}</p>
              )}

              {/* Progress bar */}
              <div className="space-y-1.5 pt-2 border-t border-terminal-border/10">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-terminal-muted">Completeness Metrics</span>
                  <span className="text-terminal-accent font-bold">{project.progress}%</span>
                </div>
                <div className="w-full bg-terminal-panel h-2 rounded-full overflow-hidden border border-terminal-border">
                  <div className="bg-terminal-accent h-full rounded-full transition-all duration-500" style={{ width: `${project.progress}%` }} />
                </div>
              </div>
            </div>
          </Card>

          {/* Tasks Checklist Card */}
          <Card
            header={
              <div className="flex items-center justify-between w-full">
                <div className="flex items-center gap-2">
                  <CheckSquare size={14} className="text-terminal-accent" />
                  <span className="font-mono text-xs font-bold text-white uppercase tracking-wider">Action Items Checklist</span>
                </div>
                <Button 
                  size="sm" 
                  className="px-2.5 py-1 text-[10px] font-mono flex items-center gap-1"
                  onClick={() => {
                    window.dispatchEvent(new CustomEvent('open-quick-create', { detail: { tab: 'task' } }));
                  }}
                >
                  <Plus size={12} /> ADD TASK
                </Button>
              </div>
            }
          >
            {tasks.length === 0 ? (
              <div className="py-8 text-center text-terminal-muted text-xs italic font-mono">
                No tasks are currently linked to this project workspace.
              </div>
            ) : (
              <div className="space-y-2.5">
                {tasks.map(task => {
                  const isDone = task.status === 'done';
                  const isUpdating = updatingTaskId === task.id;
                  return (
                    <div
                      key={task.id}
                      className={`p-3.5 rounded-lg border border-terminal-border/60 bg-terminal-panel/30 hover:border-terminal-accent/25 transition-all flex items-center justify-between gap-3 ${
                        isUpdating ? 'opacity-50 pointer-events-none' : ''
                      }`}
                    >
                      <div className="flex items-start gap-2.5 min-w-0">
                        {/* Checkbox button */}
                        <button
                          onClick={() => handleToggleTask(task)}
                          className="mt-0.5 text-terminal-muted hover:text-terminal-accent transition-colors flex-shrink-0"
                        >
                          {isDone ? (
                            <CheckSquare size={16} className="text-terminal-accent" />
                          ) : (
                            <Square size={16} />
                          )}
                        </button>
                        <div className="min-w-0">
                          <p className={`text-xs font-medium ${isDone ? 'line-through text-terminal-muted' : 'text-terminal-fg'}`}>
                            {task.title}
                          </p>
                          {task.due_date && (
                            <span className="text-[9px] text-terminal-muted font-mono block mt-0.5">
                              Due: {new Date(task.due_date).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <PriorityBadge priority={task.priority} />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>
        </div>
      ) : null}
    </LayoutShell>
  );
}

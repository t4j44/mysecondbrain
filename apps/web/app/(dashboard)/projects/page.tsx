'use client';

import * as React from 'react';
import { FolderKanban, Pencil, Trash2, X, Check } from 'lucide-react';
import { ResponsivePageContainer } from '@/components/shared/responsive-page-container';
import { PageHeader } from '@/components/shared/page-header';
import { EmptyState } from '@/components/shared/empty-state';
import { LoadingState } from '@/components/shared/loading-state';
import { ErrorState } from '@/components/shared/error-state';
import { ConfirmActionDialog } from '@/components/shared/confirm-action-dialog';
import { StatusBadge } from '@/components/shared/status-badge';
import { PriorityBadge } from '@/components/shared/priority-badge';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';
import { useProjects } from '@/hooks/useProjects';
import { useVentures } from '@/hooks/useVentures';
import { formatApiError } from '@/lib/api/format-error';
import type { Project } from '@/lib/api/domains';

export default function ProjectsPage() {
  const { toast } = useToast();
  const { ventures } = useVentures();
  const [ventureFilter, setVentureFilter] = React.useState('');
  const { projects, loading, error, refetch, createProject, updateProject, deleteProject } =
    useProjects({ ventureId: ventureFilter || undefined });

  const [showCreate, setShowCreate] = React.useState(false);
  const [createName, setCreateName] = React.useState('');
  const [createVentureId, setCreateVentureId] = React.useState('');
  const [createDescription, setCreateDescription] = React.useState('');
  const [creating, setCreating] = React.useState(false);

  const [editingId, setEditingId] = React.useState<string | null>(null);
  const [editName, setEditName] = React.useState('');
  const [editDescription, setEditDescription] = React.useState('');
  const [editStatus, setEditStatus] = React.useState('in_progress');
  const [saving, setSaving] = React.useState(false);

  const [deleteTarget, setDeleteTarget] = React.useState<Project | null>(null);

  const ventureName = (id?: string | null) =>
    ventures.find((v) => v.id === id)?.name ?? 'Unassigned';

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createName.trim()) return;
    setCreating(true);
    try {
      await createProject({
        name: createName.trim(),
        venture_id: createVentureId || undefined,
        description: createDescription.trim() || undefined,
      });
      setCreateName('');
      setCreateDescription('');
      setCreateVentureId('');
      setShowCreate(false);
      toast({ title: 'Project created', description: createName.trim() });
    } catch (err) {
      toast({ variant: 'destructive', title: 'Create failed', description: formatApiError(err) });
    } finally {
      setCreating(false);
    }
  };

  const startEdit = (project: Project) => {
    setEditingId(project.id);
    setEditName(project.name);
    setEditDescription(project.description ?? '');
    setEditStatus(project.status);
  };

  const handleSaveEdit = async (id: string) => {
    if (!editName.trim()) return;
    setSaving(true);
    try {
      await updateProject(id, {
        name: editName.trim(),
        description: editDescription.trim() || undefined,
        status: editStatus,
      });
      setEditingId(null);
      toast({ title: 'Project updated' });
    } catch (err) {
      toast({ variant: 'destructive', title: 'Update failed', description: formatApiError(err) });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteProject(deleteTarget.id);
      toast({ title: 'Project archived', description: deleteTarget.name });
    } catch (err) {
      toast({ variant: 'destructive', title: 'Delete failed', description: formatApiError(err) });
      throw err;
    }
  };

  return (
    <ResponsivePageContainer>
      <PageHeader
        title="Project Portfolio"
        description="Operational milestones nested under ventures."
        badge="PROJECTS"
        actions={
          <Button
            data-testid="project-create"
            onClick={() => setShowCreate((v) => !v)}
            className="font-mono text-xs min-h-[44px]"
          >
            {showCreate ? 'Cancel' : '+ New Project'}
          </Button>
        }
      />

      <div className="flex flex-wrap items-center gap-3 mb-4">
        <label className="text-xs font-mono text-muted-foreground uppercase">Filter by venture:</label>
        <select
          value={ventureFilter}
          onChange={(e) => setVentureFilter(e.target.value)}
          className="bg-[#0a0510] border border-[#301642] text-xs font-mono text-[#f7f4ea] px-3 py-2 rounded-lg min-h-[44px]"
        >
          <option value="">All ventures</option>
          {ventures.map((v) => (
            <option key={v.id} value={v.id}>
              {v.name}
            </option>
          ))}
        </select>
      </div>

      {error && <ErrorState error={error} onRetry={refetch} />}

      {showCreate && (
        <form
          onSubmit={handleCreate}
          className="mb-6 rounded-xl border border-[#3b1e5a] bg-[#0e0716] p-4 space-y-3"
        >
          <input
            type="text"
            value={createName}
            onChange={(e) => setCreateName(e.target.value)}
            placeholder="Project name *"
            required
            className="w-full bg-[#0a0510] border border-[#301642] focus:border-[#00ff9d] text-sm text-[#f7f4ea] px-3 py-2.5 rounded-lg outline-none"
            autoFocus
          />
          <select
            value={createVentureId}
            onChange={(e) => setCreateVentureId(e.target.value)}
            className="w-full bg-[#0a0510] border border-[#301642] text-xs font-mono text-[#f7f4ea] px-3 py-2.5 rounded-lg min-h-[44px]"
          >
            <option value="">No venture (optional)</option>
            {ventures.map((v) => (
              <option key={v.id} value={v.id}>
                {v.name}
              </option>
            ))}
          </select>
          <textarea
            value={createDescription}
            onChange={(e) => setCreateDescription(e.target.value)}
            placeholder="Description (optional)"
            rows={2}
            className="w-full bg-[#0a0510] border border-[#301642] focus:border-[#00ff9d] text-sm text-[#f7f4ea] px-3 py-2.5 rounded-lg outline-none resize-none"
          />
          <Button type="submit" disabled={creating || !createName.trim()} className="font-mono text-xs">
            {creating ? 'Creating...' : 'Create Project'}
          </Button>
        </form>
      )}

      {loading ? (
        <LoadingState rows={3} showHeader={false} />
      ) : projects.length === 0 ? (
        <EmptyState
          icon={FolderKanban}
          title="No projects yet"
          description="Create a project under a venture to track milestones."
          actionLabel="Create Project"
          onAction={() => setShowCreate(true)}
        />
      ) : (
        <div data-testid="project-list" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((project) => (
            <div
              key={project.id}
              data-testid="project-card"
              className="rounded-xl border border-[#251238] bg-[#0a0510] p-4 space-y-3 hover:border-[#00ff9d]/40 transition-colors"
            >
              {editingId === project.id ? (
                <div className="space-y-2">
                  <input
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    className="w-full bg-[#12081d] border border-[#301642] text-sm text-[#f7f4ea] px-3 py-2 rounded-lg outline-none"
                  />
                  <textarea
                    value={editDescription}
                    onChange={(e) => setEditDescription(e.target.value)}
                    rows={2}
                    className="w-full bg-[#12081d] border border-[#301642] text-sm text-[#f7f4ea] px-3 py-2 rounded-lg outline-none resize-none"
                  />
                  <select
                    value={editStatus}
                    onChange={(e) => setEditStatus(e.target.value)}
                    className="w-full bg-[#12081d] border border-[#301642] text-xs font-mono text-[#f7f4ea] px-2 py-1.5 rounded-lg"
                  >
                    <option value="planned">Planned</option>
                    <option value="in_progress">In Progress</option>
                    <option value="paused">Paused</option>
                    <option value="completed">Completed</option>
                  </select>
                  <div className="flex gap-2">
                    <Button size="sm" onClick={() => handleSaveEdit(project.id)} disabled={saving} className="font-mono text-xs flex-1">
                      <Check className="h-3.5 w-3.5 mr-1" /> Save
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => setEditingId(null)} className="font-mono text-xs">
                      <X className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="text-base font-bold text-[#f7f4ea]">{project.name}</h3>
                    <StatusBadge status={project.status} />
                  </div>
                  <p className="text-[11px] font-mono text-[#00ff9d]/80">{ventureName(project.venture_id)}</p>
                  {project.description && (
                    <p className="text-xs text-muted-foreground line-clamp-2">{project.description}</p>
                  )}
                  <div className="flex items-center justify-between pt-2 border-t border-[#251238]">
                    <PriorityBadge priority={project.priority} />
                    <div className="flex gap-1">
                      <button
                        type="button"
                        onClick={() => startEdit(project)}
                        className="p-2 rounded-lg hover:bg-[#251238] text-muted-foreground hover:text-[#00ff9d] min-h-[36px] min-w-[36px]"
                        aria-label="Edit project"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button
                        type="button"
                        onClick={() => setDeleteTarget(project)}
                        className="p-2 rounded-lg hover:bg-red-950/30 text-muted-foreground hover:text-red-400 min-h-[36px] min-w-[36px]"
                        aria-label="Archive project"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
      )}

      <ConfirmActionDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title={`Archive "${deleteTarget?.name}"?`}
        description="This project will be removed from your active portfolio."
        confirmLabel="Archive Project"
        onConfirm={handleDelete}
      />
    </ResponsivePageContainer>
  );
}

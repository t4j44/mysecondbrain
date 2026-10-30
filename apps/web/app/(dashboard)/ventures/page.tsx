'use client';

import * as React from 'react';
import { Briefcase, Pencil, Trash2, X, Check } from 'lucide-react';
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
import { useVentures } from '@/hooks/useVentures';
import { formatApiError } from '@/lib/api/format-error';
import type { Venture } from '@/lib/api/domains';

export default function VenturesPage() {
  const { toast } = useToast();
  const { ventures, loading, error, refetch, createVenture, updateVenture, deleteVenture } =
    useVentures();

  const [showCreate, setShowCreate] = React.useState(false);
  const [createName, setCreateName] = React.useState('');
  const [createDescription, setCreateDescription] = React.useState('');
  const [createPriority, setCreatePriority] = React.useState('medium');
  const [creating, setCreating] = React.useState(false);

  const [editingId, setEditingId] = React.useState<string | null>(null);
  const [editName, setEditName] = React.useState('');
  const [editDescription, setEditDescription] = React.useState('');
  const [editStatus, setEditStatus] = React.useState('active');
  const [editPriority, setEditPriority] = React.useState('medium');
  const [saving, setSaving] = React.useState(false);

  const [deleteTarget, setDeleteTarget] = React.useState<Venture | null>(null);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createName.trim()) return;
    setCreating(true);
    try {
      await createVenture({
        name: createName.trim(),
        description: createDescription.trim() || undefined,
        priority: createPriority,
      });
      setCreateName('');
      setCreateDescription('');
      setCreatePriority('medium');
      setShowCreate(false);
      toast({ title: 'Venture created', description: createName.trim() });
    } catch (err) {
      toast({ variant: 'destructive', title: 'Create failed', description: formatApiError(err) });
    } finally {
      setCreating(false);
    }
  };

  const startEdit = (venture: Venture) => {
    setEditingId(venture.id);
    setEditName(venture.name);
    setEditDescription(venture.description ?? '');
    setEditStatus(venture.status);
    setEditPriority(venture.priority);
  };

  const handleSaveEdit = async (id: string) => {
    if (!editName.trim()) return;
    setSaving(true);
    try {
      await updateVenture(id, {
        name: editName.trim(),
        description: editDescription.trim() || undefined,
        status: editStatus,
        priority: editPriority,
      });
      setEditingId(null);
      toast({ title: 'Venture updated' });
    } catch (err) {
      toast({ variant: 'destructive', title: 'Update failed', description: formatApiError(err) });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteVenture(deleteTarget.id);
      toast({ title: 'Venture archived', description: deleteTarget.name });
    } catch (err) {
      toast({ variant: 'destructive', title: 'Delete failed', description: formatApiError(err) });
      throw err;
    }
  };

  return (
    <ResponsivePageContainer>
      <PageHeader
        title="Venture Management"
        description="Strategic business initiatives — create, edit, and archive ventures."
        badge="PORTFOLIO"
        actions={
          <Button
            data-testid="venture-create"
            onClick={() => setShowCreate((v) => !v)}
            className="font-mono text-xs min-h-[44px]"
          >
            {showCreate ? 'Cancel' : '+ New Venture'}
          </Button>
        }
      />

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
            placeholder="Venture name *"
            required
            className="w-full bg-[#0a0510] border border-[#301642] focus:border-[#00ff9d] text-sm text-[#f7f4ea] px-3 py-2.5 rounded-lg outline-none"
            autoFocus
          />
          <textarea
            value={createDescription}
            onChange={(e) => setCreateDescription(e.target.value)}
            placeholder="Description (optional)"
            rows={2}
            className="w-full bg-[#0a0510] border border-[#301642] focus:border-[#00ff9d] text-sm text-[#f7f4ea] px-3 py-2.5 rounded-lg outline-none resize-none"
          />
          <select
            value={createPriority}
            onChange={(e) => setCreatePriority(e.target.value)}
            className="bg-[#0a0510] border border-[#301642] text-xs font-mono text-[#f7f4ea] px-3 py-2 rounded-lg"
          >
            <option value="low">Low priority</option>
            <option value="medium">Medium priority</option>
            <option value="high">High priority</option>
            <option value="urgent">Urgent</option>
          </select>
          <Button type="submit" disabled={creating || !createName.trim()} className="font-mono text-xs">
            {creating ? 'Creating...' : 'Create Venture'}
          </Button>
        </form>
      )}

      {loading ? (
        <LoadingState rows={3} showHeader={false} />
      ) : ventures.length === 0 ? (
        <EmptyState
          icon={Briefcase}
          title="No ventures yet"
          description="Create your first venture to organize projects and tasks."
          actionLabel="Create Venture"
          onAction={() => setShowCreate(true)}
        />
      ) : (
        <div data-testid="venture-list" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {ventures.map((venture) => (
            <div
              key={venture.id}
              data-testid="venture-card"
              className="rounded-xl border border-[#251238] bg-[#0a0510] p-4 space-y-3 hover:border-[#00ff9d]/40 transition-colors"
            >
              {editingId === venture.id ? (
                <div data-testid="venture-edit" className="space-y-2">
                  <input
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    className="w-full bg-[#12081d] border border-[#301642] focus:border-[#00ff9d] text-sm text-[#f7f4ea] px-3 py-2 rounded-lg outline-none"
                  />
                  <textarea
                    value={editDescription}
                    onChange={(e) => setEditDescription(e.target.value)}
                    rows={2}
                    className="w-full bg-[#12081d] border border-[#301642] text-sm text-[#f7f4ea] px-3 py-2 rounded-lg outline-none resize-none"
                  />
                  <div className="flex gap-2">
                    <select
                      value={editStatus}
                      onChange={(e) => setEditStatus(e.target.value)}
                      className="flex-1 bg-[#12081d] border border-[#301642] text-xs font-mono text-[#f7f4ea] px-2 py-1.5 rounded-lg"
                    >
                      <option value="active">Active</option>
                      <option value="paused">Paused</option>
                      <option value="archived">Archived</option>
                    </select>
                    <select
                      value={editPriority}
                      onChange={(e) => setEditPriority(e.target.value)}
                      className="flex-1 bg-[#12081d] border border-[#301642] text-xs font-mono text-[#f7f4ea] px-2 py-1.5 rounded-lg"
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="urgent">Urgent</option>
                    </select>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={() => handleSaveEdit(venture.id)}
                      disabled={saving}
                      className="font-mono text-xs flex-1"
                    >
                      <Check className="h-3.5 w-3.5 mr-1" />
                      Save
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setEditingId(null)}
                      className="font-mono text-xs"
                    >
                      <X className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="text-base font-bold text-[#f7f4ea]">{venture.name}</h3>
                    <StatusBadge status={venture.status} />
                  </div>
                  {venture.description && (
                    <p className="text-xs text-muted-foreground line-clamp-2">{venture.description}</p>
                  )}
                  <div className="flex items-center justify-between pt-2 border-t border-[#251238]">
                    <PriorityBadge priority={venture.priority} />
                    <div className="flex gap-1">
                      <button
                        type="button"
                        onClick={() => startEdit(venture)}
                        className="p-2 rounded-lg hover:bg-[#251238] text-muted-foreground hover:text-[#00ff9d] min-h-[36px] min-w-[36px]"
                        aria-label="Edit venture"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button
                        type="button"
                        onClick={() => setDeleteTarget(venture)}
                        className="p-2 rounded-lg hover:bg-red-950/30 text-muted-foreground hover:text-red-400 min-h-[36px] min-w-[36px]"
                        aria-label="Archive venture"
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
        description="This venture will be archived. Linked projects and tasks remain but the venture will no longer appear in active lists."
        confirmLabel="Archive Venture"
        onConfirm={handleDelete}
      />
    </ResponsivePageContainer>
  );
}

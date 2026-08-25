'use client';

import * as React from 'react';
import { CheckSquare, Trash2, ChevronDown, ChevronUp } from 'lucide-react';
import { ResponsivePageContainer } from '@/components/shared/responsive-page-container';
import { PageHeader } from '@/components/shared/page-header';
import { EmptyState } from '@/components/shared/empty-state';
import { LoadingState } from '@/components/shared/loading-state';
import { ErrorState } from '@/components/shared/error-state';
import { ConfirmActionDialog } from '@/components/shared/confirm-action-dialog';
import { PriorityBadge } from '@/components/shared/priority-badge';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';
import { useTasks } from '@/hooks/useTasks';
import { useVentures } from '@/hooks/useVentures';
import { useProjects } from '@/hooks/useProjects';
import { formatApiError } from '@/lib/api/format-error';
import type { Task, TaskStatusFilter } from '@/lib/api/domains';

const STATUS_FILTERS: { label: string; value: TaskStatusFilter }[] = [
  { label: 'All', value: 'all' },
  { label: 'Todo', value: 'todo' },
  { label: 'In Progress', value: 'in_progress' },
  { label: 'Done', value: 'done' },
];

const STATUS_CYCLE: Record<string, string> = {
  todo: 'in_progress',
  in_progress: 'done',
  done: 'todo',
};

export default function TasksPage() {
  const { toast } = useToast();
  const [statusFilter, setStatusFilter] = React.useState<TaskStatusFilter>('all');
  const { tasks, loading, error, refetch, createTask, updateTask, deleteTask } = useTasks({
    status: statusFilter,
  });
  const { ventures } = useVentures();
  const { projects } = useProjects();

  const [quickTitle, setQuickTitle] = React.useState('');
  const [showOptions, setShowOptions] = React.useState(false);
  const [optVentureId, setOptVentureId] = React.useState('');
  const [optProjectId, setOptProjectId] = React.useState('');
  const [optPriority, setOptPriority] = React.useState('medium');
  const [optDueDate, setOptDueDate] = React.useState('');
  const [creating, setCreating] = React.useState(false);

  const [deleteTarget, setDeleteTarget] = React.useState<Task | null>(null);

  const filteredProjects = optVentureId
    ? projects.filter((p) => p.venture_id === optVentureId)
    : projects;

  const handleQuickCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!quickTitle.trim()) return;
    setCreating(true);
    try {
      await createTask({
        title: quickTitle.trim(),
        venture_id: optVentureId || undefined,
        project_id: optProjectId || undefined,
        priority: optPriority,
        due_date: optDueDate ? new Date(optDueDate).toISOString() : undefined,
      });
      setQuickTitle('');
      setOptDueDate('');
      toast({ title: 'Task created', description: quickTitle.trim() });
    } catch (err) {
      toast({ variant: 'destructive', title: 'Create failed', description: formatApiError(err) });
    } finally {
      setCreating(false);
    }
  };

  const handleStatusToggle = async (task: Task) => {
    const next = STATUS_CYCLE[task.status] ?? 'todo';
    try {
      await updateTask(task.id, { status: next });
    } catch (err) {
      toast({ variant: 'destructive', title: 'Status update failed', description: formatApiError(err) });
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteTask(deleteTarget.id);
      toast({ title: 'Task deleted', description: deleteTarget.title });
    } catch (err) {
      toast({ variant: 'destructive', title: 'Delete failed', description: formatApiError(err) });
      throw err;
    }
  };

  const ventureName = (id?: string | null) => ventures.find((v) => v.id === id)?.name;
  const projectName = (id?: string | null) => projects.find((p) => p.id === id)?.name;

  return (
    <ResponsivePageContainer>
      <PageHeader
        title="Task Execution Engine"
        description="Quick capture — type a title and press Enter. Filter by status below."
        badge="EXECUTION"
      />

      <form onSubmit={handleQuickCreate} className="mb-4 space-y-2">
        <div className="relative flex items-center gap-2">
          <input
            data-testid="task-quick-input"
            type="text"
            value={quickTitle}
            onChange={(e) => setQuickTitle(e.target.value)}
            placeholder="What needs doing? Press Enter to add..."
            className="flex-1 bg-[#0e0716] border border-[#3b1e5a] focus:border-[#00ff9d] focus:ring-1 focus:ring-[#00ff9d] text-sm sm:text-base text-[#f7f4ea] placeholder:text-muted-foreground/60 px-4 py-3.5 rounded-xl outline-none min-h-[44px]"
            disabled={creating}
          />
          <Button type="submit" disabled={creating || !quickTitle.trim()} className="font-mono text-xs shrink-0 min-h-[44px]">
            Add
          </Button>
        </div>

        <button
          type="button"
          onClick={() => setShowOptions((v) => !v)}
          className="flex items-center gap-1 text-xs font-mono text-[#00ff9d] hover:underline"
        >
          {showOptions ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          {showOptions ? 'Hide options' : 'Add venture, project, priority, due date'}
        </button>

        {showOptions && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 p-3 rounded-xl bg-[#12081d] border border-[#251238]">
            <select
              value={optVentureId}
              onChange={(e) => {
                setOptVentureId(e.target.value);
                setOptProjectId('');
              }}
              className="bg-[#0a0510] border border-[#301642] text-xs font-mono text-[#f7f4ea] px-3 py-2 rounded-lg min-h-[44px]"
            >
              <option value="">Venture (optional)</option>
              {ventures.map((v) => (
                <option key={v.id} value={v.id}>{v.name}</option>
              ))}
            </select>
            <select
              value={optProjectId}
              onChange={(e) => setOptProjectId(e.target.value)}
              className="bg-[#0a0510] border border-[#301642] text-xs font-mono text-[#f7f4ea] px-3 py-2 rounded-lg min-h-[44px]"
            >
              <option value="">Project (optional)</option>
              {filteredProjects.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
            <select
              value={optPriority}
              onChange={(e) => setOptPriority(e.target.value)}
              className="bg-[#0a0510] border border-[#301642] text-xs font-mono text-[#f7f4ea] px-3 py-2 rounded-lg min-h-[44px]"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
            <input
              type="date"
              value={optDueDate}
              onChange={(e) => setOptDueDate(e.target.value)}
              className="bg-[#0a0510] border border-[#301642] text-xs font-mono text-[#f7f4ea] px-3 py-2 rounded-lg min-h-[44px]"
            />
          </div>
        )}
      </form>

      <div className="flex flex-wrap gap-2 mb-6">
        {STATUS_FILTERS.map((f) => (
          <button
            key={f.value}
            type="button"
            onClick={() => setStatusFilter(f.value)}
            className={`px-3 py-2 rounded-lg text-xs font-mono uppercase whitespace-nowrap transition-all min-h-[44px] ${
              statusFilter === f.value
                ? 'bg-[#00ff9d] text-[#0a0510] font-bold'
                : 'bg-[#12081d] text-muted-foreground hover:text-[#f7f4ea] border border-[#251238]'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {error && <ErrorState error={error} onRetry={refetch} />}

      {loading ? (
        <LoadingState rows={4} showHeader={false} />
      ) : tasks.length === 0 ? (
        <EmptyState
          icon={CheckSquare}
          title={statusFilter === 'all' ? 'No tasks yet' : `No ${statusFilter.replace('_', ' ')} tasks`}
          description="Type above and press Enter to capture your first task."
        />
      ) : (
        <div data-testid="task-list" className="space-y-2">
          {tasks.map((task) => (
            <div
              key={task.id}
              data-testid="task-row"
              className="flex flex-col sm:flex-row sm:items-center gap-3 rounded-xl border border-[#251238] bg-[#0a0510] p-4 hover:border-[#00ff9d]/30 transition-colors"
            >
              <button
                type="button"
                data-testid="task-status"
                onClick={() => handleStatusToggle(task)}
                className={`shrink-0 h-6 w-6 rounded border-2 flex items-center justify-center transition-colors min-h-[44px] min-w-[44px] sm:min-h-0 sm:min-w-0 ${
                  task.status === 'done'
                    ? 'bg-[#00ff9d]/20 border-[#00ff9d] text-[#00ff9d]'
                    : task.status === 'in_progress'
                      ? 'border-[#ffb800] bg-[#ffb800]/10'
                      : 'border-[#301642] hover:border-[#00ff9d]'
                }`}
                aria-label={`Status: ${task.status}. Click to change.`}
              >
                {task.status === 'done' && <CheckSquare className="h-3.5 w-3.5" />}
              </button>

              <div className="flex-1 min-w-0">
                <p className={`text-sm font-medium ${task.status === 'done' ? 'line-through text-muted-foreground' : 'text-[#f7f4ea]'}`}>
                  {task.title}
                </p>
                <div className="flex flex-wrap items-center gap-2 mt-1">
                  <span className="text-[10px] font-mono uppercase text-muted-foreground">{task.status.replace('_', ' ')}</span>
                  <PriorityBadge priority={task.priority} />
                  {ventureName(task.venture_id) && (
                    <span className="text-[10px] font-mono text-[#00ff9d]/70">{ventureName(task.venture_id)}</span>
                  )}
                  {projectName(task.project_id) && (
                    <span className="text-[10px] font-mono text-muted-foreground">{projectName(task.project_id)}</span>
                  )}
                  {task.due_date && (
                    <span className="text-[10px] font-mono text-muted-foreground">
                      Due {new Date(task.due_date).toLocaleDateString()}
                    </span>
                  )}
                </div>
              </div>

              <button
                type="button"
                onClick={() => setDeleteTarget(task)}
                className="self-end sm:self-center p-2 rounded-lg hover:bg-red-950/30 text-muted-foreground hover:text-red-400 min-h-[44px] min-w-[44px]"
                aria-label="Delete task"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      <ConfirmActionDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete this task?"
        description={`"${deleteTarget?.title}" will be permanently removed.`}
        confirmLabel="Delete Task"
        onConfirm={handleDelete}
      />
    </ResponsivePageContainer>
  );
}

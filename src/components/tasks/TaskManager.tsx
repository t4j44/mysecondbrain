'use client';

import React, { useState, useEffect } from 'react';
import { 
  CheckSquare, 
  Square, 
  Search, 
  Calendar, 
  AlertCircle, 
  Trash2, 
  SlidersHorizontal,
  ChevronRight,
  Plus,
  Briefcase,
  FolderGit2,
  Clock
} from 'lucide-react';
import { Card, Button, StatusBadge, PriorityBadge, Dialog } from '../ui/CustomUi';
import { mockApi } from '../../lib/mockApi';
import { Task, Venture, Project, TaskStatus, TaskPriority } from '../../types/execution';

interface TaskManagerProps {
  initialView?: 'all' | 'today' | 'upcoming' | 'completed';
}

export default function TaskManager({ initialView = 'all' }: TaskManagerProps) {
  const [loading, setLoading] = useState(true);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [ventures, setVentures] = useState<Venture[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  
  // Views
  const [currentView, setCurrentView] = useState<'all' | 'today' | 'upcoming' | 'completed'>(initialView);
  
  // Filter States
  const [searchQuery, setSearchQuery] = useState('');
  const [priorityFilter, setPriorityFilter] = useState<'all' | TaskPriority>('all');
  const [ventureFilter, setVentureFilter] = useState('all');
  const [projectFilter, setProjectFilter] = useState('all');

  // Task Details Drawer State
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [updatingTaskId, setUpdatingTaskId] = useState<string | null>(null);
  
  // Detail Editor Forms
  const [editTitle, setEditTitle] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [editPriority, setEditPriority] = useState<TaskPriority>('medium');
  const [editStatus, setEditStatus] = useState<TaskStatus>('todo');
  const [editDueDate, setEditDueDate] = useState('');
  const [editVenture, setEditVenture] = useState('');
  const [editProject, setEditProject] = useState('');

  const loadData = async () => {
    setLoading(true);
    try {
      const allTasks = await mockApi.getTasks();
      const allVentures = await mockApi.getVentures();
      const allProjects = await mockApi.getProjects();
      
      setTasks(allTasks);
      setVentures(allVentures);
      setProjects(allProjects);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    window.addEventListener('second-brain-data-updated', loadData);
    return () => window.removeEventListener('second-brain-data-updated', loadData);
  }, []);

  // Sync edit forms when a task is selected
  useEffect(() => {
    if (selectedTask) {
      setEditTitle(selectedTask.title);
      setEditDesc(selectedTask.description || '');
      setEditPriority(selectedTask.priority);
      setEditStatus(selectedTask.status);
      setEditDueDate(selectedTask.due_date ? selectedTask.due_date.split('T')[0] : '');
      setEditVenture(selectedTask.venture_id || '');
      setEditProject(selectedTask.project_id || '');
    }
  }, [selectedTask]);

  // Handle task status quick completion
  const handleToggleComplete = async (task: Task, e: React.MouseEvent) => {
    e.stopPropagation(); // prevent opening details
    setUpdatingTaskId(task.id);
    
    const isDone = task.status === 'done';
    const newStatus = isDone ? 'todo' : 'done';
    
    // Optimistic UI updates
    const prevStatus = task.status;
    task.status = newStatus;
    
    try {
      await mockApi.updateTaskStatus(task.id, newStatus);
      // Fire update event
      window.dispatchEvent(new Event('second-brain-data-updated'));
    } catch (err) {
      console.error(err);
      task.status = prevStatus; // Rollback
    } finally {
      setUpdatingTaskId(null);
    }
  };

  // Handle updating task details from side panel
  const handleSaveDetails = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTask || !editTitle.trim()) return;

    try {
      await mockApi.updateTask(selectedTask.id, {
        title: editTitle,
        description: editDesc || null,
        priority: editPriority,
        status: editStatus,
        due_date: editDueDate ? new Date(editDueDate).toISOString() : null,
        venture_id: editVenture || null,
        project_id: editProject || null
      });
      setSelectedTask(null);
      window.dispatchEvent(new Event('second-brain-data-updated'));
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteTask = async () => {
    if (!selectedTask) return;
    if (!confirm('Are you sure you want to delete this task?')) return;

    try {
      await mockApi.deleteTask(selectedTask.id);
      setSelectedTask(null);
      window.dispatchEvent(new Event('second-brain-data-updated'));
    } catch (err) {
      console.error(err);
    }
  };

  // Filter logic
  const todayStr = new Date().toISOString().split('T')[0];
  
  const filteredTasks = tasks.filter(t => {
    // Search query
    const matchesSearch = t.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
      (t.description && t.description.toLowerCase().includes(searchQuery.toLowerCase()));
      
    // Dropdown filters
    const matchesPriority = priorityFilter === 'all' || t.priority === priorityFilter;
    const matchesVenture = ventureFilter === 'all' || t.venture_id === ventureFilter;
    const matchesProject = projectFilter === 'all' || t.project_id === projectFilter;
    
    if (!matchesSearch || !matchesPriority || !matchesVenture || !matchesProject) return false;

    // Subviews tabs filter
    if (currentView === 'today') {
      const isDone = t.status === 'done';
      const isDueToday = t.due_date && t.due_date.split('T')[0] === todayStr;
      const isOverdue = t.due_date && t.due_date.split('T')[0] < todayStr;
      return !isDone && (isDueToday || isOverdue || t.priority === 'urgent');
    }
    if (currentView === 'upcoming') {
      const isDone = t.status === 'done';
      const isUpcoming = t.due_date && t.due_date.split('T')[0] > todayStr;
      return !isDone && isUpcoming;
    }
    if (currentView === 'completed') {
      return t.status === 'done';
    }
    
    // Default 'all' (exclude archived)
    return t.status !== 'archived';
  });

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center p-5 bg-terminal-panel border border-terminal-border rounded-xl gap-4">
        <div className="space-y-1">
          <span className="text-[10px] uppercase font-mono tracking-wider text-terminal-accent font-semibold flex items-center gap-1">
            <Clock size={12} /> Operations Center
          </span>
          <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white font-mono uppercase">
            Task Execution Board
          </h1>
          <p className="text-xs text-terminal-muted">
            Manage daily action parameters, prioritize focus tasks, and track completed items.
          </p>
        </div>
        <Button 
          variant="primary" 
          className="flex items-center gap-1.5 self-start sm:self-auto font-mono text-xs"
          onClick={() => {
            window.dispatchEvent(new CustomEvent('open-quick-create', { detail: { tab: 'task' } }));
          }}
        >
          <Plus size={16} /> CREATE TASK
        </Button>
      </div>

      {/* View Tabs Selector */}
      <div className="flex border-b border-terminal-border font-mono text-xs pb-1">
        {([
          { key: 'all', label: 'All Tasks' },
          { key: 'today', label: 'Today Focus' },
          { key: 'upcoming', label: 'Upcoming Sprint' },
          { key: 'completed', label: 'Completed Log' }
        ] as const).map(tab => (
          <button
            key={tab.key}
            onClick={() => setCurrentView(tab.key)}
            className={`px-4 py-2.5 border-b-2 capitalize transition-all ${
              currentView === tab.key 
                ? 'border-terminal-accent text-terminal-accent font-bold' 
                : 'border-transparent text-terminal-muted hover:text-terminal-fg'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col lg:flex-row gap-4 justify-between bg-terminal-panel/40 p-4 border border-terminal-border rounded-xl font-mono text-xs">
        {/* Search */}
        <div className="flex items-center bg-terminal-panel border border-terminal-border rounded-lg px-3 py-2 w-full lg:max-w-xs">
          <Search className="text-terminal-muted mr-2 w-4 h-4" />
          <input
            type="text"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Search tasks by title..."
            className="bg-transparent text-terminal-fg placeholder-terminal-muted outline-none border-none w-full"
          />
        </div>

        {/* Dropdown Filters */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {/* Priority */}
          <select
            value={priorityFilter}
            onChange={e => setPriorityFilter(e.target.value as any)}
            className="bg-terminal-panel border border-terminal-border rounded-lg p-2 text-terminal-fg outline-none"
          >
            <option value="all">All Priorities</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="urgent">Urgent</option>
          </select>

          {/* Venture */}
          <select
            value={ventureFilter}
            onChange={e => {
              setVentureFilter(e.target.value);
              setProjectFilter('all'); // reset project
            }}
            className="bg-terminal-panel border border-terminal-border rounded-lg p-2 text-terminal-fg outline-none"
          >
            <option value="all">All Ventures</option>
            {ventures.map(v => (
              <option key={v.id} value={v.id}>{v.name}</option>
            ))}
          </select>

          {/* Project */}
          <select
            value={projectFilter}
            onChange={e => setProjectFilter(e.target.value)}
            className="bg-terminal-panel border border-terminal-border rounded-lg p-2 text-terminal-fg outline-none disabled:opacity-40 col-span-2 sm:col-span-1"
          >
            <option value="all">All Projects</option>
            {projects
              .filter(p => ventureFilter === 'all' || p.venture_id === ventureFilter)
              .map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
          </select>
        </div>
      </div>

      {/* Task Streams List */}
      {loading ? (
        <div className="space-y-3 animate-pulse">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-14 bg-terminal-panel border border-terminal-border rounded-xl" />
          ))}
        </div>
      ) : filteredTasks.length === 0 ? (
        <div className="py-16 text-center border border-terminal-border border-dashed rounded-xl font-mono text-sm text-terminal-muted">
          <AlertCircle className="w-8 h-8 text-terminal-muted mx-auto mb-3" />
          <p>
            {currentView === 'today' && 'Nothing is due today. Review upcoming work or choose a focus task.'}
            {currentView === 'upcoming' && 'No upcoming scheduled tasks. Ready for plan execution.'}
            {currentView === 'completed' && 'No completed tasks archived in this view.'}
            {currentView === 'all' && 'No tasks found matching current parameters.'}
          </p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {filteredTasks.map(task => {
            const isDone = task.status === 'done';
            const isUpdating = updatingTaskId === task.id;
            const isOverdue = task.due_date && task.due_date.split('T')[0] < todayStr && !isDone;

            return (
              <div
                key={task.id}
                onClick={() => setSelectedTask(task)}
                className={`p-3.5 rounded-lg border bg-terminal-panel/30 flex items-center justify-between gap-4 cursor-pointer hover:border-terminal-accent/30 transition-all ${
                  isOverdue ? 'border-terminal-alert/20' : 'border-terminal-border'
                } ${isUpdating ? 'opacity-50 pointer-events-none' : ''}`}
              >
                {/* Checkbox + Title */}
                <div className="flex items-start gap-3 min-w-0">
                  <button
                    onClick={(e) => handleToggleComplete(task, e)}
                    className="mt-0.5 text-terminal-muted hover:text-terminal-accent transition-colors flex-shrink-0"
                  >
                    {isDone ? (
                      <CheckSquare size={17} className="text-terminal-accent" />
                    ) : (
                      <Square size={17} />
                    )}
                  </button>
                  <div className="min-w-0">
                    <p className={`text-xs font-medium leading-snug ${isDone ? 'line-through text-terminal-muted' : 'text-terminal-fg'}`}>
                      {task.title}
                    </p>
                    <div className="flex items-center gap-3 mt-1.5 text-[9px] font-mono text-terminal-muted">
                      {task.venture_id && (
                        <span className="flex items-center gap-0.5">
                          <Briefcase size={10} />
                          {ventures.find(v => v.id === task.venture_id)?.name}
                        </span>
                      )}
                      {task.project_id && (
                        <span className="flex items-center gap-0.5">
                          <FolderGit2 size={10} />
                          {projects.find(p => p.id === task.project_id)?.name}
                        </span>
                      )}
                      {task.due_date && (
                        <span className={`flex items-center gap-0.5 ${isOverdue ? 'text-terminal-alert font-bold' : ''}`}>
                          <Calendar size={10} />
                          {isOverdue ? 'OVERDUE' : new Date(task.due_date).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Priority / Status */}
                <div className="flex items-center gap-3 flex-shrink-0">
                  <PriorityBadge priority={task.priority} />
                  <StatusBadge status={task.status} />
                  <ChevronRight size={14} className="text-terminal-muted" />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Task Details Dialog Modal */}
      <Dialog
        isOpen={selectedTask !== null}
        onClose={() => setSelectedTask(null)}
        title="MODIFY TASK ATTRIBUTES"
      >
        {selectedTask && (
          <form onSubmit={handleSaveDetails} className="space-y-4 text-sm font-sans">
            <div>
              <label className="block font-mono text-xs text-terminal-muted mb-1.5 uppercase">Task Title *</label>
              <input
                type="text"
                required
                value={editTitle}
                onChange={e => setEditTitle(e.target.value)}
                className="w-full bg-terminal-panel border border-terminal-border rounded-lg p-2.5 text-terminal-fg focus:border-terminal-accent focus:ring-1 focus:ring-terminal-accent/30 outline-none"
              />
            </div>

            <div>
              <label className="block font-mono text-xs text-terminal-muted mb-1.5 uppercase">Description</label>
              <textarea
                value={editDesc}
                onChange={e => setEditDesc(e.target.value)}
                rows={3}
                className="w-full bg-terminal-panel border border-terminal-border rounded-lg p-2.5 text-terminal-fg focus:border-terminal-accent focus:ring-1 focus:ring-terminal-accent/30 outline-none resize-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block font-mono text-xs text-terminal-muted mb-1.5 uppercase">Priority</label>
                <select
                  value={editPriority}
                  onChange={e => setEditPriority(e.target.value as TaskPriority)}
                  className="w-full bg-terminal-panel border border-terminal-border rounded-lg p-2.5 text-terminal-fg outline-none font-mono"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>
              <div>
                <label className="block font-mono text-xs text-terminal-muted mb-1.5 uppercase">Task Status</label>
                <select
                  value={editStatus}
                  onChange={e => setEditStatus(e.target.value as TaskStatus)}
                  className="w-full bg-terminal-panel border border-terminal-border rounded-lg p-2.5 text-terminal-fg outline-none font-mono"
                >
                  <option value="todo">To Do</option>
                  <option value="in_progress">In Progress</option>
                  <option value="done">Completed</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block font-mono text-xs text-terminal-muted mb-1.5 uppercase">Linked Venture</label>
                <select
                  value={editVenture}
                  onChange={e => {
                    setEditVenture(e.target.value);
                    setEditProject('');
                  }}
                  className="w-full bg-terminal-panel border border-terminal-border rounded-lg p-2.5 text-terminal-fg outline-none font-mono"
                >
                  <option value="">None (Independent)</option>
                  {ventures.map(v => (
                    <option key={v.id} value={v.id}>{v.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block font-mono text-xs text-terminal-muted mb-1.5 uppercase">Linked Project</label>
                <select
                  value={editProject}
                  onChange={e => setEditProject(e.target.value)}
                  disabled={!editVenture}
                  className="w-full bg-terminal-panel border border-terminal-border rounded-lg p-2.5 text-terminal-fg outline-none font-mono disabled:opacity-40"
                >
                  <option value="">None (Independent)</option>
                  {projects
                    .filter(p => !editVenture || p.venture_id === editVenture)
                    .map(p => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block font-mono text-xs text-terminal-muted mb-1.5 uppercase">Due Date</label>
              <input
                type="date"
                value={editDueDate}
                onChange={e => setEditDueDate(e.target.value)}
                className="w-full bg-terminal-panel border border-terminal-border rounded-lg p-2 text-terminal-fg outline-none font-mono text-xs"
              />
            </div>

            <div className="flex gap-3 justify-between pt-4 border-t border-terminal-border/10">
              <Button type="button" variant="destructive" onClick={handleDeleteTask}>
                <Trash2 size={14} className="mr-1.5" /> DELETE
              </Button>
              <div className="flex gap-2">
                <Button type="button" onClick={() => setSelectedTask(null)}>Cancel</Button>
                <Button type="submit" variant="primary">
                  Save Changes
                </Button>
              </div>
            </div>
          </form>
        )}
      </Dialog>
    </div>
  );
}

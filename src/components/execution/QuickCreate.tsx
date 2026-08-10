'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Dialog, Button } from '../ui/CustomUi';
import { mockApi } from '../../lib/mockApi';
import { Venture, Project, TaskPriority, TaskStatus, VentureStatus, ProjectStatus } from '../../types/execution';

interface QuickCreateProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function QuickCreate({ isOpen, onClose }: QuickCreateProps) {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'task' | 'project' | 'venture'>('task');
  
  // Lists for dropdown selection
  const [ventures, setVentures] = useState<Venture[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  
  // Loading & success
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Listen for custom event to set active tab
  useEffect(() => {
    const handleOpenQuickCreate = (e: Event) => {
      const customEvent = e as CustomEvent<{ tab: 'task' | 'project' | 'venture' }>;
      if (customEvent.detail && customEvent.detail.tab) {
        setActiveTab(customEvent.detail.tab);
      }
    };
    window.addEventListener('open-quick-create', handleOpenQuickCreate);
    return () => window.removeEventListener('open-quick-create', handleOpenQuickCreate);
  }, []);

  // Form states - Task
  const [taskTitle, setTaskTitle] = useState('');
  const [taskDesc, setTaskDesc] = useState('');
  const [taskVenture, setTaskVenture] = useState('');
  const [taskProject, setTaskProject] = useState('');
  const [taskPriority, setTaskPriority] = useState<TaskPriority>('medium');
  const [taskDueDate, setTaskDueDate] = useState('');

  // Form states - Project
  const [projectName, setProjectName] = useState('');
  const [projectDesc, setProjectDesc] = useState('');
  const [projectVenture, setProjectVenture] = useState('');
  const [projectTargetDate, setProjectTargetDate] = useState('');

  // Form states - Venture
  const [ventureName, setVentureName] = useState('');
  const [ventureSlug, setVentureSlug] = useState('');
  const [ventureVision, setVentureVision] = useState('');
  const [ventureMission, setVentureMission] = useState('');

  // Fetch ventures and projects list when modal opens
  useEffect(() => {
    if (isOpen) {
      mockApi.getVentures().then(setVentures);
      mockApi.getProjects().then(setProjects);
      setErrorMsg(null);
    }
  }, [isOpen]);

  // Handle auto slug creation for venture
  useEffect(() => {
    if (ventureName) {
      setVentureSlug(ventureName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, ''));
    }
  }, [ventureName]);

  const resetForms = () => {
    setTaskTitle('');
    setTaskDesc('');
    setTaskVenture('');
    setTaskProject('');
    setTaskPriority('medium');
    setTaskDueDate('');
    
    setProjectName('');
    setProjectDesc('');
    setProjectVenture('');
    setProjectTargetDate('');
    
    setVentureName('');
    setVentureSlug('');
    setVentureVision('');
    setVentureMission('');
    setErrorMsg(null);
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!taskTitle.trim()) return;

    setSubmitting(true);
    setErrorMsg(null);
    try {
      await mockApi.createTask({
        title: taskTitle,
        description: taskDesc || null,
        venture_id: taskVenture || null,
        project_id: taskProject || null,
        status: 'todo',
        priority: taskPriority,
        due_date: taskDueDate ? new Date(taskDueDate).toISOString() : null,
      });
      resetForms();
      onClose();
      router.refresh();
      // Dispatch custom event to notify listeners (e.g. page components) to reload data
      window.dispatchEvent(new Event('second-brain-data-updated'));
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to create task');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectName.trim()) return;

    setSubmitting(true);
    setErrorMsg(null);
    try {
      const newProj = await mockApi.createProject({
        name: projectName,
        description: projectDesc || null,
        venture_id: projectVenture || null,
        status: 'in_progress',
        progress: 0,
        target_date: projectTargetDate || null,
      });
      resetForms();
      onClose();
      router.push(`/projects/${newProj.id}`);
      window.dispatchEvent(new Event('second-brain-data-updated'));
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to create project');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCreateVenture = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ventureName.trim() || !ventureSlug.trim()) return;

    setSubmitting(true);
    setErrorMsg(null);
    try {
      // Check slug uniqueness
      const existing = ventures.find(v => v.slug === ventureSlug);
      if (existing) {
        throw new Error('Duplicate Slug: A venture with this slug already exists.');
      }

      const newVent = await mockApi.createVenture({
        name: ventureName,
        slug: ventureSlug,
        mission: ventureMission || null,
        vision: ventureVision || null,
        status: 'active',
      });
      resetForms();
      onClose();
      router.push(`/ventures/${newVent.id}`);
      window.dispatchEvent(new Event('second-brain-data-updated'));
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to create venture');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog isOpen={isOpen} onClose={onClose} title="EXECUTE NEW RECORD">
      <div className="space-y-4">
        {/* Navigation Tabs */}
        <div className="flex border-b border-terminal-border font-mono text-xs pb-1 mb-4">
          {(['task', 'project', 'venture'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => {
                setActiveTab(tab);
                setErrorMsg(null);
              }}
              className={`flex-1 text-center py-2 border-b-2 capitalize transition-all ${
                activeTab === tab 
                  ? 'border-terminal-accent text-terminal-accent font-bold' 
                  : 'border-transparent text-terminal-muted hover:text-terminal-fg'
              }`}
            >
              + {tab}
            </button>
          ))}
        </div>

        {errorMsg && (
          <div className="p-3 bg-terminal-alert/10 border border-terminal-alert/20 text-terminal-alert text-xs font-mono rounded">
            ERROR: {errorMsg}
          </div>
        )}

        {/* Task Form */}
        {activeTab === 'task' && (
          <form onSubmit={handleCreateTask} className="space-y-3.5 text-sm">
            <div>
              <label className="block font-mono text-xs text-terminal-muted mb-1 uppercase">Task Title *</label>
              <input
                type="text"
                required
                value={taskTitle}
                onChange={e => setTaskTitle(e.target.value)}
                placeholder="Review milestone criteria"
                className="w-full bg-terminal-panel border border-terminal-border rounded p-2.5 text-terminal-fg focus:border-terminal-accent focus:ring-1 focus:ring-terminal-accent/30 outline-none"
              />
            </div>
            
            <div>
              <label className="block font-mono text-xs text-terminal-muted mb-1 uppercase">Description</label>
              <textarea
                value={taskDesc}
                onChange={e => setTaskDesc(e.target.value)}
                placeholder="Details or specific checklist items..."
                rows={2}
                className="w-full bg-terminal-panel border border-terminal-border rounded p-2.5 text-terminal-fg focus:border-terminal-accent focus:ring-1 focus:ring-terminal-accent/30 outline-none resize-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block font-mono text-xs text-terminal-muted mb-1 uppercase">Priority</label>
                <select
                  value={taskPriority}
                  onChange={e => setTaskPriority(e.target.value as TaskPriority)}
                  className="w-full bg-terminal-panel border border-terminal-border rounded p-2 text-terminal-fg focus:border-terminal-accent outline-none"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>
              <div>
                <label className="block font-mono text-xs text-terminal-muted mb-1 uppercase">Due Date</label>
                <input
                  type="date"
                  value={taskDueDate}
                  onChange={e => setTaskDueDate(e.target.value)}
                  className="w-full bg-terminal-panel border border-terminal-border rounded p-1.5 text-terminal-fg focus:border-terminal-accent outline-none text-xs"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block font-mono text-xs text-terminal-muted mb-1 uppercase">Venture Link</label>
                <select
                  value={taskVenture}
                  onChange={e => {
                    setTaskVenture(e.target.value);
                    setTaskProject(''); // reset project
                  }}
                  className="w-full bg-terminal-panel border border-terminal-border rounded p-2 text-terminal-fg focus:border-terminal-accent outline-none"
                >
                  <option value="">None (Independent)</option>
                  {ventures.map(v => (
                    <option key={v.id} value={v.id}>{v.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block font-mono text-xs text-terminal-muted mb-1 uppercase">Project Link</label>
                <select
                  value={taskProject}
                  onChange={e => setTaskProject(e.target.value)}
                  disabled={!taskVenture}
                  className="w-full bg-terminal-panel border border-terminal-border rounded p-2 text-terminal-fg focus:border-terminal-accent outline-none disabled:opacity-40"
                >
                  <option value="">None (Independent)</option>
                  {projects
                    .filter(p => !taskVenture || p.venture_id === taskVenture)
                    .map(p => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                </select>
              </div>
            </div>

            <div className="flex gap-2 pt-2 justify-end">
              <Button type="button" onClick={onClose} disabled={submitting}>Cancel</Button>
              <Button type="submit" variant="primary" disabled={submitting || !taskTitle.trim()}>
                {submitting ? 'Creating...' : 'Create Task'}
              </Button>
            </div>
          </form>
        )}

        {/* Project Form */}
        {activeTab === 'project' && (
          <form onSubmit={handleCreateProject} className="space-y-3.5 text-sm">
            <div>
              <label className="block font-mono text-xs text-terminal-muted mb-1 uppercase">Project Name *</label>
              <input
                type="text"
                required
                value={projectName}
                onChange={e => setProjectName(e.target.value)}
                placeholder="NextJS monorepo setup"
                className="w-full bg-terminal-panel border border-terminal-border rounded p-2.5 text-terminal-fg focus:border-terminal-accent focus:ring-1 focus:ring-terminal-accent/30 outline-none"
              />
            </div>

            <div>
              <label className="block font-mono text-xs text-terminal-muted mb-1 uppercase">Description</label>
              <textarea
                value={projectDesc}
                onChange={e => setProjectDesc(e.target.value)}
                placeholder="Project objective and key milestone indicators..."
                rows={3}
                className="w-full bg-terminal-panel border border-terminal-border rounded p-2.5 text-terminal-fg focus:border-terminal-accent focus:ring-1 focus:ring-terminal-accent/30 outline-none resize-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block font-mono text-xs text-terminal-muted mb-1 uppercase">Venture Link</label>
                <select
                  value={projectVenture}
                  onChange={e => setProjectVenture(e.target.value)}
                  className="w-full bg-terminal-panel border border-terminal-border rounded p-2 text-terminal-fg focus:border-terminal-accent outline-none"
                >
                  <option value="">None (Independent)</option>
                  {ventures.map(v => (
                    <option key={v.id} value={v.id}>{v.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block font-mono text-xs text-terminal-muted mb-1 uppercase">Target Date</label>
                <input
                  type="date"
                  value={projectTargetDate}
                  onChange={e => setProjectTargetDate(e.target.value)}
                  className="w-full bg-terminal-panel border border-terminal-border rounded p-1.5 text-terminal-fg focus:border-terminal-accent outline-none text-xs"
                />
              </div>
            </div>

            <div className="flex gap-2 pt-2 justify-end">
              <Button type="button" onClick={onClose} disabled={submitting}>Cancel</Button>
              <Button type="submit" variant="primary" disabled={submitting || !projectName.trim()}>
                {submitting ? 'Creating...' : 'Create Project'}
              </Button>
            </div>
          </form>
        )}

        {/* Venture Form */}
        {activeTab === 'venture' && (
          <form onSubmit={handleCreateVenture} className="space-y-3.5 text-sm">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block font-mono text-xs text-terminal-muted mb-1 uppercase">Venture Name *</label>
                <input
                  type="text"
                  required
                  value={ventureName}
                  onChange={e => setVentureName(e.target.value)}
                  placeholder="Justor AI"
                  className="w-full bg-terminal-panel border border-terminal-border rounded p-2.5 text-terminal-fg focus:border-terminal-accent focus:ring-1 focus:ring-terminal-accent/30 outline-none"
                />
              </div>
              <div>
                <label className="block font-mono text-xs text-terminal-muted mb-1 uppercase">Slug (URL identifier) *</label>
                <input
                  type="text"
                  required
                  value={ventureSlug}
                  onChange={e => setVentureSlug(e.target.value)}
                  placeholder="justor-ai"
                  className="w-full bg-terminal-panel border border-terminal-border rounded p-2.5 text-terminal-fg focus:border-terminal-accent focus:ring-1 focus:ring-terminal-accent/30 outline-none font-mono"
                />
              </div>
            </div>

            <div>
              <label className="block font-mono text-xs text-terminal-muted mb-1 uppercase">Venture Vision</label>
              <input
                type="text"
                value={ventureVision}
                onChange={e => setVentureVision(e.target.value)}
                placeholder="Decentralized multi-agent execution standard"
                className="w-full bg-terminal-panel border border-terminal-border rounded p-2.5 text-terminal-fg focus:border-terminal-accent focus:ring-1 focus:ring-terminal-accent/30 outline-none"
              />
            </div>

            <div>
              <label className="block font-mono text-xs text-terminal-muted mb-1 uppercase">Venture Mission</label>
              <textarea
                value={ventureMission}
                onChange={e => setVentureMission(e.target.value)}
                placeholder="Explain the mission target for this venture..."
                rows={2}
                className="w-full bg-terminal-panel border border-terminal-border rounded p-2.5 text-terminal-fg focus:border-terminal-accent focus:ring-1 focus:ring-terminal-accent/30 outline-none resize-none"
              />
            </div>

            <div className="flex gap-2 pt-2 justify-end">
              <Button type="button" onClick={onClose} disabled={submitting}>Cancel</Button>
              <Button type="submit" variant="primary" disabled={submitting || !ventureName.trim()}>
                {submitting ? 'Creating...' : 'Create Venture'}
              </Button>
            </div>
          </form>
        )}
      </div>
    </Dialog>
  );
}

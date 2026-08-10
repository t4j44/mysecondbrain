'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { FolderGit2, ArrowLeft, Save } from 'lucide-react';
import LayoutShell from '../../../../components/layout/Sidebar';
import { Card, Button } from '../../../../components/ui/CustomUi';
import { mockApi } from '../../../../lib/mockApi';
import { Venture, Project, ProjectStatus } from '../../../../types/execution';

export default function EditProjectPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = params.projectId as string;

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [ventures, setVentures] = useState<Venture[]>([]);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [ventureId, setVentureId] = useState('');
  const [targetDate, setTargetDate] = useState('');
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<ProjectStatus>('in_progress');

  useEffect(() => {
    Promise.all([
      mockApi.getVentures(),
      mockApi.getProjectById(projectId)
    ]).then(([vList, proj]) => {
      setVentures(vList);
      setName(proj.name);
      setDescription(proj.description || '');
      setVentureId(proj.venture_id || '');
      setTargetDate(proj.target_date || '');
      setProgress(proj.progress);
      setStatus(proj.status);
      setLoading(false);
    }).catch(err => {
      setErrorMsg(err.message || 'Project details not loaded');
      setLoading(false);
    });
  }, [projectId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    if (progress < 0 || progress > 100) {
      setErrorMsg('Progress must reside between 0 and 100.');
      return;
    }

    setSubmitting(true);
    setErrorMsg(null);
    try {
      await mockApi.updateProject(projectId, {
        name: name.trim(),
        description: description.trim() || null,
        venture_id: ventureId || null,
        target_date: targetDate || null,
        progress: Number(progress),
        status: status,
      });

      window.dispatchEvent(new Event('second-brain-data-updated'));
      router.push(`/projects/${projectId}`);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to update project.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <LayoutShell>
      <div className="max-w-2xl mx-auto space-y-6">
        <Link href={`/projects/${projectId}`} className="inline-flex items-center gap-1.5 text-xs text-terminal-muted hover:text-terminal-accent font-mono transition-colors">
          <ArrowLeft size={14} /> CANCEL AND RETURN
        </Link>

        {loading ? (
          <div className="h-64 bg-terminal-panel border border-terminal-border rounded-xl animate-pulse" />
        ) : (
          <Card 
            header={
              <div className="flex items-center gap-2">
                <FolderGit2 size={16} className="text-terminal-accent" />
                <h2 className="font-mono text-sm font-bold text-white uppercase tracking-wider">Configure Project Parameters</h2>
              </div>
            }
          >
            {errorMsg && (
              <div className="mb-4 p-3 bg-terminal-alert/10 border border-terminal-alert/20 text-terminal-alert text-xs font-mono rounded">
                ERROR: {errorMsg}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4 text-sm">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block font-mono text-xs text-terminal-muted mb-1.5 uppercase">Project Name *</label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={e => setName(e.target.value)}
                    className="w-full bg-terminal-panel border border-terminal-border rounded-lg p-2.5 text-terminal-fg focus:border-terminal-accent focus:ring-1 focus:ring-terminal-accent/30 outline-none"
                  />
                </div>
                <div>
                  <label className="block font-mono text-xs text-terminal-muted mb-1.5 uppercase">Linked Venture</label>
                  <select
                    value={ventureId}
                    onChange={e => setVentureId(e.target.value)}
                    className="w-full bg-terminal-panel border border-terminal-border rounded-lg p-2.5 text-terminal-fg focus:border-terminal-accent outline-none font-mono"
                  >
                    <option value="">None (Independent)</option>
                    {ventures.map(v => (
                      <option key={v.id} value={v.id}>{v.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-mono text-xs text-terminal-muted mb-1.5 uppercase">Description</label>
                <textarea
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  rows={3}
                  className="w-full bg-terminal-panel border border-terminal-border rounded-lg p-2.5 text-terminal-fg focus:border-terminal-accent focus:ring-1 focus:ring-terminal-accent/30 outline-none resize-none"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block font-mono text-xs text-terminal-muted mb-1.5 uppercase">Project Status</label>
                  <select
                    value={status}
                    onChange={e => setStatus(e.target.value as ProjectStatus)}
                    className="w-full bg-terminal-panel border border-terminal-border rounded-lg p-2.5 text-terminal-fg focus:border-terminal-accent outline-none font-mono"
                  >
                    <option value="planning">Planning</option>
                    <option value="in_progress">Active</option>
                    <option value="completed">Completed</option>
                    <option value="on_hold">On Hold</option>
                  </select>
                </div>
                <div>
                  <label className="block font-mono text-xs text-terminal-muted mb-1.5 uppercase">Progress Percentage *</label>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    required
                    value={progress}
                    onChange={e => setProgress(Number(e.target.value))}
                    className="w-full bg-terminal-panel border border-terminal-border rounded-lg p-2.5 text-terminal-fg focus:border-terminal-accent outline-none font-mono"
                  />
                </div>
                <div>
                  <label className="block font-mono text-xs text-terminal-muted mb-1.5 uppercase">Target Date</label>
                  <input
                    type="date"
                    value={targetDate}
                    onChange={e => setTargetDate(e.target.value)}
                    className="w-full bg-terminal-panel border border-terminal-border rounded-lg p-1.5 text-terminal-fg focus:border-terminal-accent outline-none font-mono text-xs"
                  />
                </div>
              </div>

              <div className="flex gap-3 justify-end pt-4 border-t border-terminal-border/10">
                <Link href={`/projects/${projectId}`}>
                  <Button type="button" disabled={submitting}>Cancel</Button>
                </Link>
                <Button type="submit" variant="primary" disabled={submitting || !name.trim()}>
                  <Save size={14} className="mr-1.5" />
                  {submitting ? 'Saving Config...' : 'Save Parameters'}
                </Button>
              </div>
            </form>
          </Card>
        )}
      </div>
    </LayoutShell>
  );
}

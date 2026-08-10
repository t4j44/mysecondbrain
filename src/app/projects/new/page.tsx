'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { FolderGit2, ArrowLeft } from 'lucide-react';
import LayoutShell from '../../../components/layout/Sidebar';
import { Card, Button } from '../../../components/ui/CustomUi';
import { mockApi } from '../../../lib/mockApi';
import { Venture } from '../../../types/execution';

function NewProjectForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const presetVentureId = searchParams.get('ventureId') || '';

  const [ventures, setVentures] = useState<Venture[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [ventureId, setVentureId] = useState(presetVentureId);
  const [targetDate, setTargetDate] = useState('');

  useEffect(() => {
    mockApi.getVentures().then(data => {
      setVentures(data);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setSubmitting(true);
    setErrorMsg(null);
    try {
      const newProject = await mockApi.createProject({
        name: name.trim(),
        description: description.trim() || null,
        venture_id: ventureId || null,
        status: 'in_progress',
        progress: 0,
        target_date: targetDate || null,
      });

      window.dispatchEvent(new Event('second-brain-data-updated'));
      router.push(`/projects/${newProject.id}`);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to create project.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="h-64 bg-terminal-panel border border-terminal-border rounded-xl animate-pulse" />
    );
  }

  return (
    <Card 
      header={
        <div className="flex items-center gap-2">
          <FolderGit2 size={16} className="text-terminal-accent" />
          <h2 className="font-mono text-sm font-bold text-white uppercase tracking-wider">Initialize New Project</h2>
        </div>
      }
    >
      {errorMsg && (
        <div className="mb-4 p-3 bg-terminal-alert/10 border border-terminal-alert/20 text-terminal-alert text-xs font-mono rounded">
          ERROR: {errorMsg}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4 text-sm">
        <div>
          <label className="block font-mono text-xs text-terminal-muted mb-1.5 uppercase">Project Name *</label>
          <input
            type="text"
            required
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="Compliance engine audit logs"
            className="w-full bg-terminal-panel border border-terminal-border rounded-lg p-2.5 text-terminal-fg focus:border-terminal-accent focus:ring-1 focus:ring-terminal-accent/30 outline-none"
          />
        </div>

        <div>
          <label className="block font-mono text-xs text-terminal-muted mb-1.5 uppercase">Description</label>
          <textarea
            value={description}
            onChange={e => setDescription(e.target.value)}
            placeholder="Define the scope and core milestone indicators..."
            rows={3}
            className="w-full bg-terminal-panel border border-terminal-border rounded-lg p-2.5 text-terminal-fg focus:border-terminal-accent focus:ring-1 focus:ring-terminal-accent/30 outline-none resize-none"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block font-mono text-xs text-terminal-muted mb-1.5 uppercase">Venture Link</label>
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
          <div>
            <label className="block font-mono text-xs text-terminal-muted mb-1.5 uppercase">Target Date</label>
            <input
              type="date"
              value={targetDate}
              onChange={e => setTargetDate(e.target.value)}
              className="w-full bg-terminal-panel border border-terminal-border rounded-lg p-2 text-terminal-fg focus:border-terminal-accent outline-none font-mono text-xs"
            />
          </div>
        </div>

        <div className="flex gap-3 justify-end pt-4 border-t border-terminal-border/10">
          <Link href="/projects">
            <Button type="button" disabled={submitting}>Cancel</Button>
          </Link>
          <Button type="submit" variant="primary" disabled={submitting || !name.trim()}>
            Initialize Project
          </Button>
        </div>
      </form>
    </Card>
  );
}

export default function NewProjectPage() {
  return (
    <LayoutShell>
      <div className="max-w-2xl mx-auto space-y-6">
        <Link href="/projects" className="inline-flex items-center gap-1.5 text-xs text-terminal-muted hover:text-terminal-accent font-mono transition-colors">
          <ArrowLeft size={14} /> BACK TO PROJECTS
        </Link>

        <Suspense fallback={<div className="font-mono text-xs text-terminal-muted animate-pulse">Initializing scope settings...</div>}>
          <NewProjectForm />
        </Suspense>
      </div>
    </LayoutShell>
  );
}

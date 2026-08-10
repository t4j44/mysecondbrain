'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { Briefcase, ArrowLeft, Save } from 'lucide-react';
import LayoutShell from '../../../../components/layout/Sidebar';
import { Card, Button } from '../../../../components/ui/CustomUi';
import { mockApi } from '../../../../lib/mockApi';
import { Venture, VentureStatus } from '../../../../types/execution';

export default function EditVenturePage() {
  const router = useRouter();
  const params = useParams();
  const ventureId = params.ventureId as string;

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [name, setName] = useState('');
  const [vision, setVision] = useState('');
  const [mission, setMission] = useState('');
  const [status, setStatus] = useState<VentureStatus>('active');

  useEffect(() => {
    mockApi.getVentureById(ventureId).then(v => {
      setName(v.name);
      setVision(v.vision || '');
      setMission(v.mission || '');
      setStatus(v.status);
      setLoading(false);
    }).catch(err => {
      setErrorMsg(err.message || 'Venture not found');
      setLoading(false);
    });
  }, [ventureId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setSubmitting(true);
    setErrorMsg(null);
    try {
      await mockApi.updateVenture(ventureId, {
        name: name.trim(),
        vision: vision.trim() || null,
        mission: mission.trim() || null,
        status: status,
      });

      window.dispatchEvent(new Event('second-brain-data-updated'));
      router.push(`/ventures/${ventureId}`);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to update venture.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <LayoutShell>
      <div className="max-w-2xl mx-auto space-y-6">
        <Link href={`/ventures/${ventureId}`} className="inline-flex items-center gap-1.5 text-xs text-terminal-muted hover:text-terminal-accent font-mono transition-colors">
          <ArrowLeft size={14} /> CANCEL AND RETURN
        </Link>

        {loading ? (
          <div className="h-64 bg-terminal-panel border border-terminal-border rounded-xl animate-pulse" />
        ) : (
          <Card 
            header={
              <div className="flex items-center gap-2">
                <Briefcase size={16} className="text-terminal-accent" />
                <h2 className="font-mono text-sm font-bold text-white uppercase tracking-wider">Configure Venture Parameters</h2>
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
                  <label className="block font-mono text-xs text-terminal-muted mb-1.5 uppercase">Venture Name *</label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={e => setName(e.target.value)}
                    placeholder="Justor AI"
                    className="w-full bg-terminal-panel border border-terminal-border rounded-lg p-2.5 text-terminal-fg focus:border-terminal-accent focus:ring-1 focus:ring-terminal-accent/30 outline-none"
                  />
                </div>
                <div>
                  <label className="block font-mono text-xs text-terminal-muted mb-1.5 uppercase">Venture Status</label>
                  <select
                    value={status}
                    onChange={e => setStatus(e.target.value as VentureStatus)}
                    className="w-full bg-terminal-panel border border-terminal-border rounded-lg p-2.5 text-terminal-fg focus:border-terminal-accent outline-none font-mono"
                  >
                    <option value="active">Active</option>
                    <option value="paused">Paused</option>
                    <option value="exited">Exited</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-mono text-xs text-terminal-muted mb-1.5 uppercase">Vision Statement</label>
                <input
                  type="text"
                  value={vision}
                  onChange={e => setVision(e.target.value)}
                  placeholder="Empower creators with private execution agents"
                  className="w-full bg-terminal-panel border border-terminal-border rounded-lg p-2.5 text-terminal-fg focus:border-terminal-accent focus:ring-1 focus:ring-terminal-accent/30 outline-none"
                />
              </div>

              <div>
                <label className="block font-mono text-xs text-terminal-muted mb-1.5 uppercase">Mission Target</label>
                <textarea
                  value={mission}
                  onChange={e => setMission(e.target.value)}
                  placeholder="Explain the mission target for this venture..."
                  rows={4}
                  className="w-full bg-terminal-panel border border-terminal-border rounded-lg p-2.5 text-terminal-fg focus:border-terminal-accent focus:ring-1 focus:ring-terminal-accent/30 outline-none resize-none"
                />
              </div>

              <div className="flex gap-3 justify-end pt-4 border-t border-terminal-border/10">
                <Link href={`/ventures/${ventureId}`}>
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

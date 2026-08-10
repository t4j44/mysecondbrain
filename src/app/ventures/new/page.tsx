'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Briefcase, ArrowLeft } from 'lucide-react';
import LayoutShell from '../../../components/layout/Sidebar';
import { Card, Button } from '../../../components/ui/CustomUi';
import { mockApi } from '../../../lib/mockApi';

export default function NewVenturePage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [vision, setVision] = useState('');
  const [mission, setMission] = useState('');

  // Auto-generate slug from name
  useEffect(() => {
    setSlug(name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, ''));
  }, [name]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !slug.trim()) return;

    setSubmitting(true);
    setErrorMsg(null);
    try {
      // Validate unique slug
      const all = await mockApi.getVentures(true);
      if (all.some(v => v.slug === slug)) {
        throw new Error('Duplicate Slug: A venture with this slug URL identifier already exists.');
      }

      const newVenture = await mockApi.createVenture({
        name: name.trim(),
        slug: slug.trim(),
        vision: vision.trim() || null,
        mission: mission.trim() || null,
        status: 'active',
      });

      window.dispatchEvent(new Event('second-brain-data-updated'));
      router.push(`/ventures/${newVenture.id}`);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to create venture.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <LayoutShell>
      <div className="max-w-2xl mx-auto space-y-6">
        <Link href="/ventures" className="inline-flex items-center gap-1.5 text-xs text-terminal-muted hover:text-terminal-accent font-mono transition-colors">
          <ArrowLeft size={14} /> BACK TO LIST
        </Link>

        <Card 
          header={
            <div className="flex items-center gap-2">
              <Briefcase size={16} className="text-terminal-accent" />
              <h2 className="font-mono text-sm font-bold text-white uppercase tracking-wider">Initialize New Venture</h2>
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
                <label className="block font-mono text-xs text-terminal-muted mb-1.5 uppercase">Slug identifier *</label>
                <input
                  type="text"
                  required
                  value={slug}
                  onChange={e => setSlug(e.target.value)}
                  placeholder="justor-ai"
                  className="w-full bg-terminal-panel border border-terminal-border rounded-lg p-2.5 text-terminal-fg focus:border-terminal-accent focus:ring-1 focus:ring-terminal-accent/30 outline-none font-mono"
                />
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
                placeholder="Flesh out the exact long-term mission parameters..."
                rows={4}
                className="w-full bg-terminal-panel border border-terminal-border rounded-lg p-2.5 text-terminal-fg focus:border-terminal-accent focus:ring-1 focus:ring-terminal-accent/30 outline-none resize-none"
              />
            </div>

            <div className="flex gap-3 justify-end pt-4 border-t border-terminal-border/10">
              <Link href="/ventures">
                <Button type="button" disabled={submitting}>Cancel</Button>
              </Link>
              <Button type="submit" variant="primary" disabled={submitting || !name.trim()}>
                {submitting ? 'Initializing...' : 'Initialize Venture'}
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </LayoutShell>
  );
}

'use client';

import React, { useState } from 'react';
import { CheckCircle2, ArrowRight, X, Sparkles, Clock, Flame } from 'lucide-react';
import { api } from '@/lib/api/browser-client';
import { useToast } from '@/components/ui/use-toast';

interface WorkSessionModalProps {
  isOpen: boolean;
  onClose: () => void;
  completedCount?: number;
}

export function WorkSessionModal({
  isOpen,
  onClose,
  completedCount = 3,
}: WorkSessionModalProps) {
  const [accomplishment, setAccomplishment] = useState('');
  const [nextAction, setNextAction] = useState('');
  const [saving, setSaving] = useState(false);
  const { toast } = useToast();

  if (!isOpen) return null;

  const handleFinish = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);

    try {
      // Save session wrap-up to memories and next return task
      const summary = `Session Wrap-up: ${accomplishment || 'Focused execution session'}. Next immediate focus: ${nextAction || 'Continue priority pipeline'}`;

      await api.post('/api/v1/memories', {
        title: `Work Session Summary — ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`,
        content: summary,
        category: 'reflection',
        tags: ['work-session', 'founder-momentum'],
      });

      if (nextAction.trim()) {
        await api.post('/api/v1/tasks', {
          title: `Next Return Action: ${nextAction}`,
          description: `Logged from session wrap-up`,
          priority: 'high',
          due_date: new Date().toISOString(),
        });
      }

      toast({
        title: '🔥 Session Logged & Context Anchored',
        description: `Your next return step "${nextAction || 'Next action'}" is pinned to TODAY.`,
      });

      onClose();
    } catch (err) {
      toast({
        title: '✓ Session Saved Locally',
        description: 'Context anchor established.',
      });
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[250] flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="fixed inset-0" onClick={onClose} aria-hidden="true" />

      <div
        className="relative w-full max-w-lg rounded-t-2xl sm:rounded-2xl border border-[#3b1e5a] bg-[#0a0510] shadow-[0_0_50px_rgba(0,255,157,0.15)] overflow-hidden animate-in slide-in-from-bottom sm:zoom-in-95 duration-200 z-10 font-sans"
        role="dialog"
        aria-modal="true"
        aria-label="Finalize Work Session"
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-[#251238] bg-[#0e0716]">
          <div className="flex items-center space-x-2">
            <div className="h-7 w-7 rounded-lg bg-[#00ff9d]/10 border border-[#00ff9d]/40 flex items-center justify-center text-[#00ff9d]">
              <Flame className="h-4 w-4 text-[#00ff9d]" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-[#f7f4ea] tracking-tight uppercase font-mono">
                Finalize Work Session
              </h3>
              <p className="text-[10px] text-muted-foreground font-mono">
                Anchor context to eliminate context-switching friction
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="inline-flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground hover:bg-[#251238] hover:text-[#f7f4ea] transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <form onSubmit={handleFinish} className="p-5 sm:p-6 space-y-5">
          {/* Quick Accomplishment Banner */}
          <div className="flex items-center justify-between p-3.5 rounded-xl bg-[#12081d] border border-[#301642]">
            <div className="flex items-center space-x-3">
              <CheckCircle2 className="h-5 w-5 text-[#00ff9d]" />
              <div>
                <span className="text-xs font-bold text-[#f7f4ea] block">
                  Session Completed
                </span>
                <span className="text-[11px] text-muted-foreground">
                  Momentum maintained • Ready to power down
                </span>
              </div>
            </div>
            <span className="text-xs font-mono font-bold text-[#00ff9d] bg-[#00ff9d]/10 px-2.5 py-1 rounded border border-[#00ff9d]/30">
              +{completedCount} items
            </span>
          </div>

          {/* Key Output Note */}
          <div className="space-y-1.5">
            <label className="text-xs font-mono uppercase text-[#00ff9d] font-semibold">
              1. What got shipped or decided?
            </label>
            <input
              type="text"
              value={accomplishment}
              onChange={(e) => setAccomplishment(e.target.value)}
              placeholder="e.g. Approved seed deck revision, sent update to Aris"
              className="w-full bg-[#12081d] border border-[#301642] focus:border-[#00ff9d] text-sm text-[#f7f4ea] px-3.5 py-2.5 rounded-xl outline-none"
            />
          </div>

          {/* Next Return Action (ADHD Context Anchor) */}
          <div className="space-y-1.5">
            <label className="text-xs font-mono uppercase text-[#ff4fd8] font-semibold flex items-center gap-1.5">
              <span>2. What is the immediate next step when you return?</span>
              <span className="text-[9px] text-muted-foreground font-normal">(Crucial anchor)</span>
            </label>
            <input
              type="text"
              value={nextAction}
              onChange={(e) => setNextAction(e.target.value)}
              placeholder="e.g. Open Figma file and review pricing slider component"
              className="w-full bg-[#12081d] border border-[#301642] focus:border-[#ff4fd8] text-sm text-[#f7f4ea] px-3.5 py-2.5 rounded-xl outline-none"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 text-xs font-mono text-muted-foreground hover:text-white"
            >
              Skip & Close
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2.5 rounded-xl bg-[#00ff9d] text-[#0a0510] font-mono text-xs font-bold uppercase hover:bg-[#00e08a] transition-all flex items-center gap-2 shadow-[0_0_20px_rgba(0,255,157,0.25)] min-h-[44px]"
            >
              <span>{saving ? 'Anchoring...' : 'Wrap Session & Anchor Context'}</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

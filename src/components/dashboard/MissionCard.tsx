'use client';

import React, { useState, useEffect } from 'react';
import { Target, Edit2, Check, X, BrainCircuit } from 'lucide-react';
import { Card, Button } from '../ui/CustomUi';
import { mockApi } from '../../lib/mockApi';

interface MissionCardProps {
  initialMission?: string;
  onUpdate?: (newMission: string) => void;
}

export default function MissionCard({ initialMission = '', onUpdate }: MissionCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [mission, setMission] = useState(initialMission);
  const [inputVal, setInputVal] = useState(initialMission);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setMission(initialMission);
    setInputVal(initialMission);
  }, [initialMission]);

  const handleSave = async () => {
    if (!inputVal.trim()) return;
    setSaving(true);
    try {
      await mockApi.updateMission(inputVal.trim());
      setMission(inputVal.trim());
      setIsEditing(false);
      if (onUpdate) onUpdate(inputVal.trim());
      // Notify navigation/sidebar to update as well
      window.dispatchEvent(new Event('second-brain-data-updated'));
    } catch (err) {
      console.error('Failed to update mission', err);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setInputVal(mission);
    setIsEditing(false);
  };

  return (
    <Card className="relative overflow-hidden group">
      <div className="flex items-start gap-4">
        {/* Visual Indicator */}
        <div className="w-10 h-10 rounded-lg bg-terminal-accent/10 border border-terminal-accent/20 flex items-center justify-center flex-shrink-0 text-terminal-accent">
          <BrainCircuit size={20} className="animate-pulse" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <span className="text-[10px] uppercase font-mono tracking-widest text-terminal-accent font-semibold flex items-center gap-1">
            <Target size={12} /> Master Mission
          </span>
          
          {isEditing ? (
            <div className="mt-2 space-y-2">
              <textarea
                value={inputVal}
                onChange={e => setInputVal(e.target.value)}
                className="w-full bg-terminal-panel border border-terminal-border rounded-lg p-2.5 text-sm text-terminal-fg focus:border-terminal-accent focus:ring-1 focus:ring-terminal-accent/30 outline-none font-sans resize-none"
                rows={2}
                placeholder="Define your current mission to align today’s work with your long-term direction."
              />
              <div className="flex justify-end gap-1.5">
                <Button size="sm" onClick={handleCancel} disabled={saving}>
                  <X size={14} className="mr-1" /> Cancel
                </Button>
                <Button size="sm" variant="primary" onClick={handleSave} disabled={saving || !inputVal.trim()}>
                  <Check size={14} className="mr-1" /> {saving ? 'Saving...' : 'Save'}
                </Button>
              </div>
            </div>
          ) : (
            <div className="mt-1 flex items-start justify-between gap-4">
              {mission ? (
                <p className="text-sm md:text-base text-terminal-fg font-sans leading-relaxed">
                  "{mission}"
                </p>
              ) : (
                <p className="text-sm text-terminal-muted font-sans italic">
                  Define your current mission to align today’s work with your long-term direction.
                </p>
              )}
              
              <button
                onClick={() => setIsEditing(true)}
                className="opacity-0 group-hover:opacity-100 text-terminal-muted hover:text-terminal-accent transition-all p-1 self-start rounded bg-terminal-panel border border-terminal-border/40"
                title="Edit Mission"
              >
                <Edit2 size={13} />
              </button>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}

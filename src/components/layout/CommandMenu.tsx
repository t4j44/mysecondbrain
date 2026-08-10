'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Search, Sparkles, Terminal, FileText, ArrowRight } from 'lucide-react';
import { getMockDB } from '../../lib/mockDb';

interface CommandMenuProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function CommandMenu({ isOpen, onClose }: CommandMenuProps) {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  // Search results
  const [results, setResults] = useState<Array<{
    type: 'venture' | 'project' | 'task' | 'action';
    title: string;
    id?: string;
    href?: string;
    description?: string;
  }>>([]);

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  // Handle local searching across Mock DB
  useEffect(() => {
    if (!isOpen) return;
    const db = getMockDB();
    
    const staticActions = [
      { type: 'action', title: 'Create Task...', href: 'action:task', description: 'Open quick task execution dialog' },
      { type: 'action', title: 'Create Project...', href: 'action:project', description: 'Initialize a new project milestone pipeline' },
      { type: 'action', title: 'Create Venture...', href: 'action:venture', description: 'Setup a new startup entity container' },
      { type: 'action', title: 'Go to Today\'s Tasks', href: '/tasks?view=today', description: 'View items due today and overdue list' },
      { type: 'action', title: 'Go to Completed Tasks', href: '/tasks?view=completed', description: 'View linear operational resolution log' },
    ];

    if (!query.trim()) {
      setResults(staticActions as any);
      return;
    }

    const q = query.toLowerCase();

    const matchedVentures = db.ventures
      .filter(v => v.name.toLowerCase().includes(q) || v.slug.toLowerCase().includes(q) || (v.mission && v.mission.toLowerCase().includes(q)))
      .map(v => ({ type: 'venture', title: `Venture: ${v.name}`, href: `/ventures/${v.id}`, description: v.mission || '' }));

    const matchedProjects = db.projects
      .filter(p => p.name.toLowerCase().includes(q) || (p.description && p.description.toLowerCase().includes(q)))
      .map(p => ({ type: 'project', title: `Project: ${p.name}`, href: `/projects/${p.id}`, description: p.description || '' }));

    const matchedTasks = db.tasks
      .filter(t => t.title.toLowerCase().includes(q) || (t.description && t.description.toLowerCase().includes(q)))
      .map(t => ({ type: 'task', title: `Task: ${t.title}`, href: `/tasks`, description: t.description || '' }));

    const filteredActions = staticActions.filter(a => a.title.toLowerCase().includes(q) || a.description.toLowerCase().includes(q));

    setResults([
      ...filteredActions,
      ...matchedVentures,
      ...matchedProjects,
      ...matchedTasks
    ] as any);
    setSelectedIndex(0);
  }, [query, isOpen]);

  // Keyboard navigation logic
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      onClose();
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => (prev + 1) % Math.max(1, results.length));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => (prev - 1 + results.length) % Math.max(1, results.length));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (results[selectedIndex]) {
        triggerAction(results[selectedIndex]);
      }
    }
  };

  const triggerAction = (item: any) => {
    onClose();
    if (item.href.startsWith('action:')) {
      const formType = item.href.split(':')[1];
      // Fire custom event to open QuickCreate for specific tab
      window.dispatchEvent(new CustomEvent('open-quick-create', { detail: { tab: formType } }));
    } else {
      router.push(item.href);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center p-4 pt-[12vh]">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" onClick={onClose} />
      
      {/* Command Shell */}
      <div 
        onKeyDown={handleKeyDown}
        className="relative w-full max-w-2xl bg-terminal-panel border border-terminal-border rounded-xl shadow-[0_10px_50px_rgba(0,0,0,0.8)] overflow-hidden z-10 font-mono text-sm"
      >
        {/* Input Bar */}
        <div className="flex items-center border-b border-terminal-border px-4 py-3 bg-terminal-panel">
          <Search className="text-terminal-accent mr-3 w-5 h-5 flex-shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Type a command or search record (e.g. Justor)..."
            className="w-full bg-transparent text-terminal-fg placeholder-terminal-muted outline-none border-none text-sm"
          />
          <span className="text-[10px] text-terminal-muted border border-terminal-border px-1.5 py-0.5 rounded flex-shrink-0">ESC</span>
        </div>

        {/* Results Stream */}
        <div className="max-h-[350px] overflow-y-auto py-2 divide-y divide-terminal-border/5 bg-terminal-bg">
          {results.length === 0 ? (
            <div className="px-5 py-8 text-center text-terminal-muted text-xs">
              NO MATCHES FOUND FOR: "{query}"
            </div>
          ) : (
            results.map((item, idx) => {
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={idx}
                  onClick={() => triggerAction(item)}
                  className={`px-5 py-3 cursor-pointer transition-all flex items-start justify-between ${
                    isSelected 
                      ? 'bg-terminal-fg/5 text-terminal-accent border-l-2 border-terminal-accent' 
                      : 'text-terminal-muted'
                  }`}
                >
                  <div className="flex items-start gap-3 min-w-0">
                    {item.type === 'action' && <Terminal size={16} className="mt-0.5 text-terminal-accent flex-shrink-0" />}
                    {item.type !== 'action' && <FileText size={16} className="mt-0.5 text-white flex-shrink-0" />}
                    <div className="min-w-0">
                      <p className={`font-mono text-xs ${isSelected ? 'text-white' : 'text-terminal-fg'}`}>
                        {item.title}
                      </p>
                      {item.description && (
                        <p className="text-[10px] text-terminal-muted truncate mt-0.5 max-w-[400px]">
                          {item.description}
                        </p>
                      )}
                    </div>
                  </div>
                  {isSelected && (
                    <span className="text-[10px] text-terminal-accent flex items-center gap-1 font-mono">
                      Execute <ArrowRight size={10} />
                    </span>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}

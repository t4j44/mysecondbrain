'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { Search, Terminal, ArrowRight, CornerDownLeft } from 'lucide-react';
import { Dialog } from '@radix-ui/react-dialog';

interface CommandItem {
  title: string;
  category: string;
  href: string;
  shortcut?: string;
}

const commandLinks: CommandItem[] = [
  { title: 'Command Center Dashboard', category: 'Command', href: '/dashboard', shortcut: 'D' },
  { title: 'Task Execution Engine', category: 'Command', href: '/tasks', shortcut: 'T' },
  { title: 'Venture Management', category: 'Build', href: '/ventures', shortcut: 'V' },
  { title: 'Project Portfolio', category: 'Build', href: '/projects', shortcut: 'P' },
  { title: 'Idea Validation Incubator', category: 'Build', href: '/ideas' },
  { title: 'People & CRM Network', category: 'Network', href: '/people', shortcut: 'C' },
  { title: 'Organization Directory', category: 'Network', href: '/organizations' },
  { title: 'Meeting Intelligence & Audio', category: 'Network', href: '/meetings', shortcut: 'M' },
  { title: 'Second Brain Memories', category: 'Network', href: '/memories', shortcut: 'B' },
  { title: 'Life & Founder KPIs', category: 'Growth', href: '/kpis', shortcut: 'K' },
  { title: 'Career & Venture Achievements', category: 'Growth', href: '/achievements' },
  { title: 'AI Content Synthesis Engine', category: 'Growth', href: '/content' },
  { title: 'Proactive AI Assistant', category: 'Intelligence', href: '/assistant', shortcut: 'A' },
  { title: 'Operator Settings & Protocols', category: 'System', href: '/settings', shortcut: 'S' },
];

export function CommandMenu() {
  const [open, setOpen] = React.useState(false);
  const [query, setQuery] = React.useState('');
  const [selectedIndex, setSelectedIndex] = React.useState(0);
  const inputRef = React.useRef<HTMLInputElement>(null);
  const router = useRouter();

  const filteredItems = React.useMemo(() => {
    if (!query) return commandLinks;
    const lower = query.toLowerCase();
    return commandLinks.filter(
      item => item.title.toLowerCase().includes(lower) || item.category.toLowerCase().includes(lower)
    );
  }, [query]);

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  React.useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 50);
      setSelectedIndex(0);
    }
  }, [open]);

  const handleSelect = (href: string) => {
    setOpen(false);
    setQuery('');
    router.push(href);
  };

  const handleInputKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => (prev + 1) % (filteredItems.length || 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => (prev - 1 + (filteredItems.length || 1)) % (filteredItems.length || 1));
    } else if (e.key === 'Enter' && filteredItems[selectedIndex]) {
      e.preventDefault();
      handleSelect(filteredItems[selectedIndex].href);
    } else if (e.key === 'Escape') {
      setOpen(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="inline-flex items-center justify-between rounded-md border border-border bg-[#0e0716] px-3 py-1.5 text-xs font-mono text-muted-foreground hover:border-[#00ff9d] hover:text-[#f7f4ea] transition-all duration-200 w-64 md:w-80 shadow-inner"
        aria-label="Open command menu"
      >
        <span className="inline-flex items-center">
          <Terminal className="mr-2 h-3.5 w-3.5 text-[#00ff9d]" />
          <span>Search OS & commands...</span>
        </span>
        <kbd className="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border border-border bg-[#1d0e2e] px-1.5 text-[10px] font-mono font-medium opacity-100">
          <span className="text-xs">⌘</span>K
        </kbd>
      </button>

      {open && (
        <div className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh] bg-black/80 backdrop-blur-sm animate-in fade-in duration-150">
          <div
            className="w-full max-w-xl rounded-lg border border-[#3b1e5a] bg-[#0a0510] shadow-[0_10px_50px_rgba(0,255,157,0.15)] overflow-hidden animate-in zoom-in-95 duration-150"
            role="dialog"
            aria-modal="true"
            aria-label="Command Palette"
          >
            <div className="flex items-center border-b border-border px-4 py-3">
              <Search className="h-4 w-4 mr-3 text-[#00ff9d]" />
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => { setQuery(e.target.value); setSelectedIndex(0); }}
                onKeyDown={handleInputKeyDown}
                placeholder="Type a command or jump to feature domain..."
                className="flex-1 bg-transparent text-sm font-sans text-[#f7f4ea] placeholder:text-muted-foreground focus:outline-none"
              />
              <span className="text-[10px] font-mono uppercase bg-[#251238] text-muted-foreground px-2 py-0.5 rounded border border-border">
                ESC to cancel
              </span>
            </div>

            <div className="max-h-80 overflow-y-auto p-2 space-y-1">
              {filteredItems.length === 0 ? (
                <div className="py-12 text-center font-mono text-xs text-muted-foreground">
                  [ 404: No matching command or venture domain located ]
                </div>
              ) : (
                filteredItems.map((item, index) => {
                  const isSelected = index === selectedIndex;
                  return (
                    <div
                      key={item.href}
                      onClick={() => handleSelect(item.href)}
                      onMouseEnter={() => setSelectedIndex(index)}
                      className={`flex items-center justify-between px-3 py-2 rounded-md text-sm font-sans cursor-pointer transition-colors ${
                        isSelected
                          ? 'bg-[#00ff9d]/15 text-[#f7f4ea] border border-[#00ff9d]/40 shadow-sm'
                          : 'text-muted-foreground hover:bg-muted/30 hover:text-[#f7f4ea]'
                      }`}
                    >
                      <div className="flex items-center space-x-2.5">
                        <span className="text-xs font-mono font-semibold uppercase text-[#00ff9d] bg-[#1d0e2e] px-1.5 py-0.5 rounded border border-border/50 min-w-[70px] text-center">
                          {item.category}
                        </span>
                        <span className="font-medium">{item.title}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        {item.shortcut && (
                          <kbd className="text-[10px] font-mono text-muted-foreground bg-background px-1.5 py-0.5 rounded border border-border">
                            {item.shortcut}
                          </kbd>
                        )}
                        <CornerDownLeft className={`h-3.5 w-3.5 ${isSelected ? 'text-[#00ff9d]' : 'opacity-0'}`} />
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            <div className="border-t border-border px-4 py-2 bg-[#050208] flex items-center justify-between text-[11px] font-mono text-muted-foreground">
              <span>Use ↑↓ arrows to navigate</span>
              <span className="text-[#00ff9d]">Taj’s Second Brain OS // Command Shell</span>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

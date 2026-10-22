'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { Search, Terminal, ArrowRight, CornerDownLeft } from 'lucide-react';


interface CommandItem {
  title: string;
  category: string;
  href: string;
  shortcut?: string;
}

const commandLinks: CommandItem[] = [
  { title: 'Home', category: 'Navigate', href: '/dashboard' },
  { title: 'Capture', category: 'Navigate', href: '/capture' },
  { title: 'People', category: 'Navigate', href: '/people' },
  { title: 'Work', category: 'Navigate', href: '/work' },
  { title: 'Ask', category: 'Navigate', href: '/assistant' },
  { title: 'Projects', category: 'Work', href: '/projects' },
  { title: 'Ventures', category: 'Work', href: '/ventures' },
  { title: 'Tasks', category: 'Work', href: '/tasks' },
  { title: 'Commitments', category: 'Work', href: '/work/commitments' },
  { title: 'Meetings', category: 'Work', href: '/meetings' },
  { title: 'Documents', category: 'Work', href: '/documents' },
  { title: 'Organizations', category: 'People', href: '/organizations' },
  { title: 'Settings', category: 'Navigate', href: '/settings' },
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
        className="sb-interactive inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border border-border bg-[#0e0716] p-2 text-xs font-mono text-muted-foreground hover:border-[#00ff9d] hover:text-[#f7f4ea] sm:h-10 sm:w-44 sm:justify-between sm:px-3 md:w-56 lg:w-64"
        aria-label="Open command menu"
      >
        <span className="inline-flex items-center">
          <Search className="h-4 w-4 shrink-0 text-[#00ff9d] sm:mr-2" />
          <span className="hidden truncate sm:inline">Find a page...</span>
        </span>
        <kbd className="pointer-events-none hidden h-5 select-none items-center gap-1 rounded border border-border bg-[#1d0e2e] px-1.5 text-[10px] font-mono font-medium opacity-100 sm:inline-flex">
          <span className="text-xs">⌘</span>K
        </kbd>
      </button>

      {open && (
        <div className="fixed inset-0 z-[100] flex items-start justify-center px-3 pt-[8vh] sm:pt-[15vh] bg-black/80 backdrop-blur-sm animate-in fade-in duration-150">
          <div
            className="w-full max-w-xl rounded-xl border border-[#3b1e5a] bg-[#0a0510] shadow-[0_10px_50px_rgba(0,255,157,0.15)] overflow-hidden animate-in zoom-in-95 duration-150"
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
                placeholder="Find people, work or settings..."
                className="min-w-0 flex-1 bg-transparent text-base sm:text-sm font-sans text-[#f7f4ea] placeholder:text-muted-foreground focus:outline-none"
              />
              <span className="text-[10px] font-mono uppercase bg-[#251238] text-muted-foreground px-2 py-0.5 rounded border border-border">
                ESC to cancel
              </span>
            </div>

            <div className="max-h-80 overflow-y-auto p-2 space-y-1">
              {filteredItems.length === 0 ? (
                <div className="py-12 text-center font-mono text-xs text-muted-foreground">
                  No matching pages.
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
              <span className="text-[#00ff9d]">Second Brain</span>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

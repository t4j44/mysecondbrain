'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { User, LogOut, Settings, ShieldCheck, Moon, Sun, Monitor, ChevronDown } from 'lucide-react';
import { useTheme } from 'next-themes';
import { createClient } from '@/lib/supabase/client';
import { useToast } from '@/components/ui/use-toast';

export function UserMenu() {
  const [open, setOpen] = React.useState(false);
  const [userEmail, setUserEmail] = React.useState('operator@tajssecondbrain.ai');
  const [userName, setUserName] = React.useState('Taj');
  const { theme, setTheme } = useTheme();
  const router = useRouter();
  const { toast } = useToast();
  const menuRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    async function getOperatorProfile() {
      const supabase = createClient();
      const { data: { user } } = await supabase.auth.getUser();
      if (user) {
        setUserEmail(user.email || 'operator@tajssecondbrain.ai');
        setUserName(user.user_metadata?.full_name || 'Taj');
      }
    }
    getOperatorProfile();
  }, []);

  React.useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  async function handleSignOut() {
    const supabase = createClient();
    await supabase.auth.signOut();
    toast({
      title: 'TERMINAL LOCKED',
      description: 'Operator credentials severed. Session purged.',
    });
    router.push('/login');
    router.refresh();
  }

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setOpen(prev => !prev)}
        className="inline-flex items-center space-x-2 rounded-md border border-border bg-[#0e0716] p-1.5 pl-2.5 text-xs font-mono hover:border-[#00ff9d] transition-all"
        aria-label="User account options"
      >
        <div className="flex items-center space-x-2">
          <div className="h-6 w-6 rounded bg-[#251238] border border-[#00ff9d]/50 flex items-center justify-center text-[#00ff9d] font-bold">
            {userName.charAt(0).toUpperCase()}
          </div>
          <span className="hidden sm:inline font-semibold text-[#f7f4ea] max-w-[100px] truncate">
            {userName}
          </span>
          <span className="h-2 w-2 rounded-full bg-[#00ff9d] animate-pulse-slow" title="Operator Active" />
        </div>
        <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-64 rounded-lg border border-[#3b1e5a] bg-[#0a0510] shadow-[0_10px_40px_rgba(0,0,0,0.9)] p-2 z-[150] font-sans animate-in fade-in duration-150">
          <div className="px-3 py-2 border-b border-border/60">
            <p className="text-xs font-semibold text-[#f7f4ea] truncate">{userName}</p>
            <p className="text-[11px] font-mono text-muted-foreground truncate">{userEmail}</p>
            <div className="mt-2 inline-flex items-center space-x-1 px-1.5 py-0.5 rounded bg-[#00ff9d]/10 text-[#00ff9d] text-[10px] font-mono border border-[#00ff9d]/30">
              <ShieldCheck className="h-3 w-3" />
              <span>RLS ENCLAVE VERIFIED</span>
            </div>
          </div>

          <div className="py-1 border-b border-border/60 space-y-0.5">
            <button
              onClick={() => { setOpen(false); router.push('/settings'); }}
              className="flex w-full items-center px-3 py-2 text-xs text-[#f7f4ea] hover:bg-[#251238] rounded-md transition-colors"
            >
              <Settings className="mr-2.5 h-3.5 w-3.5 text-[#00ff9d]" />
              <span>Terminal Settings & Keys</span>
            </button>
            <button
              onClick={() => { setOpen(false); router.push('/settings/profile'); }}
              className="flex w-full items-center px-3 py-2 text-xs text-[#f7f4ea] hover:bg-[#251238] rounded-md transition-colors"
            >
              <User className="mr-2.5 h-3.5 w-3.5 text-[#00ff9d]" />
              <span>Operator Profile</span>
            </button>
          </div>

          <div className="py-1 border-b border-border/60">
            <div className="px-3 py-1 text-[10px] font-mono uppercase text-muted-foreground">
              UI Theme Protocol
            </div>
            <div className="grid grid-cols-3 gap-1 px-2 py-1">
              <button
                onClick={() => setTheme('dark')}
                className={`flex flex-col items-center justify-center p-1.5 rounded text-[10px] font-mono border ${theme === 'dark' ? 'border-[#00ff9d] bg-[#00ff9d]/10 text-[#00ff9d]' : 'border-border/50 text-muted-foreground hover:bg-[#251238]'}`}
              >
                <Moon className="h-3 w-3 mb-1" />
                Dark
              </button>
              <button
                onClick={() => setTheme('light')}
                className={`flex flex-col items-center justify-center p-1.5 rounded text-[10px] font-mono border ${theme === 'light' ? 'border-[#00ff9d] bg-[#00ff9d]/10 text-[#00ff9d]' : 'border-border/50 text-muted-foreground hover:bg-[#251238]'}`}
              >
                <Sun className="h-3 w-3 mb-1" />
                Light
              </button>
              <button
                onClick={() => setTheme('system')}
                className={`flex flex-col items-center justify-center p-1.5 rounded text-[10px] font-mono border ${theme === 'system' ? 'border-[#00ff9d] bg-[#00ff9d]/10 text-[#00ff9d]' : 'border-border/50 text-muted-foreground hover:bg-[#251238]'}`}
              >
                <Monitor className="h-3 w-3 mb-1" />
                Auto
              </button>
            </div>
          </div>

          <div className="pt-1">
            <button
              onClick={handleSignOut}
              className="flex w-full items-center px-3 py-2 text-xs font-mono text-destructive hover:bg-destructive/10 rounded-md transition-colors font-bold"
            >
              <LogOut className="mr-2.5 h-3.5 w-3.5" />
              <span>LOCK TERMINAL // SIGN OUT</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

'use client';

import * as React from 'react';
import { useTheme } from 'next-themes';
import { SectionHeader } from '@/components/shared/section-header';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';
import { Moon, Sun, Monitor } from 'lucide-react';

export default function SettingsAppearancePage() {
  const { theme, setTheme } = useTheme();
  const { toast } = useToast();
  const [density, setDensity] = React.useState('standard');

  function handleSave() {
    toast({
      title: 'UI APPEARANCE APPLIED',
      description: `Theme preference and ${density} interface density locked into profile settings.`,
    });
  }

  return (
    <div className="space-y-8">
      <SectionHeader
        title="UI Appearance & Theme Protocols"
        description="Customize visual contrast, color motifs, and console viewport density."
      />

      <div className="space-y-4">
        <label className="text-xs font-mono uppercase text-muted-foreground font-semibold block">
          Color Scheme Mode
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div
            onClick={() => setTheme('dark')}
            className={`cursor-pointer rounded-lg border p-4 text-center space-y-2 transition-all ${theme === 'dark' ? 'border-[#00ff9d] bg-[#00ff9d]/10 text-[#f7f4ea]' : 'border-border bg-[#0e0716] text-muted-foreground hover:border-[#3b1e5a]'}`}
          >
            <Moon className="h-6 w-6 mx-auto text-[#00ff9d]" />
            <span className="text-sm font-bold block font-sans">Dark Founder Console</span>
            <span className="text-[11px] font-mono block text-muted-foreground">Deep purple (#12081d) high contrast terminal motif.</span>
          </div>

          <div
            onClick={() => setTheme('light')}
            className={`cursor-pointer rounded-lg border p-4 text-center space-y-2 transition-all ${theme === 'light' ? 'border-[#00ff9d] bg-[#00ff9d]/10 text-[#f7f4ea]' : 'border-border bg-[#0e0716] text-muted-foreground hover:border-[#3b1e5a]'}`}
          >
            <Sun className="h-6 w-6 mx-auto text-[#00ff9d]" />
            <span className="text-sm font-bold block font-sans">Light Editorial</span>
            <span className="text-[11px] font-mono block text-muted-foreground">Clean day-mode palette for document drafting.</span>
          </div>

          <div
            onClick={() => setTheme('system')}
            className={`cursor-pointer rounded-lg border p-4 text-center space-y-2 transition-all ${theme === 'system' ? 'border-[#00ff9d] bg-[#00ff9d]/10 text-[#f7f4ea]' : 'border-border bg-[#0e0716] text-muted-foreground hover:border-[#3b1e5a]'}`}
          >
            <Monitor className="h-6 w-6 mx-auto text-[#00ff9d]" />
            <span className="text-sm font-bold block font-sans">System Auto-Sync</span>
            <span className="text-[11px] font-mono block text-muted-foreground">Automatically align with OS day/night cycles.</span>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <label className="text-xs font-mono uppercase text-muted-foreground font-semibold block">
          Terminal Console Density
        </label>
        <div className="flex gap-4">
          {['compact', 'standard', 'comfortable'].map((opt) => (
            <button
              key={opt}
              type="button"
              onClick={() => setDensity(opt)}
              className={`px-4 py-2 rounded-md font-mono text-xs uppercase border transition-colors ${density === opt ? 'border-[#00ff9d] bg-[#00ff9d]/15 text-[#00ff9d] font-bold' : 'border-border bg-[#0e0716] text-muted-foreground hover:text-white'}`}
            >
              {opt}
            </button>
          ))}
        </div>
      </div>

      <div className="pt-4 border-t border-border">
        <Button onClick={handleSave} className="font-mono text-xs font-bold uppercase px-6">
          COMMIT APPEARANCE SETTINGS
        </Button>
      </div>
    </div>
  );
}

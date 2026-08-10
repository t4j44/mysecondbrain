import * as React from 'react';
import Link from 'next/link';
import { Terminal, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[75vh] p-6 text-center font-sans text-foreground">
      <div className="inline-flex h-20 w-20 items-center justify-center rounded-3xl bg-[#251238] border border-[#00ff9d]/50 text-[#00ff9d] shadow-[0_0_40px_rgba(0,255,157,0.15)] mb-6">
        <Terminal className="h-10 w-10" />
      </div>
      
      <div className="inline-block rounded px-2.5 py-1 text-xs font-mono font-semibold bg-[#251238] text-[#00ff9d] border border-[#00ff9d]/30 uppercase tracking-widest mb-3">
        [ 404: SECTOR NOT FOUND ]
      </div>

      <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#f7f4ea] max-w-md">
        Unmapped Venture Coordinates
      </h1>
      
      <p className="mt-2 text-sm text-muted-foreground max-w-md leading-relaxed mb-8">
        The requested feature route or record ID does not correspond to an existing node within your multi-venture RLS network graph.
      </p>

      <Link href="/dashboard">
        <Button variant="default" className="font-mono text-xs font-bold uppercase tracking-wider h-11 px-6">
          <ArrowLeft className="mr-2 h-4 w-4" />
          RETURN TO COMMAND CENTER
        </Button>
      </Link>
    </div>
  );
}

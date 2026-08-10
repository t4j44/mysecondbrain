'use client';

import * as React from 'react';
import { ShieldAlert, RotateCcw } from 'lucide-react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#12081d] text-[#f7f4ea] font-sans antialiased flex items-center justify-center min-h-screen p-6">
        <div className="max-w-xl w-full border border-red-500/60 bg-[#0a0510] p-8 rounded-lg shadow-2xl text-center space-y-6">
          <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-red-600/20 border border-red-500 text-red-400 mx-auto">
            <ShieldAlert className="h-8 w-8" />
          </div>
          <div className="space-y-2">
            <span className="text-xs font-mono font-bold uppercase text-red-400 tracking-widest block">
              [ GLOBAL KERNEL PANIC // SYSTEM HALT ]
            </span>
            <h1 className="text-2xl font-extrabold text-white">
              Critical OS Application Failure
            </h1>
            <p className="text-sm text-red-200/80 max-w-md mx-auto">
              The root HTML shell encountered an unrecoverable exception during rendering.
            </p>
          </div>
          {error.digest && (
            <div className="font-mono text-xs text-red-400 bg-black/60 py-1.5 px-3 rounded border border-red-500/30">
              Error Digest: {error.digest}
            </div>
          )}
          <button
            onClick={() => reset()}
            className="inline-flex items-center justify-center rounded-md bg-[#00ff9d] text-[#0a0510] font-mono font-bold text-xs h-10 px-6 hover:bg-[#00e58d] transition-colors uppercase tracking-wider"
          >
            <RotateCcw className="mr-2 h-4 w-4" />
            REBOOT SYSTEM KERNEL
          </button>
        </div>
      </body>
    </html>
  );
}

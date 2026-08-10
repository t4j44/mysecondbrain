'use client';

import * as React from 'react';
import { ShieldAlert, RotateCcw, Terminal } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ErrorStateProps {
  title?: string;
  message?: string;
  error?: Error | { code?: string; message?: string; requestId?: string; request_id?: string };
  onRetry?: () => void;
}

export function ErrorState({
  title = 'OPERATIONAL COMMUNICATION FAILURE',
  message = 'The UI client encountered an unexpected state or API communication disruption.',
  error,
  onRetry,
}: ErrorStateProps) {
  const errObj = error as any;
  const errorCode = errObj?.code || 'ERR_SYSTEM';
  const errorMessage = errObj?.message || errObj?.toString() || message;
  const requestId = errObj?.requestId || errObj?.request_id;

  return (
    <div className="my-6 rounded-lg border border-destructive/60 bg-[#190610] p-6 shadow-[0_10px_30px_rgba(0,0,0,0.6)] font-sans">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between space-y-4 sm:space-y-0">
        <div className="flex items-start space-x-4">
          <div className="inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-destructive/20 border border-destructive text-red-400 shadow-sm">
            <ShieldAlert className="h-6 w-6" />
          </div>
          <div className="space-y-1">
            <div className="inline-block rounded px-1.5 py-0.2 text-[10px] font-mono font-bold uppercase bg-destructive/30 text-red-300 border border-red-500/30">
              [ ERROR CODE: {errorCode} ]
            </div>
            <h3 className="text-base font-bold text-[#f7f4ea]">
              {title}
            </h3>
            <p className="text-sm text-red-200/80 leading-relaxed max-w-xl">
              {errorMessage}
            </p>
          </div>
        </div>

        {onRetry && (
          <Button
            onClick={onRetry}
            variant="outline"
            className="shrink-0 border-red-500/40 text-red-200 hover:bg-destructive/20 hover:text-white font-mono text-xs"
          >
            <RotateCcw className="mr-2 h-3.5 w-3.5 animate-spin-once" />
            RETRY OPERATOR PROTOCOL
          </Button>
        )}
      </div>

      {requestId && (
        <div className="mt-4 border-t border-red-500/20 pt-3 flex items-center justify-between text-[11px] font-mono text-red-300/60">
          <span className="flex items-center">
            <Terminal className="h-3 w-3 mr-1.5" />
            FastAPI Tracing ID:
          </span>
          <span className="font-semibold text-red-300 select-all">{requestId}</span>
        </div>
      )}
    </div>
  );
}

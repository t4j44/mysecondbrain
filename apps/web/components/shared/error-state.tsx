'use client';

import { Button } from '@/components/ui/button';

interface ErrorStateProps {
  title?: string;
  message?: string;
  error?: Error | { code?: string; message?: string; requestId?: string; request_id?: string };
  onRetry?: () => void;
}
export function ErrorState({title='Could not load this page',message='The service is unavailable. Try again in a moment. Your records have not been removed.',error,onRetry}:ErrorStateProps) {
  const code=error&&'code' in error?error.code:undefined;
  const requestId=error&&'requestId' in error?error.requestId:error&&'request_id' in error?error.request_id:undefined;
  return <section role="alert" className="my-5 min-w-0 space-y-3 rounded-xl border border-destructive/50 bg-card p-4">
    <h2 className="text-lg font-semibold">{title}</h2><p className="text-base text-muted-foreground">{message}</p>
    {onRetry&&<Button onClick={onRetry} variant="outline">Try again</Button>}
    {(code||requestId)&&<details className="text-sm"><summary className="flex min-h-11 cursor-pointer items-center">Support details</summary><p className="break-all">{code?`Code: ${code}`:''}{requestId?` · Request: ${requestId}`:''}</p></details>}
  </section>;
}

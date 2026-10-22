import { ApiError } from '@/lib/api/errors';

export function RequestError({ error, onRetry }: { error: unknown; onRetry: () => void }) {
  return <section role="alert" className="space-y-3 rounded-xl border border-destructive/50 p-4">
    <h2 className="font-medium">Your saved context could not be loaded</h2>
    <p className="text-sm text-muted-foreground">This is a service error. It does not mean your records are empty. Try again in a moment.</p>
    <button type="button" className="min-h-11 rounded-lg border px-4" onClick={onRetry}>Try again</button>
    {error instanceof ApiError && <details className="text-sm"><summary className="flex min-h-11 cursor-pointer items-center">Support details</summary><p className="break-all">Code: {error.code} · HTTP {error.status}{error.requestId ? ` · Request: ${error.requestId}` : ''}</p></details>}
  </section>;
}

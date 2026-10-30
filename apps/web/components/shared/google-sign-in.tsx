'use client';

import * as React from 'react';
import { Loader2 } from 'lucide-react';

import { safeAuthReturnPath } from '@/lib/auth/redirect';
import { env } from '@/lib/env';
import { useToast } from '@/components/ui/use-toast';

type GoogleAuthSettings = { external?: { google?: boolean } };

/** Only offer OAuth when the managed Supabase Auth service advertises it. */
export function GoogleSignIn({ next = '/dashboard' }: { next?: string }) {
  const [isEnabled, setIsEnabled] = React.useState<boolean | null>(null);
  const [loading, setLoading] = React.useState(false);
  const { toast } = useToast();

  React.useEffect(() => {
    const controller = new AbortController();
    const check = async () => {
      try {
        const response = await fetch(`${env.NEXT_PUBLIC_SUPABASE_URL}/auth/v1/settings`, {
          headers: { apikey: env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY },
          cache: 'no-store',
          signal: controller.signal,
        });
        if (!response.ok) throw new Error('Provider settings unavailable');
        const settings = (await response.json()) as GoogleAuthSettings;
        setIsEnabled(settings.external?.google === true);
      } catch {
        if (!controller.signal.aborted) setIsEnabled(false);
      }
    };
    void check();
    return () => controller.abort();
  }, []);

  async function signInWithGoogle() {
    if (!isEnabled || loading) return;
    setLoading(true);
    try {
      const { createClient } = await import('@/lib/supabase/client');
      const supabase = createClient();
      const destination = safeAuthReturnPath(next);
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/callback?next=${encodeURIComponent(destination)}`,
        },
      });
      if (error) throw error;
      // Supabase redirects away to Google. Keep the loading state until navigation.
    } catch (error) {
      setLoading(false);
      toast({
        title: 'Google sign-in unavailable',
        description: error instanceof Error ? error.message : 'Please try email sign-in.',
        variant: 'destructive',
      });
    }
  }

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={() => void signInWithGoogle()}
        disabled={isEnabled !== true || loading}
        className="flex w-full min-h-[44px] items-center justify-center gap-3 rounded-xl border border-border bg-card px-4 py-2.5 font-medium text-foreground transition-colors hover:border-primary disabled:cursor-not-allowed disabled:opacity-60"
        aria-label="Continue with Google"
        data-testid="google-signin"
      >
        {loading ? <Loader2 className="h-4 w-4 animate-spin" /> :
          <span aria-hidden="true" className="text-lg font-bold">G</span>}
        Continue with Google
      </button>
      {isEnabled === false && (
        <p role="status" className="text-center text-sm text-muted-foreground">
          Google sign-in is awaiting provider setup. Email and password remain available.
        </p>
      )}
      {isEnabled === null && (
        <p role="status" className="text-center text-sm text-muted-foreground">
          Checking Google sign-in availability…
        </p>
      )}
    </div>
  );
}

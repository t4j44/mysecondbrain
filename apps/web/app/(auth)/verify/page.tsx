'use client';

import * as React from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { MailCheck, ArrowLeft, ShieldAlert, Loader2 } from 'lucide-react';
import { createClient } from '@/lib/supabase/client';
import { useToast } from '@/components/ui/use-toast';
import { Button } from '@/components/ui/button';

export default function VerifyPage() {
  const searchParams = useSearchParams();
  const email = searchParams.get('email') || '';
  const [sending, setSending] = React.useState(false);
  const [resent, setResent] = React.useState(false);
  const { toast } = useToast();

  async function resendConfirmation() {
    if (!email || sending || resent) return;
    setSending(true);
    try {
      const supabase = createClient();
      const { error } = await supabase.auth.resend({
        type: 'signup',
        email,
        options: { emailRedirectTo: `${window.location.origin}/callback` },
      });
      if (error) throw error;
      setResent(true);
      toast({ title: 'Confirmation requested', description: 'Check your inbox for the newest confirmation message.' });
    } catch (error) {
      toast({
        title: 'Unable to resend confirmation',
        description: error instanceof Error ? error.message : 'Please try again later.',
        variant: 'destructive',
      });
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="space-y-6 text-center">
      <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 border border-primary text-primary shadow-[0_0_30px_rgba(0,255,157,0.2)]">
        <MailCheck className="h-8 w-8" />
      </div>

      <div className="space-y-2">
        <h2 className="text-2xl font-extrabold tracking-tight text-foreground">
          Check your email
        </h2>
        <p className="text-sm text-muted-foreground leading-relaxed max-w-sm mx-auto">
          Look for a confirmation link in <span className="text-primary font-semibold">{email || 'your registered email'}</span>.
        </p>
      </div>

      <div className="rounded-lg border border-border bg-card p-4 text-left space-y-2">
        <div className="flex items-center space-x-2 text-xs font-mono text-muted-foreground">
          <ShieldAlert className="h-4 w-4 shrink-0" />
          <span>Confirm your email to continue</span>
        </div>
        <p className="text-xs text-muted-foreground leading-normal">
          Open the newest confirmation link, then return to sign in.
        </p>
      </div>

      <div className="pt-4 flex flex-col space-y-3">
        {email && (
          <Button
            type="button"
            onClick={() => void resendConfirmation()}
            disabled={sending || resent}
            data-testid="resend-confirmation"
            className="w-full font-mono text-xs"
          >
            {sending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
            {resent ? 'Confirmation requested — check email' : 'Resend confirmation email'}
          </Button>
        )}
        <p className="text-xs text-muted-foreground">
          If an email link expired, use only the newest message. Already confirmed? Return to sign in.
        </p>
          <Button asChild variant="outline" className="w-full text-sm"><Link href="/login">
            <ArrowLeft className="h-3 w-3 mr-2" />
            Return to sign in
          </Link></Button>
      </div>
    </div>
  );
}

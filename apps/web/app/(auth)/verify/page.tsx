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
      <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-[#00ff9d]/10 border border-[#00ff9d] text-[#00ff9d] shadow-[0_0_30px_rgba(0,255,157,0.2)]">
        <MailCheck className="h-8 w-8" />
      </div>

      <div className="space-y-2">
        <h2 className="text-2xl font-extrabold tracking-tight text-[#f7f4ea]">
          Verification Required
        </h2>
        <p className="text-sm text-muted-foreground leading-relaxed max-w-sm mx-auto">
          We have dispatched an identity validation link to <span className="font-mono text-[#00ff9d] font-semibold">{email || 'your registered email'}</span>.
        </p>
      </div>

      <div className="rounded-lg border border-border bg-[#0a0510] p-4 text-left space-y-2">
        <div className="flex items-center space-x-2 text-xs font-mono text-[#ffb800]">
          <ShieldAlert className="h-4 w-4 shrink-0" />
          <span>RLS SECURITY ENFORCED</span>
        </div>
        <p className="text-xs text-muted-foreground leading-normal">
          For your data isolation security, access to the multi-venture command center remains blocked until email ownership verification is confirmed.
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
            {resent ? 'CONFIRMATION REQUESTED — CHECK EMAIL' : 'RESEND CONFIRMATION EMAIL'}
          </Button>
        )}
        <p className="text-xs text-muted-foreground">
          If an email link expired, use only the newest message. Already confirmed? Return to sign in.
        </p>
        <Link href="/login" className="w-full">
          <Button variant="outline" className="w-full font-mono text-xs">
            <ArrowLeft className="h-3 w-3 mr-2" />
            RETURN TO SIGN IN
          </Button>
        </Link>
      </div>
    </div>
  );
}

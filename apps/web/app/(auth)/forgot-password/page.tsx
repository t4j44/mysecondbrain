'use client';

import * as React from 'react';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, ArrowLeft, KeyRound } from 'lucide-react';

import { createClient } from '@/lib/supabase/client';
import { forgotPasswordSchema, type ForgotPasswordFormValues } from '@/lib/validation/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';

export default function ForgotPasswordPage() {
  const { toast } = useToast();
  const [isLoading, setIsLoading] = React.useState(false);
  const [isSubmitted, setIsSubmitted] = React.useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordFormValues>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: {
      email: '',
    },
  });

  async function onSubmit(data: ForgotPasswordFormValues) {
    setIsLoading(true);
    const supabase = createClient();

    const { error } = await supabase.auth.resetPasswordForEmail(data.email, {
      redirectTo: `${window.location.origin}/reset-password`,
    });

    setIsLoading(false);

    if (error) {
      toast({
        title: 'RECOVERY ERROR',
        description: error.message || 'Failed to dispatch passkey recovery instructions.',
        variant: 'destructive',
      });
      return;
    }

    setIsSubmitted(true);
    toast({
      title: 'RECOVERY INSTRUCTIONS SENT',
      description: 'Check your operator email inbox for the passkey reset link.',
    });
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <div className="inline-flex items-center space-x-1 rounded px-2 py-0.5 text-[11px] font-mono font-semibold bg-[#251238] text-[#00ff9d] border border-[#00ff9d]/30 uppercase tracking-widest">
          <KeyRound className="h-3 w-3 mr-1" />
          <span>Credential Recovery</span>
        </div>
        <h2 className="text-3xl font-extrabold tracking-tight text-[#f7f4ea]">
          Reset Passkey
        </h2>
        <p className="text-sm text-muted-foreground">
          Enter your registered operator email to receive access restoration instructions.
        </p>
      </div>

      {isSubmitted ? (
        <div className="rounded-lg border border-[#00ff9d]/40 bg-[#0a0510] p-6 text-center space-y-4 shadow-[0_0_25px_rgba(0,255,157,0.1)]">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-[#00ff9d]/10 text-[#00ff9d]">
            <KeyRound className="h-6 w-6" />
          </div>
          <h3 className="text-lg font-bold text-[#f7f4ea]">Recovery Link Dispatched</h3>
          <p className="text-sm text-muted-foreground leading-relaxed">
            If an account matching that email address exists in our RLS registry, a secure reset protocol link has been transmitted to your inbox.
          </p>
          <div className="pt-2">
            <Link href="/login">
              <Button variant="outline" className="w-full font-mono text-xs">
                RETURN TO SIGN IN
              </Button>
            </Link>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email" className="text-xs font-mono uppercase text-muted-foreground">
              Email Address
            </Label>
            <Input
              id="email"
              type="email"
              placeholder="taj@tajssecondbrain.ai"
              disabled={isLoading}
              {...register('email')}
            />
            {errors.email && (
              <p className="text-xs font-mono text-destructive">{errors.email.message}</p>
            )}
          </div>

          <Button type="submit" className="w-full h-11 font-mono tracking-wider text-sm font-bold mt-2" disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                DISPATCHING RECOVERY LINK...
              </>
            ) : (
              'SEND RESET PROTOCOL'
            )}
          </Button>

          <div className="pt-2 text-center">
            <Link href="/login" className="inline-flex items-center text-xs font-mono text-muted-foreground hover:text-[#00ff9d] transition-colors">
              <ArrowLeft className="h-3 w-3 mr-1.5" />
              Return to Operator Sign In
            </Link>
          </div>
        </form>
      )}
    </div>
  );
}

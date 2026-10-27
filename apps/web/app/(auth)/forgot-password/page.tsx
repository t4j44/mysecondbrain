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
        title: 'Could not request reset',
        description: error.message || 'Could not request a password reset. Please try again.',
        variant: 'destructive',
      });
      return;
    }

    setIsSubmitted(true);
    toast({
      title: 'Reset link requested',
      description: 'Check your email for a password reset link.',
    });
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <div className="inline-flex items-center space-x-1 rounded px-2 py-0.5 text-[11px] font-mono font-semibold bg-primary/10 text-primary border border-primary/30 uppercase tracking-widest">
          <KeyRound className="h-3 w-3 mr-1" />
          <span>Credential Recovery</span>
        </div>
        <h2 className="text-3xl font-extrabold tracking-tight text-foreground">
          Reset password
        </h2>
        <p className="text-sm text-muted-foreground">
          Enter your email to request a password reset link.
        </p>
      </div>

      {isSubmitted ? (
        <div className="rounded-lg border border-primary/40 bg-card p-6 text-center space-y-4 shadow-[0_0_25px_rgba(0,255,157,0.1)]">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
            <KeyRound className="h-6 w-6" />
          </div>
          <h3 className="text-lg font-bold text-foreground">Check your email</h3>
          <p className="text-sm text-muted-foreground leading-relaxed">
            If an account with that email exists, you will receive a password reset link.
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
                Requesting reset link…
              </>
            ) : (
              'SEND RESET PROTOCOL'
            )}
          </Button>

          <div className="pt-2 text-center">
            <Link href="/login" className="inline-flex items-center text-xs font-mono text-muted-foreground hover:text-primary transition-colors">
              <ArrowLeft className="h-3 w-3 mr-1.5" />
              Return to sign in
            </Link>
          </div>
        </form>
      )}
    </div>
  );
}

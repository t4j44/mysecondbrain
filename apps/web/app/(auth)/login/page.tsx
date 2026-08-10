'use client';

import * as React from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, ArrowRight, KeyRound } from 'lucide-react';

import { createClient } from '@/lib/supabase/client';
import { loginSchema, type LoginFormValues } from '@/lib/validation/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = React.useState(false);
  const redirectUrl = searchParams.get('redirect') || '/dashboard';

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
      rememberMe: false,
    },
  });

  async function onSubmit(data: LoginFormValues) {
    setIsLoading(true);
    const supabase = createClient();

    const { error } = await supabase.auth.signInWithPassword({
      email: data.email,
      password: data.password,
    });

    setIsLoading(false);

    if (error) {
      toast({
        title: 'AUTHENTICATION REJECTED',
        description: error.message || 'Invalid credentials provided for operator login.',
        variant: 'destructive',
      });
      return;
    }

    toast({
      title: 'ACCESS GRANTED',
      description: 'Redirecting operator to Command Center...',
    });

    router.push(redirectUrl);
    router.refresh();
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <div className="inline-block rounded px-2 py-0.5 text-[11px] font-mono font-semibold bg-[#251238] text-[#00ff9d] border border-[#00ff9d]/30 uppercase tracking-widest">
          Operator Authentication
        </div>
        <h2 className="text-3xl font-extrabold tracking-tight text-[#f7f4ea]">
          Sign in to Terminal
        </h2>
        <p className="text-sm text-muted-foreground">
          Enter your operator email and passkey to access your ventures.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email" className="text-xs font-mono uppercase text-muted-foreground">
            Email Address
          </Label>
          <Input
            id="email"
            type="email"
            placeholder="taj@tajssecondbrain.ai"
            autoComplete="email"
            disabled={isLoading}
            {...register('email')}
          />
          {errors.email && (
            <p className="text-xs font-mono text-destructive">{errors.email.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="password" className="text-xs font-mono uppercase text-muted-foreground">
              Security Passkey
            </Label>
            <Link
              href="/forgot-password"
              className="text-xs font-mono text-[#00ff9d] hover:underline"
            >
              Forgot passkey?
            </Link>
          </div>
          <Input
            id="password"
            type="password"
            placeholder="••••••••••••"
            autoComplete="current-password"
            disabled={isLoading}
            {...register('password')}
          />
          {errors.password && (
            <p className="text-xs font-mono text-destructive">{errors.password.message}</p>
          )}
        </div>

        <Button type="submit" className="w-full h-11 font-mono tracking-wider text-sm font-bold mt-2" disabled={isLoading}>
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              AUTHENTICATING...
            </>
          ) : (
            <>
              INITIALIZE SESSION
              <ArrowRight className="ml-2 h-4 w-4" />
            </>
          )}
        </Button>
      </form>

      <div className="relative my-6">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-border" />
        </div>
        <div className="relative flex justify-center text-xs uppercase font-mono">
          <span className="bg-[#12081d] px-2 text-muted-foreground">Or access via</span>
        </div>
      </div>

      <div className="text-center text-sm text-muted-foreground font-mono">
        Need operator authorization?{' '}
        <Link href="/signup" className="text-[#00ff9d] hover:underline font-semibold font-sans">
          Request system credentials
        </Link>
      </div>
    </div>
  );
}

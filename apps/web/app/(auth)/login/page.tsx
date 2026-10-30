'use client';

import * as React from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, ArrowRight, KeyRound } from 'lucide-react';

import { GoogleSignIn } from '@/components/shared/google-sign-in';
import { safeAuthReturnPath } from '@/lib/auth/redirect';
import { loginSchema, type LoginFormInput, type LoginFormValues } from '@/lib/validation/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = React.useState(false);
  const signingIn = React.useRef(false);
  const redirectUrl = safeAuthReturnPath(searchParams.get('redirect'));

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormInput, unknown, LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
      rememberMe: false,
    },
  });

  async function onSubmit(data: LoginFormValues) {
    if (signingIn.current) return;
    signingIn.current = true;
    setIsLoading(true);
    try {
      // The auth SDK is needed on submission, not for reading the login form.
      const { createClient } = await import('@/lib/supabase/client');
      const { error } = await createClient().auth.signInWithPassword({email:data.email,password:data.password});
      if (error) throw error;
      router.push(redirectUrl);
      router.refresh();
    } catch (error) {
      toast({
        title: 'Could not sign in',
        description: error instanceof Error ? error.message : 'Check your connection, email and password, then try again.',
        variant: 'destructive',
      });
    } finally {
      signingIn.current = false;
      setIsLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <div className="inline-block rounded px-2 py-0.5 text-sm font-semibold bg-primary/10 text-primary border border-primary/30 tracking-widest">
          Welcome back
        </div>
        <h2 className="text-3xl font-extrabold tracking-tight text-foreground">
          Sign in
        </h2>
        <p className="text-sm text-muted-foreground">
          Use your email and password to open Second Brain.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email" className="text-sm text-muted-foreground">
            Email Address
          </Label>
          <Input
            id="email"
            type="email"
            placeholder="you@example.com"
            autoComplete="email"
            disabled={isLoading}
            {...register('email')}
          />
          {errors.email && (
            <p className="text-sm text-destructive">{errors.email.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="password" className="text-sm text-muted-foreground">
              Password
            </Label>
            <Link
              href="/forgot-password"
              prefetch={false}
              className="inline-flex min-h-11 items-center text-sm text-primary hover:underline"
            >
              Forgot password?
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
            <p className="text-sm text-destructive">{errors.password.message}</p>
          )}
        </div>

        <Button type="submit" className="w-full h-11 tracking-wider text-sm font-bold mt-2" disabled={isLoading}>
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Signing in…
            </>
          ) : (
            <>
              Sign in
              <ArrowRight className="ml-2 h-4 w-4" />
            </>
          )}
        </Button>
      </form>

      <div className="relative my-6">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-border" />
        </div>
        <div className="relative flex justify-center text-sm ">
          <span className="bg-background px-2 text-muted-foreground">Or continue with</span>
        </div>
      </div>

      <GoogleSignIn next={redirectUrl} />

      <div className="text-center text-sm text-muted-foreground ">
        New to Second Brain?{' '}
        <Link href="/signup" prefetch={false} className="inline-flex min-h-11 items-center text-primary hover:underline font-semibold font-sans">
          Create an account
        </Link>
      </div>
    </div>
  );
}

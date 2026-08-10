'use client';

import * as React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, ArrowRight, ShieldCheck } from 'lucide-react';

import { createClient } from '@/lib/supabase/client';
import { signupSchema, type SignupFormValues } from '@/lib/validation/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';

export default function SignupPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = React.useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SignupFormValues>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      fullName: '',
      email: '',
      password: '',
    },
  });

  async function onSubmit(data: SignupFormValues) {
    setIsLoading(true);
    const supabase = createClient();

    const { error } = await supabase.auth.signUp({
      email: data.email,
      password: data.password,
      options: {
        data: {
          full_name: data.fullName,
        },
        emailRedirectTo: `${window.location.origin}/callback`,
      },
    });

    setIsLoading(false);

    if (error) {
      toast({
        title: 'REGISTRATION ERROR',
        description: error.message || 'Unable to establish new operator identity.',
        variant: 'destructive',
      });
      return;
    }

    toast({
      title: 'VERIFICATION REQUIRED',
      description: 'Verification check sent to operator email address.',
    });

    router.push(`/verify?email=${encodeURIComponent(data.email)}`);
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <div className="inline-flex items-center space-x-1.5 rounded px-2 py-0.5 text-[11px] font-mono font-semibold bg-[#251238] text-[#00ff9d] border border-[#00ff9d]/30 uppercase tracking-widest">
          <ShieldCheck className="h-3 w-3" />
          <span>Operator Registration</span>
        </div>
        <h2 className="text-3xl font-extrabold tracking-tight text-[#f7f4ea]">
          Request Credentials
        </h2>
        <p className="text-sm text-muted-foreground">
          Create an isolated RLS profile to initialize your multi-venture OS.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="fullName" className="text-xs font-mono uppercase text-muted-foreground">
            Full Name / Designation
          </Label>
          <Input
            id="fullName"
            placeholder="Taj"
            disabled={isLoading}
            {...register('fullName')}
          />
          {errors.fullName && (
            <p className="text-xs font-mono text-destructive">{errors.fullName.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="email" className="text-xs font-mono uppercase text-muted-foreground">
            Email Address
          </Label>
          <Input
            id="email"
            type="email"
            placeholder="operator@tajssecondbrain.ai"
            autoComplete="email"
            disabled={isLoading}
            {...register('email')}
          />
          {errors.email && (
            <p className="text-xs font-mono text-destructive">{errors.email.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="password" className="text-xs font-mono uppercase text-muted-foreground">
            Security Passkey
          </Label>
          <Input
            id="password"
            type="password"
            placeholder="10+ chars (Uppercase, symbol & number)"
            autoComplete="new-password"
            disabled={isLoading}
            {...register('password')}
          />
          {errors.password && (
            <p className="text-xs font-mono text-destructive">{errors.password.message}</p>
          )}
        </div>

        <Button type="submit" className="w-full h-11 font-mono tracking-wider text-sm font-bold mt-4" disabled={isLoading}>
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              PROVISIONING IDENTITY...
            </>
          ) : (
            <>
              PROVISION WORKSPACE
              <ArrowRight className="ml-2 h-4 w-4" />
            </>
          )}
        </Button>
      </form>

      <div className="text-center text-sm text-muted-foreground font-mono pt-4">
        Already registered?{' '}
        <Link href="/login" className="text-[#00ff9d] hover:underline font-semibold font-sans">
          Sign in to existing terminal
        </Link>
      </div>
    </div>
  );
}

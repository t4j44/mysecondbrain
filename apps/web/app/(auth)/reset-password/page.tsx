'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, KeyRound, CheckCircle2 } from 'lucide-react';

import { createClient } from '@/lib/supabase/client';
import { resetPasswordSchema, type ResetPasswordFormValues } from '@/lib/validation/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';

export default function ResetPasswordPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = React.useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordFormValues>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      password: '',
      confirmPassword: '',
    },
  });

  async function onSubmit(data: ResetPasswordFormValues) {
    setIsLoading(true);
    const supabase = createClient();

    const { error } = await supabase.auth.updateUser({
      password: data.password,
    });

    setIsLoading(false);

    if (error) {
      toast({
        title: 'PASSKEY UPDATE FAILED',
        description: error.message || 'Could not commit new passkey to secure enclave.',
        variant: 'destructive',
      });
      return;
    }

    toast({
      title: 'CREDENTIALS UPDATED',
      description: 'Your operator passkey has been successfully reset.',
    });

    router.push('/login');
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <div className="inline-flex items-center space-x-1.5 rounded px-2 py-0.5 text-[11px] font-mono font-semibold bg-[#251238] text-[#00ff9d] border border-[#00ff9d]/30 uppercase tracking-widest">
          <KeyRound className="h-3 w-3" />
          <span>Security Enclave</span>
        </div>
        <h2 className="text-3xl font-extrabold tracking-tight text-[#f7f4ea]">
          Set New Passkey
        </h2>
        <p className="text-sm text-muted-foreground">
          Establish a high-entropy passkey to finalize account recovery.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="password" className="text-xs font-mono uppercase text-muted-foreground">
            New Passkey
          </Label>
          <Input
            id="password"
            type="password"
            placeholder="••••••••••••"
            disabled={isLoading}
            {...register('password')}
          />
          {errors.password && (
            <p className="text-xs font-mono text-destructive">{errors.password.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="confirmPassword" className="text-xs font-mono uppercase text-muted-foreground">
            Confirm New Passkey
          </Label>
          <Input
            id="confirmPassword"
            type="password"
            placeholder="••••••••••••"
            disabled={isLoading}
            {...register('confirmPassword')}
          />
          {errors.confirmPassword && (
            <p className="text-xs font-mono text-destructive">{errors.confirmPassword.message}</p>
          )}
        </div>

        <Button type="submit" className="w-full h-11 font-mono tracking-wider text-sm font-bold mt-2" disabled={isLoading}>
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              UPDATING SECURITY CREDENTIALS...
            </>
          ) : (
            <>
              COMMIT NEW PASSKEY
              <CheckCircle2 className="ml-2 h-4 w-4" />
            </>
          )}
        </Button>
      </form>
    </div>
  );
}

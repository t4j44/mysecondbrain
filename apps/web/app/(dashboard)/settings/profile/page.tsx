'use client';

import * as React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { SectionHeader } from '@/components/shared/section-header';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';
import { profileSettingsSchema, type ProfileSettingsValues } from '@/lib/validation/settings';
import { Loader2, Save, UserCheck } from 'lucide-react';
import { createClient } from '@/lib/supabase/client';

export default function SettingsProfilePage() {
  const { toast } = useToast();
  const [isLoading, setIsLoading] = React.useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<ProfileSettingsValues>({
    resolver: zodResolver(profileSettingsSchema),
    defaultValues: {
      fullName: 'Taj',
      bio: 'Visionary founder organizing multiple high-growth technology ventures.',
      timezone: 'UTC',
    },
  });

  React.useEffect(() => {
    async function loadUser() {
      const supabase = createClient();
      const { data: { user } } = await supabase.auth.getUser();
      if (user && user.user_metadata?.full_name) {
        setValue('fullName', user.user_metadata.full_name);
      }
    }
    loadUser();
  }, [setValue]);

  async function onSubmit(data: ProfileSettingsValues) {
    setIsLoading(true);
    const supabase = createClient();
    const { error } = await supabase.auth.updateUser({
      data: { full_name: data.fullName, bio: data.bio, timezone: data.timezone },
    });
    setIsLoading(false);

    if (error) {
      toast({ title: 'PROFILE UPDATE ERROR', description: error.message, variant: 'destructive' });
      return;
    }

    toast({
      title: 'OPERATOR IDENTITY SYMMED',
      description: 'Your profile changes have been committed to the Supabase auth registry.',
    });
  }

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Operator Profile Configuration"
        description="Manage your display credentials, executive bio, and active working timezone."
      />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5 max-w-lg">
        <div className="space-y-2">
          <Label htmlFor="fullName" className="text-xs font-mono uppercase text-muted-foreground">
            Full Name / Title
          </Label>
          <Input id="fullName" disabled={isLoading} {...register('fullName')} />
          {errors.fullName && <p className="text-xs font-mono text-destructive">{errors.fullName.message}</p>}
        </div>

        <div className="space-y-2">
          <Label htmlFor="bio" className="text-xs font-mono uppercase text-muted-foreground">
            Executive Bio & Context
          </Label>
          <textarea
            id="bio"
            rows={3}
            disabled={isLoading}
            {...register('bio')}
            className="flex w-full rounded-md border border-border bg-[#0e0716] px-3 py-2 text-sm text-[#f7f4ea] placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-[#00ff9d] transition-all font-sans"
          />
          {errors.bio && <p className="text-xs font-mono text-destructive">{errors.bio.message}</p>}
        </div>

        <div className="space-y-2">
          <Label htmlFor="timezone" className="text-xs font-mono uppercase text-muted-foreground">
            Operational Timezone
          </Label>
          <select
            id="timezone"
            disabled={isLoading}
            {...register('timezone')}
            className="h-10 w-full rounded-md border border-border bg-[#0e0716] px-3 py-2 text-sm text-[#f7f4ea] focus:outline-none focus:ring-2 focus:ring-[#00ff9d] font-sans"
          >
            <option value="UTC">UTC (Universal Time Coordinated)</option>
            <option value="America/New_York">EST (Eastern Standard Time)</option>
            <option value="America/Los_Angeles">PST (Pacific Standard Time)</option>
            <option value="Europe/London">GMT (Greenwich Mean Time)</option>
            <option value="Asia/Tokyo">JST (Japan Standard Time)</option>
          </select>
          {errors.timezone && <p className="text-xs font-mono text-destructive">{errors.timezone.message}</p>}
        </div>

        <div className="pt-4">
          <Button type="submit" className="font-mono text-xs font-bold uppercase tracking-wider px-6" disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                COMMITTING...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                SAVE PROFILE PROTOCOLS
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}

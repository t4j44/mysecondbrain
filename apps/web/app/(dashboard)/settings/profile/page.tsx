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
import { Loader2, Save } from 'lucide-react';
import { createClient } from '@/lib/supabase/client';

export default function SettingsProfilePage() {
  const { toast } = useToast();
  const [isLoading, setIsLoading] = React.useState(false);
  const [isReady, setIsReady] = React.useState(false);
  const [loadError, setLoadError] = React.useState('');

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ProfileSettingsValues>({
    resolver: zodResolver(profileSettingsSchema),
    defaultValues: {
      fullName: '',
      bio: '',
      timezone: 'UTC',
    },
  });

  React.useEffect(() => {
    let active = true;
    async function loadUser() {
      try {
        const { data: { user }, error } = await createClient().auth.getUser();
        if (error || !user) throw new Error('Profile unavailable');
        if (!active) return;
        const saved = user.user_metadata;
        reset({ fullName: typeof saved?.full_name === 'string' ? saved.full_name : '',
          bio: typeof saved?.bio === 'string' ? saved.bio : '',
          timezone: typeof saved?.timezone === 'string' && saved.timezone ? saved.timezone : Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC' });
        setIsReady(true);
      } catch {
        if (active) setLoadError('Your profile could not be loaded. Reload this page to try again.');
      }
    }
    void loadUser();
    return () => { active = false; };
  }, [reset]);

  async function onSubmit(data: ProfileSettingsValues) {
    if (!isReady) return;
    setIsLoading(true);
    try {
      const { error } = await createClient().auth.updateUser({
        data: { full_name: data.fullName, bio: data.bio, timezone: data.timezone },
      });
      if (error) throw error;
      toast({ title: 'Profile saved', description: 'Your name, bio and timezone have been updated.' });
    } catch {
      toast({ title: 'Profile not saved', description: 'Your changes are still here. Check your connection and try again.', variant: 'destructive' });
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Your profile"
        description="Update your name, a short bio and your timezone."
      />
      {!isReady && <p role={loadError ? 'alert' : 'status'}>{loadError || 'Loading your profile...'}</p>}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5 max-w-lg">
        <div className="space-y-2">
          <Label htmlFor="fullName" className="text-xs font-mono uppercase text-muted-foreground">
            Full name
          </Label>
          <Input id="fullName" disabled={isLoading || !isReady} {...register('fullName')} />
          {errors.fullName && <p className="text-xs font-mono text-destructive">{errors.fullName.message}</p>}
        </div>

        <div className="space-y-2">
          <Label htmlFor="bio" className="text-xs font-mono uppercase text-muted-foreground">
            Bio
          </Label>
          <textarea
            id="bio"
            rows={3}
            disabled={isLoading || !isReady}
            {...register('bio')}
            className="flex w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-all font-sans"
          />
          {errors.bio && <p className="text-xs font-mono text-destructive">{errors.bio.message}</p>}
        </div>

        <div className="space-y-2">
          <Label htmlFor="timezone" className="text-xs font-mono uppercase text-muted-foreground">
            Timezone
          </Label>
          <Input
            id="timezone"
            disabled={isLoading || !isReady}
            {...register('timezone')}
            placeholder="Europe/London"
            aria-describedby="timezone-help"
          />
          <p id="timezone-help" className="text-sm text-muted-foreground">Use a city timezone, such as Europe/London or America/New_York. Reminder preferences are set separately in Connections.</p>
          {errors.timezone && <p className="text-xs font-mono text-destructive">{errors.timezone.message}</p>}
        </div>

        <div className="pt-4">
          <Button type="submit" disabled={isLoading || !isReady}>
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Save profile
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}

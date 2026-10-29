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

const COMMON_TIMEZONES = [
  ['UTC', 'UTC'],
  ['America/New_York', 'New York'],
  ['America/Los_Angeles', 'Los Angeles'],
  ['Europe/London', 'London'],
  ['Asia/Dhaka', 'Dhaka'],
  ['Asia/Singapore', 'Singapore'],
  ['Asia/Tokyo', 'Tokyo'],
] as const;

export default function SettingsProfilePage() {
  const { toast } = useToast();
  const [loadState, setLoadState] = React.useState<'loading' | 'ready' | 'error'>('loading');
  const [saving, setSaving] = React.useState(false);
  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm<ProfileSettingsValues>({
    resolver: zodResolver(profileSettingsSchema),
    defaultValues: { fullName: '', bio: '', timezone: 'UTC' },
  });

  React.useEffect(() => {
    let active = true;
    async function loadUser() {
      try {
        const { data, error } = await createClient().auth.getUser();
        if (error || !data.user) throw new Error('Could not load your account.');
        if (!active) return;
        const metadata = data.user.user_metadata || {};
        reset({
          fullName: typeof metadata.full_name === 'string' ? metadata.full_name : '',
          bio: typeof metadata.bio === 'string' ? metadata.bio : '',
          timezone: typeof metadata.timezone === 'string' && metadata.timezone
            ? metadata.timezone : 'UTC',
        });
        setLoadState('ready');
      } catch {
        if (!active) return;
        setLoadState('error');
      }
    }
    void loadUser();
    return () => { active = false; };
  }, [reset]);

  async function onSubmit(data: ProfileSettingsValues) {
    if (loadState !== 'ready' || saving) return;
    setSaving(true);
    try {
      const { error } = await createClient().auth.updateUser({
        data: {
          full_name: data.fullName,
          bio: data.bio ?? '',
          timezone: data.timezone,
        },
      });
      if (error) throw error;
      toast({ title: 'Profile saved', description: 'Your changes have been saved.' });
    } catch {
      toast({ title: 'Could not save profile', description: 'Please try again.', variant: 'destructive' });
    } finally {
      setSaving(false);
    }
  }

  const selectedTimezone = watch('timezone');
  const timezoneKnown = COMMON_TIMEZONES.some(([value]) => value === selectedTimezone);
  const disabled = loadState !== 'ready' || saving;

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Your profile"
        description="Manage your name, bio, and time zone for reminders and scheduling."
      />

      {loadState === 'loading' && <p role="status" className="text-sm text-muted-foreground">Loading your profile…</p>}
      {loadState === 'error' && (
        <div role="alert" className="space-y-2 text-sm">
          <p>We couldn't load your saved profile. Nothing has been changed.</p>
          <Button type="button" variant="outline" onClick={() => window.location.reload()}>Retry loading</Button>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="max-w-lg space-y-5">
        <div className="space-y-2">
          <Label htmlFor="fullName">Full name</Label>
          <Input id="fullName" disabled={disabled} autoComplete="name" {...register('fullName')} />
          {errors.fullName && <p className="text-sm text-destructive">{errors.fullName.message}</p>}
        </div>

        <div className="space-y-2">
          <Label htmlFor="bio">Bio (optional)</Label>
          <textarea
            id="bio"
            rows={3}
            disabled={disabled}
            {...register('bio')}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
          />
          {errors.bio && <p className="text-sm text-destructive">{errors.bio.message}</p>}
        </div>

        <div className="space-y-2">
          <Label htmlFor="timezone">Time zone</Label>
          <select
            id="timezone"
            disabled={disabled}
            {...register('timezone')}
            className="h-11 w-full rounded-md border border-input bg-background px-3 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
          >
            {!timezoneKnown && selectedTimezone && (
              <option value={selectedTimezone}>{selectedTimezone} (saved)</option>
            )}
            {COMMON_TIMEZONES.map(([value, name]) => (
              <option key={value} value={value}>{name} ({value})</option>
            ))}
          </select>
          {errors.timezone && <p className="text-sm text-destructive">{errors.timezone.message}</p>}
        </div>

        <Button type="submit" disabled={disabled}>
          {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
          {saving ? 'Saving…' : 'Save profile'}
        </Button>
      </form>
    </div>
  );
}

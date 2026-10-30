import { z } from 'zod';

export const profileSettingsSchema = z.object({
  fullName: z.string().min(2, { message: 'Full name must be at least 2 characters long.' }),
  bio: z.string().max(300, { message: 'Bio cannot exceed 300 characters.' }).optional(),
  timezone: z.string().trim().min(1, { message: 'Enter your timezone.' }).refine(value => {
    try { new Intl.DateTimeFormat('en', { timeZone: value }); return true; } catch { return false; }
  }, { message: 'Use a valid timezone, such as Europe/London.' }),
});

export const appearanceSettingsSchema = z.object({
  theme: z.enum(['dark', 'light', 'system']),
  terminalDensity: z.enum(['compact', 'standard', 'comfortable']),
});

export type ProfileSettingsValues = z.infer<typeof profileSettingsSchema>;
export type AppearanceSettingsValues = z.infer<typeof appearanceSettingsSchema>;

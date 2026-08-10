import { z } from 'zod';

export const profileSettingsSchema = z.object({
  fullName: z.string().min(2, { message: 'Full name must be at least 2 characters long.' }),
  bio: z.string().max(300, { message: 'Bio cannot exceed 300 characters.' }).optional(),
  timezone: z.string().min(1, { message: 'Please select a working timezone.' }),
});

export const appearanceSettingsSchema = z.object({
  theme: z.enum(['dark', 'light', 'system']),
  terminalDensity: z.enum(['compact', 'standard', 'comfortable']),
});

export type ProfileSettingsValues = z.infer<typeof profileSettingsSchema>;
export type AppearanceSettingsValues = z.infer<typeof appearanceSettingsSchema>;

import { describe, expect, it } from 'vitest';
import { zodResolver } from '@hookform/resolvers/zod';
import { loginSchema, signupSchema, forgotPasswordSchema, resetPasswordSchema } from '@/lib/validation/auth';
import { profileSettingsSchema } from '@/lib/validation/settings';

const options = { criteriaMode: 'firstError' as const, shouldUseNativeValidation: false, fields: {} };

describe('patched Zod and form resolver integration', () => {
  it('applies the remember-me default without changing valid credentials', async () => {
    const result = await zodResolver(loginSchema)({ email: 'fixture@example.invalid', password: 'synthetic password' }, undefined, options);
    expect(result.errors).toEqual({});
    expect(result.values).toEqual({ email: 'fixture@example.invalid', password: 'synthetic password', rememberMe: false });
  });
  it('returns field errors instead of throwing on invalid login input', async () => {
    const result = await zodResolver(loginSchema)({ email: 'invalid', password: '' }, undefined, options);
    expect(result.values).toEqual({});
    expect(result.errors.email?.message).toBe('Please enter a valid email address.');
    expect(result.errors.password?.message).toBe('Please enter your password.');
  });
  it('keeps signup constraints and recovery-email validation', async () => {
    const result = await zodResolver(signupSchema)({ fullName: 'A', email: 'invalid', password: 'short' }, undefined, options);
    expect(Object.keys(result.errors).sort()).toEqual(['email', 'fullName', 'password']);
    expect(forgotPasswordSchema.safeParse({ email: 'invalid' }).success).toBe(false);
  });
  it('puts password mismatch on the confirmation field', async () => {
    const result = await zodResolver(resetPasswordSchema)({ password: 'Synthetic123!', confirmPassword: 'Different123!' }, undefined, options);
    expect(result.errors.confirmPassword?.message).toBe("Passwords don't match.");
  });
  it('retains profile length bounds', async () => {
    const result = await zodResolver(profileSettingsSchema)({ fullName: 'Fixture', bio: 'x'.repeat(301), timezone: 'UTC' }, undefined, options);
    expect(result.errors.bio?.message).toBe('Bio cannot exceed 300 characters.');
  });
});

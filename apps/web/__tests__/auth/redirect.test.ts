import { describe, expect, it } from 'vitest';
import { safeAuthReturnPath } from '@/lib/auth/redirect';

describe('auth callback safe return paths', () => {
  it('defaults to the dashboard', () => {
    expect(safeAuthReturnPath(null)).toBe('/dashboard');
    expect(safeAuthReturnPath('')).toBe('/dashboard');
  });

  it('preserves same-origin application paths and query strings', () => {
    expect(safeAuthReturnPath('/dashboard')).toBe('/dashboard');
    expect(safeAuthReturnPath('/people?view=recent')).toBe('/people?view=recent');
    expect(safeAuthReturnPath('/settings#privacy')).toBe('/settings#privacy');
  });

  it.each([
    'https://attacker.invalid/collect',
    '//attacker.invalid/collect',
    '@attacker.invalid',
    '/\\attacker.invalid',
    'javascript:alert(1)',
    ' /dashboard',
    '/dashboard\nSet-Cookie: x',
  ])('rejects untrusted return target %j', (value) => {
    expect(safeAuthReturnPath(value)).toBe('/dashboard');
  });
});

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { getCurrentSession, getCurrentUser } from '@/lib/auth/session';

// Mock server Supabase client creation
const mockGetUser = vi.fn();
const mockGetSession = vi.fn();

vi.mock('@/lib/supabase/server', () => ({
  createClient: () => ({
    auth: {
      getUser: mockGetUser,
      getSession: mockGetSession,
    },
  }),
}));

describe('Supabase Authentication Session Utilities', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('getCurrentSession returns valid session when authenticated', async () => {
    const fakeUser = { id: 'operator-001', email: 'taj@tajssecondbrain.ai' };
    const fakeSession = { access_token: 'valid.jwt.token', user: fakeUser };

    mockGetSession.mockResolvedValueOnce({ data: { session: fakeSession }, error: null });

    const result = await getCurrentSession();

    expect(result).toEqual(fakeSession);
    expect(mockGetSession).toHaveBeenCalledTimes(1);
  });

  it('getCurrentUser returns user object when verified', async () => {
    const fakeUser = { id: 'operator-001', email: 'taj@tajssecondbrain.ai' };
    mockGetUser.mockResolvedValueOnce({ data: { user: fakeUser }, error: null });

    const user = await getCurrentUser();

    expect(user).toEqual(fakeUser);
    expect(mockGetUser).toHaveBeenCalledTimes(1);
  });

  it('returns null when session or user query fails', async () => {
    mockGetSession.mockResolvedValueOnce({ data: { session: null }, error: new Error('Session expired') });
    mockGetUser.mockResolvedValueOnce({ data: { user: null }, error: new Error('User missing') });

    const session = await getCurrentSession();
    const user = await getCurrentUser();

    expect(session).toBeNull();
    expect(user).toBeNull();
  });
});

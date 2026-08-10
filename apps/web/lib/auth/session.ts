import { createClient } from '@/lib/supabase/server';
import { redirect } from 'next/navigation';
import type { User, Session } from '@supabase/supabase-js';

export async function getCurrentSession(): Promise<Session | null> {
  const supabase = createClient();
  const { data: { session }, error } = await supabase.auth.getSession();
  if (error || !session) {
    return null;
  }
  return session;
}

export async function getCurrentUser(): Promise<User | null> {
  const supabase = createClient();
  const { data: { user }, error } = await supabase.auth.getUser();
  if (error || !user) {
    return null;
  }
  return user;
}

export async function requireAuthenticatedUser(redirectTo = '/login'): Promise<User> {
  const user = await getCurrentUser();
  if (!user) {
    redirect(redirectTo);
  }
  return user;
}

export async function signOut(): Promise<void> {
  const supabase = createClient();
  await supabase.auth.signOut();
}

export const getSession = getCurrentSession;
export const getUser = getCurrentUser;


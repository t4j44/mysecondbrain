import { Home, Plus, Users, Briefcase, MessageCircle, CalendarDays, FileText } from 'lucide-react';

export const primaryNavigation = [
  { title: 'Home', href: '/dashboard', icon: Home },
  { title: 'People', href: '/people', icon: Users },
  { title: 'Meetings', href: '/meetings', icon: CalendarDays },
  { title: 'Capture', href: '/capture', icon: Plus },
  { title: 'Ask', href: '/assistant', icon: MessageCircle },
  { title: 'Work', href: '/work', icon: Briefcase },
  { title: 'Documents', href: '/documents', icon: FileText },
];

export const mobileNavigation = ['/dashboard', '/people', '/capture', '/meetings'].map(
  href => primaryNavigation.find(item => item.href === href)!,
);

export function isMoreActive(pathname: string) {
  return !mobileNavigation.some(item => isPrimaryActive(item.href, pathname));
}

export const workNavigation = [
  { title: 'Projects', href: '/projects', description: 'What you are working toward and who can help.' },
  { title: 'Ventures', href: '/ventures', description: 'The organizations and initiatives behind your work.' },
  { title: 'Tasks', href: '/tasks', description: 'Next steps, with people and project context.' },
  { title: 'Commitments', href: '/work/commitments', description: 'What you promised and what others owe you.' },
  { title: 'Meetings', href: '/meetings', description: 'Conversations, participants and follow-ups.' },
  { title: 'Documents', href: '/documents', description: 'Files and evidence connected to your work.' },
];

export function isPrimaryActive(href: string, pathname: string) {
  if (href === '/dashboard') return pathname === '/' || pathname === '/dashboard';
  if (href === '/work') return ['/work', '/tasks', '/projects', '/ventures', '/memories', '/ideas', '/achievements', '/kpis', '/content'].some(path => pathname === path || pathname.startsWith(path + '/'));
  if (href === '/people' && pathname.startsWith('/organizations')) return true;
  return pathname === href || pathname.startsWith(href + '/');
}

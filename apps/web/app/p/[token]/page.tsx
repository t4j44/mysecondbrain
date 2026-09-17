import { env } from '@/lib/env';
import { notFound } from 'next/navigation';
export const dynamic = 'force-dynamic';
export const metadata = { robots: { index: false, follow: false }, referrer: 'no-referrer' };
export default async function PublicPortfolio({ params }: { params: { token: string } }) {
  if (!/^[A-Za-z0-9_-]{43}$/.test(params.token)) notFound();
  const response = await fetch(`${env.NEXT_PUBLIC_API_BASE_URL.replace(/\/$/, '')}/public/portfolio/${params.token}`, { cache: 'no-store' });
  if (response.status === 404) notFound();
  if (!response.ok) throw new Error('This portfolio is temporarily unavailable.');
  const snapshot: { title: string; body: string } = await response.json();
  return <main className="mx-auto max-w-3xl space-y-6 px-5 py-12"><p className="text-sm text-muted-foreground">Shared with Second Brain · Author-reviewed work evidence</p>
    <h1 className="break-words text-3xl font-semibold">{snapshot.title}</h1>
    <article className="whitespace-pre-wrap break-words leading-relaxed">{snapshot.body}</article>
    <p className="border-t pt-4 text-sm text-muted-foreground">This is a selected public copy. Claims have not been independently verified by Second Brain.</p></main>;
}

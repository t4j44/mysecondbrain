import Link from 'next/link';
import { workNavigation } from '@/lib/navigation';
import { PageHeader } from '@/components/shared/page-header';

export default function WorkPage() {
  return <div className="mx-auto max-w-5xl space-y-6">
    <PageHeader title="Work, connected to people" description="Find the projects, promises and conversations that move your relationships forward." />
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{workNavigation.map(item =>
      <Link key={item.href} href={item.href} className="rounded-xl border bg-card p-5 transition-colors hover:border-primary focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">
        <h2 className="text-lg font-semibold">{item.title}</h2><p className="mt-2 text-sm text-muted-foreground">{item.description}</p>
      </Link>)}</div>
    <div className="rounded-xl border p-5"><h2 className="font-semibold">Who could help with this?</h2>
      <p className="mt-2 text-sm text-muted-foreground">Ask about a project, market or topic. Suggestions explain the saved evidence connecting each person to your work.</p>
      <Link href="/assistant" className="mt-3 inline-flex min-h-11 items-center text-primary underline">Find relevant people</Link>
    </div>
  </div>;
}

'use client';
import Link from 'next/link';
import { ResponsivePageContainer } from '@/components/shared/responsive-page-container';
import { PageHeader } from '@/components/shared/page-header';
import { CapturePanel } from '@/components/meetings/capture-panel';
import { useMeetings } from '@/hooks/useMeetings';
import { statusLabel } from '@/lib/meetings/types';
export default function MeetingsPage() {
  const { meetings, loading, error, refetch } = useMeetings();
  return <ResponsivePageContainer>
    <PageHeader title="Meeting Intelligence" description="Record a conversation. Remember what matters." badge="MEETINGS" />
    <CapturePanel onSaved={() => void refetch()} />
    <section className="mt-8 space-y-3"><h2 className="text-lg font-semibold">Recent meetings</h2>
      {loading && <p role="status">Loading meetings...</p>}{error && <p role="alert">{error}</p>}
      {!loading && !error && !meetings.length && <p className="text-sm text-muted-foreground">Your recorded and uploaded meetings will appear here.</p>}
      {meetings.map(meeting => <Link key={meeting.id} href={`/meetings/${meeting.id}`} className="block rounded-xl border border-border bg-card p-4 hover:bg-accent"><p className="break-words font-semibold">{meeting.title}</p><p className="mt-2 text-sm text-muted-foreground">{new Date(meeting.meeting_date).toLocaleDateString()} · {meeting.duration_minutes} min</p><p className="mt-2 text-sm">{meeting.capture ? statusLabel(meeting.capture.state) : 'Meeting notes'}</p></Link>)}
    </section>
  </ResponsivePageContainer>;
}

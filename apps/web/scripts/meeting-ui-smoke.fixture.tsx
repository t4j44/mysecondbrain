// Isolated browser QA fixture. Production authentication and routes are untouched.
import React from 'react';
import { createRoot } from 'react-dom/client';
import { CapturePanel } from '../components/meetings/capture-panel';
import MeetingDetailPage from '../app/(dashboard)/meetings/[meetingId]/page';
import SchedulePage from '../app/(dashboard)/meetings/schedule/page';
const params = new URLSearchParams(location.search);
createRoot(document.getElementById('root')!).render(<div className={`${params.has('light') ? '' : 'dark'} min-h-screen bg-background text-foreground`}>{params.has('schedule') ? <SchedulePage /> : params.has('detail') ? <MeetingDetailPage /> : <main className="mx-auto max-w-3xl p-4"><CapturePanel onSaved={() => undefined} /></main>}</div>);

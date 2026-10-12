// Isolated browser QA fixture. Production authentication and routes are untouched.
import React from 'react';
import { createRoot } from 'react-dom/client';
import { CapturePanel } from '../components/meetings/capture-panel';
import MeetingDetailPage from '../app/(dashboard)/meetings/[meetingId]/page';
createRoot(document.getElementById('root')!).render(<div className="dark min-h-screen bg-background text-foreground">{new URLSearchParams(location.search).has('detail') ? <MeetingDetailPage /> : <main className="mx-auto max-w-3xl p-4"><CapturePanel onSaved={() => undefined} /></main>}</div>);

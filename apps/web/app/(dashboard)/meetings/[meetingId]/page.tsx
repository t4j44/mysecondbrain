import { createClient } from '@/lib/supabase/client';
'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';

export default function MeetingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const meetingId = params?.meetingId as string;

  const [meeting, setMeeting] = useState<any>(null);
  const [participants, setParticipants] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchMeetingData() {
      setLoading(true);
      setError(null);
      try {
        const { data: { session } } = await createClient().auth.getSession();
      const token = session?.access_token;
        const headers = { Authorization: `Bearer ${token || ''}` };

        // Fetch Meeting Details
        const res = await fetch(`/api/v1/meetings/${meetingId}`, { headers });
        if (!res.ok) {
          throw new Error('Failed to retrieve meeting record.');
        }
        const data = await res.json();
        setMeeting(data.data);

        // Fetch participant details using linked ids
        const participantIds = data.data.participant_person_ids || [];
        const loadedParts = [];
        for (const pId of participantIds) {
          const pRes = await fetch(`/api/v1/people/${pId}`, { headers });
          if (pRes.ok) {
            const pData = await pRes.json();
            loadedParts.push(pData.data);
          }
        }
        setParticipants(loadedParts);
      } catch (err: any) {
        setError(err.message || 'Error occurred');
      } finally {
        setLoading(false);
      }
    }

    if (meetingId) {
      fetchMeetingData();
    }
  }, [meetingId]);

  const handleCreateFollowUpTask = async (actionText: string) => {
    try {
      const { data: { session } } = await createClient().auth.getSession();
      const token = session?.access_token;
      const response = await fetch('/api/v1/tasks', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token || ''}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: `Action: ${actionText}`,
          description: `Extracted from meeting: ${meeting.title}`,
          priority: 'medium',
        }),
      });

      if (response.ok) {
        alert('Action item converted into corresponding task successfully!');
      } else {
        throw new Error('Failed to register task.');
      }
    } catch (err: any) {
      alert(`Error converting item: ${err.message}`);
    }
  };

  const handleCaptureAsMemory = async () => {
    try {
      const { data: { session } } = await createClient().auth.getSession();
      const token = session?.access_token;
      const response = await fetch('/api/v1/memories', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token || ''}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: `Insight: ${meeting.title}`,
          content: meeting.ai_summary || 'Discussion points...',
          category: 'lesson',
        }),
      });

      if (response.ok) {
        alert('Meeting summary captured as reflective memory card!');
      } else {
        throw new Error('Failed to register memory.');
      }
    } catch (err: any) {
      alert(`Error capturing memory: ${err.message}`);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#12081d] text-[#f7f4ea] font-mono p-8 flex items-center justify-center">
        <p className="animate-pulse">{"//"} ACCESSING MEETING MINUTES MATRIX...</p>
      </div>
    );
  }

  if (error || !meeting) {
    return (
      <div className="min-h-screen bg-[#12081d] text-[#f7f4ea] font-mono p-8">
        <div className="border border-red-500 bg-red-950/20 p-6 max-w-lg mx-auto mt-12 text-center">
          <p className="text-red-400 mb-4">{"//"} RECORD UNREACHABLE</p>
          <p className="text-xs text-slate-500 mb-6">{error}</p>
          <button onClick={() => router.push('/meetings')} className="px-4 py-2 bg-[#301642] border border-[#482264] hover:border-[#00ff9d]">
            [ RETURN TO MEETINGS ]
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#12081d] text-[#f7f4ea] font-sans p-6">
      {/* Back link */}
      <Link href="/meetings" className="font-mono text-xs text-[#00ff9d] hover:underline mb-6 inline-block">
        &lt;= [ BACK TO MEETINGS ]
      </Link>

      <header className="mb-8 border-b border-[#301642] pb-6 flex justify-between items-end flex-wrap gap-4">
        <div>
          <span className="font-mono text-xs text-[#00ff9d] uppercase">{"//"} Meeting Cockpit</span>
          <h1 className="text-3xl font-mono tracking-tight font-extrabold text-[#f7f4ea] uppercase mt-1">
            {meeting.title}
          </h1>
          <p className="text-xs font-mono text-slate-400 mt-2">
            Date: {new Date(meeting.meeting_date).toLocaleString()} | Loc: {meeting.location || 'Remote'}
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleCaptureAsMemory}
            className="px-4 py-2 bg-[#12081d] border border-[#301642] text-[#00ff9d] hover:border-[#00ff9d] font-mono text-xs uppercase"
          >
            [ CAPTURE AS MEMORY ]
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main section: Notes & Summaries */}
        <section className="lg:col-span-2 space-y-6">
          {/* AI Summary */}
          {meeting.ai_summary && (
            <div className="border border-[#301642] bg-[#0a0510] p-6">
              <h3 className="text-sm font-mono text-[#00ff9d] uppercase border-b border-[#301642] pb-2 mb-4">
                {"//"} AI Generated Brief
              </h3>
              <p className="text-sm leading-relaxed text-slate-300">{meeting.ai_summary}</p>
            </div>
          )}

          {/* Transcript / Notes */}
          <div className="border border-[#301642] bg-[#0a0510] p-6">
            <h3 className="text-sm font-mono text-[#00ff9d] uppercase border-b border-[#301642] pb-2 mb-4">
              {"//"} Meeting Minutes & Transcripts
            </h3>
            {meeting.transcript_text ? (
              <div className="max-h-96 overflow-y-auto bg-[#12081d] border border-[#301642] p-4 text-xs font-mono text-slate-400 whitespace-pre-wrap leading-relaxed">
                {meeting.transcript_text}
              </div>
            ) : (
              <p className="italic text-slate-500 font-mono text-xs">{"//"} No audio transcripts uploaded for this session.</p>
            )}
          </div>
        </section>

        {/* Sidebar: Participants & Action Items */}
        <section className="lg:col-span-1 space-y-6">
          {/* Participants */}
          <div className="border border-[#301642] bg-[#0a0510] p-6 font-mono text-xs">
            <h3 className="text-[#00ff9d] uppercase border-b border-[#301642] pb-2 mb-4">{"//"} Attendees</h3>
            {participants.length === 0 ? (
              <p className="text-slate-500 italic">No attendees linked.</p>
            ) : (
              <div className="space-y-3">
                {participants.map((p) => (
                  <div key={p.id} className="flex justify-between items-center bg-[#12081d] border border-[#301642] p-3">
                    <div>
                      <p className="font-bold text-[#f7f4ea]">{p.name}</p>
                      <p className="text-[10px] text-slate-500 mt-0.5">{p.role || 'Contributor'}</p>
                    </div>
                    <Link href={`/people/${p.id}`} className="text-[#00ff9d] hover:underline">
                      [ PROFILE ]
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Action Items */}
          <div className="border border-[#301642] bg-[#0a0510] p-6 font-mono text-xs">
            <h3 className="text-[#00ff9d] uppercase border-b border-[#301642] pb-2 mb-4">{"//"} Action Items</h3>
            {meeting.action_items && meeting.action_items.length > 0 ? (
              <div className="space-y-3">
                {meeting.action_items.map((item: string, idx: number) => (
                  <div key={idx} className="flex justify-between items-start bg-[#12081d] border border-[#301642] p-3 gap-2">
                    <span className="text-slate-300 leading-normal">{item}</span>
                    <button
                      onClick={() => handleCreateFollowUpTask(item)}
                      className="text-[#00ff9d] hover:underline shrink-0"
                    >
                      [ + TASK ]
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-500 italic">No action items recorded.</p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

'use client';

import { useEffect, useRef, useState } from 'react';
import { Download, Play } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { createClient } from '@/lib/supabase/client';
import { env } from '@/lib/env';

const extensions: Record<string, string> = {
  'audio/webm': '.webm', 'audio/mpeg': '.mp3', 'audio/mp4': '.m4a',
  'audio/wav': '.wav', 'audio/aac': '.aac', 'audio/ogg': '.ogg',
  'audio/flac': '.flac', 'audio/opus': '.opus',
};

export function RecordingPanel({ meetingId, retainedUntil, deletedAt }: {
  meetingId: string; retainedUntil: string | null; deletedAt: string | null;
}) {
  const [player, setPlayer] = useState('');
  const [busy, setBusy] = useState<'play' | 'download' | null>(null);
  const [error, setError] = useState('');
  const [expired, setExpired] = useState(false);
  const sequence = useRef(0);
  const unavailable = Boolean(deletedAt || expired || (retainedUntil && Date.parse(retainedUntil) <= Date.now()));
  useEffect(() => {
    setPlayer(''); setBusy(null); setError(''); setExpired(false);
    return () => { sequence.current += 1; };
  }, [meetingId, retainedUntil, deletedAt]);
  useEffect(() => () => { if (player.startsWith('blob:')) URL.revokeObjectURL(player); }, [player]);

  async function load(mode: 'play' | 'download') {
    if (busy || unavailable) return;
    const request = ++sequence.current;
    setBusy(mode); setError('');
    try {
      const { data: { session } } = await createClient().auth.getSession();
      if (!session) throw new Error('Sign in again to access your recording.');
      const response = await fetch(`${env.NEXT_PUBLIC_API_BASE_URL.replace(/\/$/, '')}/meetings/${encodeURIComponent(meetingId)}/recording${mode === 'download' ? '/download' : ''}`, {
        headers: { Authorization: `Bearer ${session.access_token}` }, cache: 'no-store',
      });
      if (request !== sequence.current) return;
      const failure = response.status === 409 ? await response.json().catch(() => null) : null;
      if (request !== sequence.current) return;
      if (response.status === 410 || failure?.error?.code === 'RECORDING_EXPIRED') {
        setExpired(true); setPlayer('');
        return;
      }
      if (response.status === 409) throw new Error('The recording is not available yet. Try again after upload finishes.');
      if (response.status === 404) throw new Error('This recording could not be found. Reload the meeting to check availability.');
      if (!response.ok) throw new Error('Could not load the recording. Try again.');
      if (mode === 'play' && response.headers.get('content-type')?.includes('application/json')) {
        const result = await response.json();
        if (request === sequence.current) setPlayer(result.url);
        return;
      }
      const blob = await response.blob();
      if (request !== sequence.current) return;
      const extension = extensions[blob.type.split(';')[0]];
      if (!extension) throw new Error('The server did not return a supported recording. Try again.');
      const url = URL.createObjectURL(blob);
      if (mode === 'play') { setPlayer(url); return; }
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `meeting-${meetingId.replace(/[^a-zA-Z0-9-]/g, '')}${extension}`;
      document.body.appendChild(anchor); anchor.click(); anchor.remove();
      // Let the browser take ownership of the download before releasing the blob.
      window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch (failure) {
      if (request === sequence.current) setError(failure instanceof Error ? failure.message : 'Could not load the recording. Try again.');
    } finally { if (request === sequence.current) setBusy(null); }
  }

  return <section className="mt-6 rounded-xl border bg-card p-4 sm:p-6" aria-labelledby="original-recording-title">
    <h2 id="original-recording-title" className="font-semibold">Original recording</h2>
    {unavailable ? <p className="mt-3 text-sm text-muted-foreground" role="status">The original recording is no longer stored. Any saved transcript is kept separately.</p> : <>
      <p className="mt-2 text-sm text-muted-foreground">{retainedUntil ? `Available until ${new Date(retainedUntil).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' })}.` : 'Available after upload finishes.'} Downloads keep the original audio format.</p>
      <div className="mt-4 flex flex-wrap gap-3">
        <Button variant="outline" disabled={Boolean(busy)} onClick={() => void load('play')}><Play className="mr-2 h-4 w-4" aria-hidden="true" />{busy === 'play' ? 'Loading recording…' : 'Play recording'}</Button>
        <Button variant="outline" disabled={Boolean(busy)} onClick={() => void load('download')}><Download className="mr-2 h-4 w-4" aria-hidden="true" />{busy === 'download' ? 'Preparing download…' : 'Download original audio'}</Button>
      </div>
      {player && <audio id="meeting-recording" aria-label="Original meeting recording" className="mt-4 w-full" controls src={player} onError={() => { setPlayer(''); setError('Playback stopped. Reload the recording if it is still available.'); }} />}
    </>}
    {error && <p role="alert" className="mt-3 text-sm text-destructive">{error}</p>}
  </section>;
}

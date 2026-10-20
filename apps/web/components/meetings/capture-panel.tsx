'use client';
import { useEffect, useRef, useState } from 'react';
import { Mic, Upload } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { createClient } from '@/lib/supabase/client';
import { meetingApi } from '@/lib/meetings/api';
import { BrowserRecorderAdapter, type RecorderAdapter } from '@/lib/meetings/recorder';
import { BrowserLiveTranscriptClient, type LiveTranscriptClient } from '@/lib/meetings/live';
import { BrowserAudioUploadClient } from '@/lib/meetings/upload';
import { deleteLocalRecording, listLocalRecordings, saveLocalRecording, type LocalRecording } from '@/lib/meetings/local-recordings';
import { timerLabel, timeLabel, type LiveSegment, type MeetingUsage } from '@/lib/meetings/types';

export async function meetingSession() { const { data: { session } } = await createClient().auth.getSession(); if (!session) throw new Error('Sign in to save a meeting.'); return session; }

export function CapturePanel({ onSaved }: { onSaved: () => void }) {
  const [usage, setUsage] = useState<MeetingUsage | null>(null); const [permission, setPermission] = useState(false); const [terms, setTerms] = useState(false);
  const [title, setTitle] = useState(''); const [recording, setRecording] = useState(false); const [paused, setPaused] = useState(false); const [busy, setBusy] = useState(false);
  const [seconds, setSeconds] = useState(0); const [progress, setProgress] = useState<number | null>(null); const [liveState, setLiveState] = useState(''); const [liveText, setLiveText] = useState<LiveSegment[]>([]);
  const [error, setError] = useState(''); const [message, setMessage] = useState(''); const [recovery, setRecovery] = useState<LocalRecording[]>([]);
  const recorder = useRef<RecorderAdapter | null>(null); const live = useRef<LiveTranscriptClient | null>(null); const active = useRef<LocalRecording | null>(null);
  const elapsed = useRef(0); const started = useRef(0); const persist = useRef<Promise<unknown>>(Promise.resolve()); const endRef = useRef<() => void>(() => undefined);
  const fileInput = useRef<HTMLInputElement>(null);
  async function refresh() { try { setUsage(await meetingApi.usage()); const session = await meetingSession(); setRecovery(await listLocalRecordings(session.user.id)); } catch { setError('Sign in and connect to Second Brain to record or upload a meeting.'); } }
  useEffect(() => { void refresh(); return () => { live.current?.stop(); void recorder.current?.dispose(); }; }, []);
  useEffect(() => { if (!recording || paused) return; const timer = setInterval(() => { const current = Math.floor((elapsed.current + Date.now() - started.current) / 1000); setSeconds(current); if (current >= (usage?.remaining_seconds || 18000)) endRef.current(); }, 250); return () => clearInterval(timer); }, [recording, paused, usage]);
  useEffect(() => { if (!recording) return; const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ''; }; window.addEventListener('beforeunload', warn); return () => window.removeEventListener('beforeunload', warn); }, [recording]);
  const allowed = permission && terms && !!usage && usage.remaining_seconds > 0;

  async function upload(value: LocalRecording) {
    setBusy(true); setError(''); setMessage(''); setProgress(0);
    try {
      await saveLocalRecording(value); const session = await meetingSession();
      const authorization = await meetingApi.authorize(value.id, value.mime);
      await new BrowserAudioUploadClient().upload(value.blob, authorization, session.access_token, setProgress);
      setMessage('Processing... You can leave this page.'); setProgress(null);
      await meetingApi.finalize(value.id); await deleteLocalRecording(value.id);
      setMessage('Recording uploaded privately. Processing continues when you leave this page.'); onSaved();
    } catch (failure) { setError(failure instanceof Error ? failure.message : "Couldn't upload. Retry your saved recording below."); }
    finally { setBusy(false); setProgress(null); await refresh(); }
  }

  async function start() {
    if (!allowed || busy) return; setBusy(true); setError(''); setMessage(''); setLiveText([]); setSeconds(0); elapsed.current = 0;
    try {
      const session = await meetingSession(); const meeting = await meetingApi.create(crypto.randomUUID(), title.trim() || 'New meeting', usage?.data_mode === 'free_redacted');
      const value: LocalRecording = { id: meeting.id, owner: session.user.id, title: meeting.title, mime: '', blob: new Blob(), createdAt: Date.now() }; active.current = value;
      const adapter = new BrowserRecorderAdapter(); recorder.current = adapter; const transcript = new BrowserLiveTranscriptClient(); live.current = transcript;
      let liveAvailable = true;
      await adapter.start(pcm => transcript.send(pcm), blob => {
        const latest = { ...value, mime: blob.type, blob }; active.current = latest;
        persist.current = persist.current.then(() => saveLocalRecording(latest)).catch(() => setError('Device storage is full. End and upload this meeting before leaving.'));
        if (blob.size > (usage?.max_bytes || 52428800) * 0.9) endRef.current();
      }, () => endRef.current(), () => { liveAvailable = false; setLiveState('Live transcript unavailable. Recording continues.'); });
      started.current = Date.now(); setRecording(true); setPaused(false);
      if (liveAvailable) transcript.start(meeting.id, async () => (await meetingSession()).access_token, segment => setLiveText(current => [...current, segment]), setLiveState);
    } catch (failure) { live.current?.stop(); await recorder.current?.dispose(); recorder.current = null; setError(failure instanceof DOMException && failure.name === 'NotAllowedError' ? 'Microphone access was denied. Allow it in browser settings, or upload a recording.' : 'Could not start recording. Check microphone access, or upload a recording.'); }
    finally { setBusy(false); }
  }

  async function end() {
    const adapter = recorder.current; if (!adapter || !active.current) return; recorder.current = null; live.current?.stop(); setRecording(false); setBusy(true);
    try { const blob = await adapter.stop(); await persist.current; await upload({ ...active.current, blob, mime: blob.type }); }
    catch { setBusy(false); setError('Recording stopped. Recover the saved copy below.'); await refresh(); }
  }
  endRef.current = () => { void end(); };
  function togglePause() { if (paused) { recorder.current?.resume(); started.current = Date.now(); } else { recorder.current?.pause(); elapsed.current += Date.now() - started.current; } setPaused(!paused); }
  async function selected(file?: File) { if (!file || !allowed) return; if (!file.size || file.size > (usage?.max_bytes || 52428800)) { setError(`Choose a recording smaller than ${Math.floor((usage?.max_bytes || 52428800) / 1048576)} MB.`); return; } setBusy(true); setError(''); try { const session = await meetingSession(); const meeting = await meetingApi.create(crypto.randomUUID(), title.trim() || file.name.replace(/\.[^.]+$/, '').slice(0, 255), usage?.data_mode === 'free_redacted'); const mime = file.type || ({ m4a: 'audio/mp4', mp4: 'audio/mp4', wav: 'audio/wav', webm: 'audio/webm', aac: 'audio/aac', ogg: 'audio/ogg', flac: 'audio/flac', opus: 'audio/opus' } as Record<string, string>)[file.name.split('.').pop()?.toLowerCase() || ''] || 'audio/mpeg'; await upload({ id: meeting.id, owner: session.user.id, title: meeting.title, mime, blob: file, createdAt: Date.now() }); } catch { setBusy(false); setError("Couldn't start this upload. Retry."); } }

  return <section className="space-y-5 rounded-xl border border-border bg-card p-4 sm:p-6">
    <div><h2 className="font-semibold">Meeting time this month</h2><p className="mt-1 text-sm text-muted-foreground">{usage ? `${timeLabel(usage.used_seconds)} / ${timeLabel(usage.limit_seconds)} · ${timeLabel(usage.remaining_seconds)} remaining` : 'Loading your allowance...'}</p>{usage && <progress className="mt-3 h-2 w-full accent-primary" max={usage.limit_seconds} value={usage.used_seconds} aria-label="Meeting time used" />}{usage?.remaining_seconds === 0 && <p className="mt-2 text-sm">You&apos;ve used your 5 hours for this month.</p>}</div>
    {!recording && <><label className="block text-sm">Meeting name (optional)<input className="mt-2 w-full rounded-md border border-input bg-background p-3" maxLength={255} value={title} onChange={e => setTitle(e.target.value)} placeholder="Meeting with Sarah" /></label>
      <label className="flex items-start gap-3 text-sm"><input type="checkbox" className="mt-1 h-4 w-4 shrink-0" checked={permission} onChange={e => setPermission(e.target.checked)} />I have permission to record this meeting.</label>
      <label className="flex items-start gap-3 text-sm"><input type="checkbox" className="mt-1 h-4 w-4 shrink-0" checked={terms} onChange={e => setTerms(e.target.checked)} /><span>{usage?.data_mode === 'paid_private' ? 'I agree to send this recording to the connected AI provider for processing.' : 'This recording contains no sensitive, confidential or personal information. It may be used to improve the provider’s products under free-tier terms. Avoid confidential meetings; use synthetic or non-sensitive public audio only.'}</span></label>
      <p className="text-xs text-muted-foreground">Recordings are private and removed {usage?.retention_days || 7} days after transcription. Your transcript and meeting details stay saved. Uploads can be up to {Math.floor((usage?.max_bytes || 52428800) / 1048576)} MB.</p>
      <div className="grid gap-3 sm:grid-cols-2"><Button className="min-h-12" disabled={!allowed || busy} onClick={() => void start()}><Mic className="mr-2 h-4 w-4" />Record meeting</Button><Button className="min-h-12" variant="outline" disabled={!allowed || busy} onClick={() => fileInput.current?.click()}><Upload className="mr-2 h-4 w-4" />Upload recording</Button></div>
      <input ref={fileInput} type="file" className="hidden" aria-label="Upload recording file" accept="audio/*,.m4a,.webm,.mp3,.wav,.aac,.ogg,.flac,.opus" onChange={e => { void selected(e.target.files?.[0]); e.target.value = ''; }} /></>}
    {recording && <div className="space-y-4"><p className="font-semibold">{paused ? 'Paused' : '● Recording'}</p><p className="text-4xl tabular-nums" aria-label="Recording timer">{timerLabel(seconds)}</p><p className="text-sm text-muted-foreground">Keep this page open and your phone awake while recording.</p><div className="flex flex-wrap gap-3"><Button variant="outline" onClick={togglePause}>{paused ? 'Resume' : 'Pause'}</Button><Button onClick={() => void end()}>End meeting</Button></div><p className="text-sm" role="status">{liveState}</p><div className="max-h-48 overflow-auto whitespace-pre-wrap text-sm text-muted-foreground" aria-label="Provisional live transcript">{liveText.map(s => <span key={s.sequence}>{s.text} </span>)}</div><p className="text-xs text-muted-foreground">Live text is provisional. The final transcript comes from your recording.</p></div>}
    {progress !== null && <p role="status">Uploading... {progress}%</p>}{message && <p role="status" className="text-sm">{message}</p>}{error && <p role="alert" className="text-sm text-red-500">{error}</p>}
    {!!recovery.length && <div className="space-y-3 border-t border-border pt-4"><h3 className="font-semibold">Recordings saved on this device</h3>{recovery.map(value => <div key={value.id} className="flex flex-wrap items-center gap-3 text-sm"><span className="min-w-0 flex-1 break-words">{value.title}</span><Button variant="outline" disabled={busy} onClick={() => void upload(value)}>Retry upload</Button><Button variant="ghost" disabled={busy} onClick={() => { if (window.confirm('Delete this local recording?')) void deleteLocalRecording(value.id).then(refresh); }}>Discard</Button></div>)}</div>}
  </section>;
}

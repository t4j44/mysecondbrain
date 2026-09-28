'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api/browser-client';
import { PrivatePhoto } from './private-photo';

type Event = {occurred_at: string; recorded_at: string; timezone: string; source_type: string;
  source_provider: string | null; raw_text: string | null; media: {id: string; kind: string}[]};
export function EventDetails({id, onDeleted}: {id: string; onDeleted: () => void}) {
  const [event, setEvent] = useState<Event | null>(null);
  const [review, setReview] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => { let active = true;
    api.get<Event>(`/context-events/${id}`).then(result => { if (active) setEvent(result); })
      .catch(() => { if (active) setError('Could not load original context.'); });
    return () => { active = false; };
  }, [id]);
  return <section className="space-y-4 rounded-xl border p-4">
    {event && <><h2 className="font-semibold">Original context</h2><p className="text-sm">Happened {new Date(event.occurred_at).toLocaleString()} · Event timezone {event.timezone}<br />Recorded {new Date(event.recorded_at).toLocaleString()} · Source {event.source_type}{event.source_provider ? ` / ${event.source_provider}` : ''}</p>
      {event.raw_text && <details><summary className="cursor-pointer py-2">Read original text</summary><p className="whitespace-pre-wrap break-words">{event.raw_text}</p></details>}
      <div className="flex flex-wrap gap-3">{event.media.map(photo => <PrivatePhoto key={photo.id} {...photo} />)}</div>
      {!review ? <button className="min-h-11 underline" onClick={() => setReview(true)}>Delete this context</button> : <div className="space-y-3"><p>Delete this event, its photos and records created from it? Search access is removed immediately. Private photo erasure runs in the background.</p><button disabled={busy} className="min-h-11 rounded border px-4" onClick={async () => {
        setBusy(true); setError(''); try { await api.delete(`/context-events/${id}`); onDeleted(); }
        catch { setError('Could not delete context. Try again.'); } finally { setBusy(false); }
      }}>Confirm deletion</button><button disabled={busy} className="ml-3 min-h-11 underline" onClick={() => setReview(false)}>Cancel</button></div>}
    </>}
    {error && <p role="alert">{error}</p>}
  </section>;
}

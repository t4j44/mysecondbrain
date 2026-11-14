'use client';

import { useEffect, useId, useRef, useState } from 'react';
import { api } from '@/lib/api/browser-client';
import { Button } from '@/components/ui/button';
import type { Meeting } from '@/lib/meetings/types';

export function MeetingTemplate({ meeting, append, disabled = false }: { meeting: Meeting; append: (text: string) => void; disabled?: boolean }) {
  const [kind, setKind] = useState('founder');
  const [preview, setPreview] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const sequence = useRef(0);
  const templateId = useId();
  const selected = JSON.stringify(meeting.capture?.receipt.selected || []);
  useEffect(() => {
    sequence.current += 1; setPreview(''); setMessage(''); setBusy(false);
    return () => { sequence.current += 1; };
  }, [meeting.id, meeting.review_token, meeting.capture?.confirmed_at, selected]);
  async function prepare() {
    const request = ++sequence.current;
    setBusy(true); setPreview(''); setMessage('');
    try {
      const text = await api.get<string>(`/meetings/${meeting.id}/export/markdown`, { params: { kind } });
      if (request === sequence.current) setPreview(text);
    } catch {
      if (request === sequence.current) setMessage('Template could not be loaded. Retry when connected.');
    } finally { if (request === sequence.current) setBusy(false); }
  }
  return <details className="rounded-lg border p-3">
    <summary className="min-h-11 cursor-pointer py-2 font-medium">Use a meeting template</summary>
    <p className="my-2 text-sm text-muted-foreground">Organize existing AI suggestions and reviewed sources. Missing information stays marked; nothing is confirmed automatically.</p>
    <label htmlFor={templateId} className="block text-sm">Meeting template</label><select id={templateId} className="my-2 min-h-12 w-full rounded border bg-background p-3" value={kind} onChange={event => {
      sequence.current += 1; setKind(event.target.value); setPreview(''); setMessage(''); setBusy(false);
    }}><option value="founder">Founder meeting</option><option value="client">Client call</option><option value="interview">User interview</option></select>
    <Button variant="outline" disabled={busy} onClick={() => void prepare()}>{busy ? 'Preparing template…' : 'Preview template'}</Button>
    {preview && <><pre aria-label="Template preview" className="my-3 max-h-96 overflow-auto whitespace-pre-wrap break-words font-sans text-sm leading-relaxed">{preview}</pre>
      <Button variant="outline" disabled={disabled} onClick={() => { append(preview); setPreview(''); }}>Append to notes</Button>
      <p className="mt-2 text-sm text-muted-foreground">Keeps your existing notes. Review the combined draft, then choose Save notes.</p></>}
    {message && <p role="status" className="mt-2 text-sm">{message}</p>}
  </details>;
}

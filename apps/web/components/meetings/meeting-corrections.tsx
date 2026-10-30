'use client';

import { useState } from 'react';
import { api } from '@/lib/api/browser-client';
import { Button } from '@/components/ui/button';
import type { Candidate, Meeting } from '@/lib/meetings/types';

type CorrectionState = { review_token: string; records_token: string; affected_records: number };

export function MeetingCorrections({ meeting, refresh }: { meeting: Meeting; refresh: () => Promise<void> }) {
  const [snapshot, setSnapshot] = useState<CorrectionState | null>(null);
  const [candidateId, setCandidateId] = useState('');
  const [description, setDescription] = useState('');
  const [due, setDue] = useState('');
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const candidates = (meeting.capture?.receipt.selected || []).flatMap(key => {
    const [category, index] = key.split(':');
    const value = meeting.capture?.intelligence[category as keyof typeof meeting.capture.intelligence];
    const candidate = Array.isArray(value) ? value[Number(index)] : undefined;
    return candidate && typeof candidate === 'object' && 'description' in candidate
      ? [{ key, category, candidate: candidate as Candidate }] : [];
  });
  const selected = candidates.find(item => item.key === candidateId);

  async function load() {
    setBusy(true); setMessage(''); setSnapshot(null);
    try {
      const state = await api.get<CorrectionState>(`/meetings/${meeting.id}/corrections`);
      if (state.review_token !== meeting.review_token) {
        await refresh(); setMessage('Meeting details changed. Open the correction form again to review the current version.');
      } else setSnapshot(state);
    } catch { setMessage('Saved details could not be loaded. Try again when connected.'); }
    finally { setBusy(false); }
  }

  async function save() {
    if (!snapshot || !selected) return;
    setBusy(true); setMessage('');
    try {
      await api.post(`/meetings/${meeting.id}/corrections`, {
        request_id: crypto.randomUUID(), expected_review_token: snapshot.review_token,
        expected_records_token: snapshot.records_token, confirmed: true,
        candidate_id: candidateId, description, due_at: due ? new Date(due).toISOString() : null, reason,
      });
      setSnapshot(null); await refresh();
      setMessage('Correction saved. Existing records were updated and old summaries were removed. The original transcript is unchanged.');
    } catch {
      setSnapshot(null);
      setMessage('Saving was not confirmed. Your text is still here. Reload saved details and compare before trying again.');
    } finally { setBusy(false); }
  }

  if (!meeting.capture?.confirmed_at) return null;
  return <details className="mt-6 space-y-3 rounded-xl border bg-card p-4 sm:p-6">
    <summary className="min-h-11 cursor-pointer font-semibold">Correct a saved detail</summary>
    <p className="text-sm text-muted-foreground">Correct a fact, decision, task or deadline. Your correction is recorded separately from the original quotation. Completed tasks and promises require separate review.</p>
    <Button variant="outline" disabled={busy} onClick={() => void load()}>Load saved details</Button>
    {snapshot && <div className="space-y-3">
      <label className="block text-sm">Saved detail<select aria-label="Saved detail" className="mt-1 min-h-12 w-full rounded border bg-background p-3" value={candidateId} onChange={event => {
        const choice = candidates.find(item => item.key === event.target.value);
        setCandidateId(event.target.value); setDescription(choice?.candidate.description || ''); setReason('');
        const date = choice?.candidate.due_at ? new Date(choice.candidate.due_at) : null;
        setDue(date ? new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16) : '');
      }}><option value="">Choose a saved detail</option>{candidates.map(item => <option key={item.key} value={item.key}>{item.category.replaceAll('_', ' ')}: {item.candidate.description}</option>)}</select></label>
      {selected && <>
        <blockquote className="border-l-2 pl-3 text-sm text-muted-foreground">Original quotation: {selected.candidate.evidence_text}</blockquote>
        <label className="block text-sm">Corrected detail<textarea aria-label="Corrected detail" className="mt-1 min-h-24 w-full rounded border bg-background p-3" maxLength={2000} value={description} onChange={event => setDescription(event.target.value)} /></label>
        {['commitments', 'action_items', 'follow_ups'].includes(selected.category) && <label className="block text-sm">Deadline (your current timezone)<input type="datetime-local" className="mt-1 min-h-12 w-full rounded border bg-background p-3" value={due} onChange={event => setDue(event.target.value)} /><span className="block text-xs text-muted-foreground">Leave blank if no deadline was agreed.</span></label>}
        <label className="block text-sm">Reason for correction<textarea aria-label="Reason for correction" className="mt-1 min-h-20 w-full rounded border bg-background p-3" maxLength={1000} value={reason} onChange={event => setReason(event.target.value)} /></label>
        <p className="text-sm text-muted-foreground">Saving updates the existing record, clears summaries that may be outdated, and cancels pending reminders for a corrected commitment. Review any connected calendar event separately.</p>
        <Button disabled={busy || !description.trim() || !reason.trim()} onClick={() => void save()}>Confirm correction</Button>
      </>}
    </div>}
    {!snapshot && description && <details><summary className="min-h-11 cursor-pointer text-sm">Your correction text</summary><p className="whitespace-pre-wrap text-sm">{description}</p><p className="whitespace-pre-wrap text-sm">{reason}</p></details>}
    {message && <p role="status" className="text-sm">{message}</p>}
  </details>;
}

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { MeetingCorrections } from '@/components/meetings/meeting-corrections';
import type { Meeting } from '@/lib/meetings/types';

const { get, post } = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn() }));
vi.mock('@/lib/api/browser-client', () => ({ api: { get, post } }));
function fixture(): Meeting {
  return { id: 'meeting-1', review_token: 'a'.repeat(64), user_id: 'owner', title: 'Review',
    meeting_date: '2026-10-20T10:00:00Z', duration_minutes: 10, ai_summary: null,
    transcript_text: 'I will send the report.', action_items: [], participant_person_ids: [],
    metadata: {}, created_at: '2026-10-20', updated_at: '2026-10-20',
    capture: { state: 'completed', confirmed_at: '2026-10-20', duration_seconds: 600,
      retained_until: null, audio_deleted_at: null, error_code: null, data_mode: 'free_redacted',
      receipt: { selected: ['commitments:0'] }, speaker_mappings: {}, transcript_segments: [],
      intelligence: { summary: 'Send report', commitments: [{ description: 'Send the report',
        evidence_text: 'I will send the report.', confidence: 0.9, interpretation: false }] } } };
}
beforeEach(() => {
  vi.clearAllMocks();
  get.mockResolvedValue({ review_token: 'a'.repeat(64), records_token: 'b'.repeat(64), affected_records: 3 });
  post.mockResolvedValue({ source_preserved: true });
});
async function edit() {
  fireEvent.click(screen.getByText('Correct a saved detail'));
  fireEvent.click(screen.getByRole('button', { name: 'Load saved details' }));
  fireEvent.change(await screen.findByLabelText('Saved detail'), { target: { value: 'commitments:0' } });
  fireEvent.change(screen.getByLabelText('Corrected detail'), { target: { value: 'Send revised estimate' } });
  fireEvent.change(screen.getByLabelText('Reason for correction'), { target: { value: 'Agreed scope changed' } });
}
it('requires explicit confirmation and sends both review snapshots with a separate assertion', async () => {
  const refresh = vi.fn().mockResolvedValue(undefined);
  render(<MeetingCorrections meeting={fixture()} refresh={refresh} />);
  await edit();
  expect(post).not.toHaveBeenCalled();
  expect(screen.getByText('Original quotation: I will send the report.')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Confirm correction' }));
  await waitFor(() => expect(refresh).toHaveBeenCalled());
  expect(post).toHaveBeenCalledWith('/meetings/meeting-1/corrections', expect.objectContaining({
    expected_review_token: 'a'.repeat(64), expected_records_token: 'b'.repeat(64),
    confirmed: true, candidate_id: 'commitments:0', description: 'Send revised estimate',
    due_at: null, reason: 'Agreed scope changed',
  }));
  expect(await screen.findByRole('status')).toHaveTextContent('Correction saved');
});
it('retains the owner text after a failed or conflicted save without claiming success', async () => {
  post.mockRejectedValue(new Error('Conflict'));
  render(<MeetingCorrections meeting={fixture()} refresh={vi.fn()} />);
  await edit();
  fireEvent.click(screen.getByRole('button', { name: 'Confirm correction' }));
  expect(await screen.findByRole('status')).toHaveTextContent('Saving was not confirmed');
  expect(screen.getByText('Send revised estimate')).toBeInTheDocument();
  expect(screen.getByText('Agreed scope changed')).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Confirm correction' })).not.toBeInTheDocument();
});
it('refreshes a stale meeting before permitting a correction', async () => {
  get.mockResolvedValue({ review_token: 'c'.repeat(64), records_token: 'b'.repeat(64) });
  const refresh = vi.fn().mockResolvedValue(undefined);
  render(<MeetingCorrections meeting={fixture()} refresh={refresh} />);
  fireEvent.click(screen.getByText('Correct a saved detail'));
  fireEvent.click(screen.getByRole('button', { name: 'Load saved details' }));
  expect(await screen.findByRole('status')).toHaveTextContent('Meeting details changed');
  expect(refresh).toHaveBeenCalled();
  expect(post).not.toHaveBeenCalled();
});

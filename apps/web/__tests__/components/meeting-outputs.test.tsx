import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { MeetingOutputs } from '@/components/meetings/meeting-outputs';
import { ApiError } from '@/lib/api/errors';
import type { Meeting } from '@/lib/meetings/types';

const { get, put } = vi.hoisted(() => ({ get: vi.fn(), put: vi.fn() }));
vi.mock('@/lib/api/browser-client', () => ({ api: { get, put } }));

function fixture(): Meeting {
  return { id: 'synthetic', user_id: 'owner', title: 'Manual title', meeting_date: '2026-10-20T10:00:00+06:00', duration_minutes: 90,
    ai_summary: null, transcript_text: 'If approved, we will test UAE.', action_items: [], participant_person_ids: [],
    metadata: {}, created_at: '2026-10-20', updated_at: '2026-10-20', capture: { state: 'awaiting_review', duration_seconds: 5400,
      retained_until: null, audio_deleted_at: null, confirmed_at: null, error_code: null, data_mode: 'free_redacted',
      receipt: {}, speaker_mappings: {}, transcript_segments: [], intelligence: { summary: 'Short preview',
        executive_summary: 'Financing and conditional market exploration.', suggested_title: { text: 'AI suggested title', evidence: [] },
        discussion_sections: [{ id: 'side', title: 'UAE expansion', kind: 'secondary', summary: 'Explore UAE only if approved.',
          key_points: [], importance: 'high', evidence: [{ segment_id: 'c1:4', speaker_id: 'c1:unknown', start_seconds: 2700, end_seconds: 2710, quote: 'If approved, we will test UAE.' }] }] } } };
}
beforeEach(() => { vi.clearAllMocks(); get.mockImplementation(async (path: string) => path.includes('/export/') ? '# Meeting minutes\nAttendees: Not confirmed' : { items: [] }); });

it('surfaces secondary discussions, canonical evidence and separate notes/minutes', async () => {
  render(<MeetingOutputs meeting={fixture()} refresh={vi.fn()} />);
  expect(screen.getByText('Other important discussions')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /Source c1:4/ })).toHaveAttribute('href', '#segment-c1%3A4');
  expect(screen.getByLabelText<HTMLTextAreaElement>('Meeting notes').value).toContain('UAE expansion');
  expect(await screen.findByText(/Attendees: Not confirmed/)).toBeInTheDocument();
  expect(put).not.toHaveBeenCalled();
});

it('does not replace unsaved notes when polling returns new AI drafts', async () => {
  const meeting = fixture(); const { rerender } = render(<MeetingOutputs meeting={meeting} refresh={vi.fn()} />);
  fireEvent.change(screen.getByLabelText('Meeting notes'), { target: { value: 'My unsaved interpretation' } });
  const updated = fixture(); updated.capture!.intelligence.summary = 'New AI output';
  rerender(<MeetingOutputs meeting={updated} refresh={vi.fn()} />);
  expect(screen.getByLabelText('Meeting notes')).toHaveValue('My unsaved interpretation');
  await screen.findByText(/Attendees: Not confirmed/);
});

it('keeps the edit visible on a concurrent save conflict and submits its original version', async () => {
  put.mockRejectedValue(new ApiError(409, 'Conflict'));
  render(<MeetingOutputs meeting={fixture()} refresh={vi.fn()} />);
  fireEvent.change(screen.getByLabelText('Meeting notes'), { target: { value: 'Keep my edit' } });
  fireEvent.click(screen.getByRole('button', { name: /^Save notes$/ }));
  expect(await screen.findByRole('status')).toHaveTextContent('Conflict: your edit is not saved');
  expect(screen.getByLabelText('Meeting notes')).toHaveValue('Keep my edit');
  expect(put).toHaveBeenCalledWith('/meetings/synthetic/notes', { expected_version: 0, markdown: 'Keep my edit' });
});

it('saves user notes independently without confirming graph/CRM writes', async () => {
  put.mockResolvedValue({ version: 1, markdown: 'Reviewed by me', author: 'user' });
  const refresh = vi.fn().mockResolvedValue(undefined);
  render(<MeetingOutputs meeting={fixture()} refresh={refresh} />);
  fireEvent.change(screen.getByLabelText('Meeting notes'), { target: { value: 'Reviewed by me' } });
  fireEvent.click(screen.getByRole('button', { name: /^Save notes$/ }));
  await waitFor(() => expect(refresh).toHaveBeenCalled());
  expect(await screen.findByRole('status')).toHaveTextContent('Notes saved.');
  expect(put.mock.calls.map(call => call[0])).toEqual(['/meetings/synthetic/notes']);
});

it('keeps the manual title while exposing an editable AI proposal', async () => {
  render(<MeetingOutputs meeting={fixture()} refresh={vi.fn()} />);
  expect(screen.getByLabelText('Title')).toHaveValue('Manual title');
  expect(screen.getByText(/Suggested title: AI suggested title/)).toBeInTheDocument();
  await screen.findByText(/Attendees: Not confirmed/);
  expect(put).not.toHaveBeenCalled();
});

it('refreshes minutes when extraction completes and speaker mappings change', async () => {
  const processing = fixture(); processing.capture!.state = 'extracting';
  const { rerender } = render(<MeetingOutputs meeting={processing} refresh={vi.fn()} />);
  await screen.findByText(/Attendees: Not confirmed/);
  get.mockImplementation(async (path: string) => path.includes('/export/') ? 'Newly extracted proposal with responsible person' : { items: [] });
  const reviewed = fixture();
  rerender(<MeetingOutputs meeting={reviewed} refresh={vi.fn()} />);
  await screen.findByText('Newly extracted proposal with responsible person');
  get.mockImplementation(async (path: string) => path.includes('/export/') ? 'Responsible person: Ahmed' : { items: [] });
  const mapped = fixture(); mapped.capture!.speaker_mappings = { 'c1:unknown': { kind: 'person', person_id: 'person', person_name: 'Ahmed' } };
  rerender(<MeetingOutputs meeting={mapped} refresh={vi.fn()} />);
  await screen.findByText('Responsible person: Ahmed');
});

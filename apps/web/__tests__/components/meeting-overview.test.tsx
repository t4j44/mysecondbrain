import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { Meeting, MeetingProcessingStatus } from '@/lib/meetings/types';

const mocks = vi.hoisted(() => ({ meetings: vi.fn(), refetch: vi.fn() }));
vi.mock('@/hooks/useMeetings', () => ({ useMeetings: mocks.meetings }));
vi.mock('@/components/meetings/capture-panel', () => ({ CapturePanel: () => <p>Capture fixture</p> }));
import MeetingsPage from '@/app/(dashboard)/meetings/page';

function meeting(id: string, state: MeetingProcessingStatus): Meeting {
  return {
    id, user_id: 'synthetic-owner', title: `Conversation ${id}`, meeting_date: '2026-10-27T10:00:00Z',
    duration_minutes: 5, ai_summary: null, transcript_text: null, action_items: [],
    participant_person_ids: [], metadata: {}, created_at: '', updated_at: '',
    capture: { state, duration_seconds: 300, retained_until: null, audio_deleted_at: null, intelligence: {}, transcript_segments: [], speaker_mappings: {}, confirmed_at: null, error_code: null, data_mode: 'free_redacted', receipt: {} },
  };
}
beforeEach(() => {
  vi.clearAllMocks();
  mocks.meetings.mockReturnValue({ meetings: [], loading: false, error: null, refetch: mocks.refetch });
});

describe('meeting overview truth and filtering', () => {
  it.each([{ loading: true, error: null }, { loading: false, error: 'Could not load' }])('never displays zero counts before a successful load: %j', state => {
    mocks.meetings.mockReturnValue({ meetings: [], refetch: mocks.refetch, ...state });
    render(<MeetingsPage />);
    expect(screen.queryByLabelText('Meeting overview')).not.toBeInTheDocument();
    expect(screen.queryByText('Your first meeting starts here')).not.toBeInTheDocument();
  });
  it('offers capture instead of zero-filled statistics for an empty account', () => {
    render(<MeetingsPage />);
    expect(screen.getByText('Your first meeting starts here')).toBeInTheDocument();
    expect(screen.queryByLabelText('Meeting overview')).not.toBeInTheDocument();
  });
  it('separates failed recordings from active processing and finds reviewable meetings', () => {
    mocks.meetings.mockReturnValue({ meetings: [meeting('failed', 'failed'), meeting('active', 'transcribing'), meeting('review', 'awaiting_review')], loading: false, error: null, refetch: mocks.refetch });
    render(<MeetingsPage />);
    fireEvent.click(screen.getByRole('button', { name: 'In progress' }));
    expect(screen.getByRole('link', { name: /Conversation active/ })).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /Conversation failed/ })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Review' }));
    expect(screen.getByRole('link', { name: /Conversation review/ })).toBeInTheDocument();
    fireEvent.change(screen.getByRole('searchbox', { name: 'Search meetings' }), { target: { value: 'no match' } });
    expect(screen.getByText(/No matching meetings/)).toBeInTheDocument();
    expect(screen.queryByText('Your first meeting starts here')).not.toBeInTheDocument();
  });
  it('keeps retry available after an API failure', () => {
    mocks.meetings.mockReturnValue({ meetings: [], loading: false, error: 'Could not load', refetch: mocks.refetch });
    render(<MeetingsPage />);
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }));
    expect(mocks.refetch).toHaveBeenCalledTimes(1);
  });
});

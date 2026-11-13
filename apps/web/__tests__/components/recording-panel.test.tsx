import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
const mocks = vi.hoisted(() => ({ fetch: vi.fn(), session: vi.fn() }));
vi.mock('@/lib/supabase/client', () => ({ createClient: () => ({ auth: { getSession: mocks.session } }) }));
import { RecordingPanel } from '@/components/meetings/recording-panel';

beforeEach(() => {
  vi.stubGlobal('fetch', mocks.fetch);
  mocks.fetch.mockReset(); mocks.session.mockResolvedValue({ data: { session: { access_token: 'synthetic-only' } } });
  vi.stubGlobal('URL', class extends URL { static createObjectURL = vi.fn(() => 'blob:synthetic'); static revokeObjectURL = vi.fn(); });
});
afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks(); vi.useRealTimers(); });
const panel = <RecordingPanel meetingId="meeting-1" retainedUntil="2099-01-01T00:00:00Z" deletedAt={null} />;

describe('original recording', () => {
  it('downloads authenticated original MIME with a matching extension', async () => {
    mocks.fetch.mockResolvedValue({ ok: true, status: 200, headers: new Headers({ 'content-type': 'audio/mp4' }), blob: async () => new Blob(['original'], { type: 'audio/mp4' }) });
    let filename = ''; const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (this: HTMLAnchorElement) { filename = this.download; });
    render(panel); fireEvent.click(screen.getByRole('button', { name: 'Download original audio' }));
    await waitFor(() => expect(click).toHaveBeenCalledOnce());
    expect(filename).toBe('meeting-meeting-1.m4a');
    expect(mocks.fetch).toHaveBeenCalledWith('http://localhost:8000/api/v1/meetings/meeting-1/recording/download', expect.objectContaining({ headers: { Authorization: 'Bearer synthetic-only' }, cache: 'no-store' }));
  });
  it.each([{ retainedUntil: '2020-01-01T00:00:00Z', deletedAt: null }, { retainedUntil: null, deletedAt: '2026-01-01' }])('makes unavailable audio explicit without a request', props => {
    render(<RecordingPanel meetingId="meeting-1" {...props} />);
    expect(screen.getByRole('status')).toHaveTextContent('no longer stored');
    expect(screen.queryByRole('button')).not.toBeInTheDocument(); expect(mocks.fetch).not.toHaveBeenCalled();
  });
  it('accepts expiry from the server and removes download actions', async () => {
    mocks.fetch.mockResolvedValue({ ok: false, status: 409, json: async () => ({ error: { code: 'RECORDING_EXPIRED' } }) }); render(panel);
    fireEvent.click(screen.getByRole('button', { name: 'Download original audio' }));
    expect(await screen.findByRole('status')).toHaveTextContent('no longer stored');
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
  it('keeps retry available when a download fails', async () => {
    mocks.fetch.mockRejectedValue(new Error('Network unavailable')); render(panel);
    fireEvent.click(screen.getByRole('button', { name: 'Download original audio' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Network unavailable');
    expect(screen.getByRole('button', { name: 'Download original audio' })).toBeEnabled();
  });
  it('keeps retry available when upload has not finished', async () => {
    mocks.fetch.mockResolvedValue({ ok: false, status: 409, json: async () => ({ error: { code: 'RECORDING_NOT_READY' } }) });
    render(panel); fireEvent.click(screen.getByRole('button', { name: 'Download original audio' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('after upload finishes');
    expect(screen.getByRole('button', { name: 'Download original audio' })).toBeEnabled();
    expect(screen.queryByText(/no longer stored/)).not.toBeInTheDocument();
  });
  it('does not start a stale download after switching meetings', async () => {
    let resolve!: (value: unknown) => void;
    mocks.fetch.mockReturnValue(new Promise(r => { resolve = r; }));
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
    const { rerender } = render(panel); fireEvent.click(screen.getByRole('button', { name: 'Download original audio' }));
    await waitFor(() => expect(mocks.fetch).toHaveBeenCalledOnce());
    rerender(<RecordingPanel meetingId="meeting-2" retainedUntil={null} deletedAt={null} />);
    await act(async () => resolve({ ok: true, status: 200, headers: new Headers(), blob: async () => new Blob(['old'], { type: 'audio/webm' }) }));
    expect(click).not.toHaveBeenCalled();
  });
  it('ignores a stale expiry response while its body is being read', async () => {
    let resolve!: (value: unknown) => void;
    const body = vi.fn(() => new Promise(r => { resolve = r; }));
    mocks.fetch.mockResolvedValue({ ok: false, status: 409, json: body });
    const { rerender } = render(panel); fireEvent.click(screen.getByRole('button', { name: 'Play recording' }));
    await waitFor(() => expect(body).toHaveBeenCalledOnce());
    rerender(<RecordingPanel meetingId="meeting-2" retainedUntil={null} deletedAt={null} />);
    await act(async () => resolve({ error: { code: 'RECORDING_EXPIRED' } }));
    expect(screen.getByRole('button', { name: 'Play recording' })).toBeEnabled();
    expect(screen.queryByText(/no longer stored/)).not.toBeInTheDocument();
  });
});

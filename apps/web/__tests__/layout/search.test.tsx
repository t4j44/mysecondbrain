import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
const mocks = vi.hoisted(() => ({ post: vi.fn() }));
vi.mock('@/lib/api/browser-client', () => ({ api: { post: mocks.post } }));
import { CommandMenu } from '@/components/layout/command-menu';
function openSearch() { render(<CommandMenu />); fireEvent.click(screen.getByRole('button', { name: 'Search' })); }
beforeEach(() => { mocks.post.mockReset(); });
describe('workspace search', () => {
  it('searches only on submission and links to the real cited meeting segment', async () => {
    mocks.post.mockResolvedValue({ results: [{ id: 'm1', entity_type: 'meeting', title: 'Fictional Sarah call', snippet: 'I will send the draft.', segment_id: 'c0:4', start_seconds: 84 }] });
    openSearch(); fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'Sarah' } });
    expect(mocks.post).not.toHaveBeenCalled(); fireEvent.click(screen.getByRole('button', { name: 'Search saved context' }));
    expect(await screen.findByRole('link', { name: /Fictional Sarah call/ })).toHaveAttribute('href', '/meetings/m1#segment-c0%3A4');
    expect(mocks.post).toHaveBeenCalledWith('/ai/search', { query: 'Sarah' });
  });
  it('discards stale results after query changes', async () => {
    let resolve!: (value: unknown) => void; mocks.post.mockReturnValue(new Promise(r => { resolve = r; }));
    openSearch(); fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'old' } });
    fireEvent.click(screen.getByRole('button', { name: 'Search saved context' }));
    await waitFor(() => expect(mocks.post).toHaveBeenCalledOnce());
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'new' } });
    await act(async () => resolve({ results: [{ id: 'old', entity_type: 'person', title: 'Old result', snippet: '' }] }));
    expect(screen.queryByText('Old result')).not.toBeInTheDocument();
  });
  it('clears old results on failure and offers retry without an invented answer', async () => {
    mocks.post.mockRejectedValue(new Error('offline')); openSearch();
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'promise' } });
    fireEvent.click(screen.getByRole('button', { name: 'Search saved context' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Try again');
    expect(screen.getByRole('button', { name: 'Search saved context' })).toBeEnabled();
    expect(screen.queryByRole('region', { name: 'Saved context results' })).not.toBeInTheDocument();
  });
});

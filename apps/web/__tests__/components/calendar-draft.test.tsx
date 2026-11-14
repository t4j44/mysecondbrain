import { act, fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import SchedulePage from '@/app/(dashboard)/meetings/schedule/page';
import { ApiError } from '@/lib/api/errors';

const { post } = vi.hoisted(() => ({ post: vi.fn() }));
vi.mock('@/lib/api/browser-client', () => ({ api: { post } }));
const result = { status: 'draft', host_start: '2027-01-15T10:30:00+06:00', host_end: '2027-01-15T11:00:00+06:00',
  guest_start: '2027-01-14T23:30:00-05:00', guest_end: '2027-01-15T00:00:00-05:00', calendar: 'SYNTHETIC-CALENDAR' };
beforeEach(() => { vi.clearAllMocks(); post.mockResolvedValue(result); });
function fill() {
  fireEvent.change(screen.getByLabelText('Title'), { target: { value: 'Synthetic call' } });
  fireEvent.change(screen.getByLabelText('Date and time in your time zone'), { target: { value: '2027-01-15T10:30' } });
  fireEvent.change(screen.getByLabelText('Your time zone'), { target: { value: 'Asia/Dhaka' } });
  fireEvent.change(screen.getByLabelText('Guest time zone'), { target: { value: 'America/New_York' } });
}
it('previews both local dates without booking or sending', async () => {
  render(<SchedulePage />); fill();
  expect(screen.getByText(/This is a draft, not a booking/)).toBeInTheDocument();
  expect(post).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Review calendar draft' }));
  expect(await screen.findByRole('region', { name: 'Calendar draft' })).toHaveTextContent('2027-01-14 23:30');
  expect(post).toHaveBeenCalledWith('/meetings/schedule/preview', expect.objectContaining({ title: 'Synthetic call', host_timezone: 'Asia/Dhaka', guest_timezone: 'America/New_York' }));
  expect(post).toHaveBeenCalledTimes(1);
});
it('invalidates displayed and pending previews when an input changes', async () => {
  render(<SchedulePage />); fill();
  fireEvent.click(screen.getByRole('button', { name: 'Review calendar draft' }));
  await screen.findByRole('region', { name: 'Calendar draft' });
  fireEvent.change(screen.getByLabelText('Title'), { target: { value: 'Changed' } });
  expect(screen.queryByRole('region', { name: 'Calendar draft' })).not.toBeInTheDocument();
  let resolve!: (value: typeof result) => void;
  post.mockImplementation(() => new Promise(done => { resolve = done; }));
  fireEvent.click(screen.getByRole('button', { name: 'Review calendar draft' }));
  fireEvent.change(screen.getByLabelText('Duration in minutes'), { target: { value: '45' } });
  await act(async () => { resolve(result); });
  expect(screen.queryByRole('region', { name: 'Calendar draft' })).not.toBeInTheDocument();
});
it('surfaces clock ambiguity and allows an explicit retry', async () => {
  post.mockRejectedValueOnce(new ApiError(422, { code: 'VALIDATION_ERROR', message: 'This local time occurs twice.' }));
  render(<SchedulePage />); fill();
  fireEvent.click(screen.getByRole('button', { name: 'Review calendar draft' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('occurs twice');
  fireEvent.change(screen.getByLabelText('Clock occurrence'), { target: { value: 'later' } });
  fireEvent.click(screen.getByRole('button', { name: 'Review calendar draft' }));
  await screen.findByRole('region', { name: 'Calendar draft' });
  expect(post).toHaveBeenLastCalledWith('/meetings/schedule/preview', expect.objectContaining({ occurrence: 'later' }));
});

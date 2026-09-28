import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { OutreachControls } from '@/components/relationships/outreach-controls';
import ConsentPage from '@/app/oauth/consent/page';
import { fitPhoto } from '@/lib/capture-photo';

const post = vi.hoisted(() => vi.fn());
vi.mock('@/lib/api/browser-client', () => ({api: {post}, oauthApi: {post}}));
vi.mock('@/lib/supabase/client', () => ({createClient: () => ({auth: {getSession: async () => ({data: {session: {access_token: 'synthetic'}}})}})}));

describe('Context actions and consent', () => {
  beforeEach(() => { post.mockReset(); vi.restoreAllMocks(); sessionStorage.clear(); });
  it('opening a reviewed draft cannot count as sent, and a retry preserves the outcome key', async () => {
    const changed = vi.fn();
    const popup = {opener: window, location: {href: ''}, close: vi.fn()};
    vi.spyOn(window, 'open').mockReturnValue(popup as unknown as Window);
    post.mockResolvedValueOnce({id: 'opened', channel: 'whatsapp', url: 'https://wa.me/8801712345678?text=Reviewed', sent: false});
    render(<OutreachControls personId="person" draft="Reviewed" onChanged={changed} />);
    fireEvent.click(screen.getByRole('button', {name: 'Open WhatsApp'}));
    await screen.findByText('Did you send it?');
    expect(post).toHaveBeenCalledTimes(1);
    expect(post.mock.calls[0][0]).toMatch(/outreach\/open$/);
    expect(changed).not.toHaveBeenCalled();
    expect(popup.opener).toBeNull();
    expect(screen.getByRole('button', {name: /I sent it/})).toBeDisabled();
    fireEvent.change(screen.getByLabelText('Outreach outcome'), {target: {value: 'Sent the update.'}});
    post.mockRejectedValueOnce(new Error('Interrupted')).mockResolvedValueOnce({sent: true});
    fireEvent.click(screen.getByRole('button', {name: /I sent it/}));
    await screen.findByRole('alert');
    const first = post.mock.calls[1][1];
    expect(first).toMatchObject({confirmed: true, opened_id: 'opened', outcome: 'Sent the update.'});
    fireEvent.click(screen.getByRole('button', {name: /I sent it/}));
    await waitFor(() => expect(changed).toHaveBeenCalledTimes(1));
    expect(post.mock.calls[2][1].request_id).toBe(first.request_id);
  });
  it('popup blocking offers the reviewed link and cancelling records no outcome', async () => {
    vi.spyOn(window, 'open').mockReturnValue(null);
    post.mockResolvedValue({id: 'opened', channel: 'whatsapp', url: 'https://wa.me/8801712345678', sent: false});
    render(<OutreachControls personId="person" draft="Reviewed" onChanged={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', {name: 'Open WhatsApp'}));
    await screen.findByRole('alert');
    expect(screen.getByRole('link', {name: 'Reopen reviewed message'})).toHaveAttribute('href', 'https://wa.me/8801712345678');
    fireEvent.click(screen.getByRole('button', {name: 'I didn’t send it'}));
    expect(post).toHaveBeenCalledTimes(1);
  });
  it('OAuth defaults to read permissions, with writes and long-lived access unchecked', async () => {
    sessionStorage.setItem('mcp-consent-request', 'a'.repeat(43));
    post.mockResolvedValue({client_name: 'Synthetic', client_id: 'client', redirect_uri: 'https://client.example/callback',
      resource: 'https://api.example/mcp', scopes: ['mcp:memory:read', 'mcp:tasks:write', 'offline_access']});
    render(<ConsentPage />);
    await screen.findByRole('button', {name: 'Approve selected access'});
    expect(screen.getByRole('checkbox', {name: /Read saved notes/})).toBeChecked();
    expect(screen.getByRole('checkbox', {name: /Create or update tasks/})).not.toBeChecked();
    expect(screen.getByRole('checkbox', {name: /Stay connected/})).not.toBeChecked();
    expect(post).toHaveBeenCalledTimes(1);
  });
  it('photo dimensions stay bounded and retain the original aspect ratio', () => {
    expect(fitPhoto(4000, 2000)).toEqual({width: 1600, height: 800});
    expect(fitPhoto(300, 600)).toEqual({width: 300, height: 600});
  });
});

'use client';

import { useCallback, useEffect, useState } from 'react';
import { api } from '@/lib/api/browser-client';
import { Button } from '@/components/ui/button';
import { TelegramActivity, TelegramPreferences } from './telegram-reminders';

type Connection = { available: boolean; delivery_available: boolean; status: 'not_connected' | 'pending' | 'expired' | 'active' | 'revoked'; linked_at: string | null; expires_at: string | null };

export function TelegramConnection() {
  const [connection, setConnection] = useState<Connection | null>(null);
  const [link, setLink] = useState<{ url: string; expires_at: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const load = useCallback(async () => {
    setError('');
    try {
      const result = await api.get<Connection>('/assistant/connections/telegram');
      setConnection(result);
      if (result.status !== 'pending') setLink(null);
    } catch { setError('Telegram status could not be loaded. Try again.'); }
  }, []);
  useEffect(() => { void load(); }, [load]);

  async function run(action: () => Promise<void>) {
    setBusy(true); setError(''); setMessage('');
    try { await action(); } catch { setError('This connection change was not confirmed. Refresh its status before retrying.'); }
    finally { setBusy(false); }
  }

  return <section className="space-y-3 rounded-xl border bg-card p-5" aria-labelledby="telegram-title">
    <h2 id="telegram-title" className="text-lg font-semibold">Telegram</h2>
    <p className="text-sm text-muted-foreground">Link your own private chat. Linking alone does not enable reminders.</p>
    {!connection && !error && <p role="status">Checking Telegram availability…</p>}
    {connection && !error && <>
      <p className="text-sm">{connection.status === 'active' ? 'Your Telegram chat is linked.' : connection.status === 'pending' ? 'Waiting for you to start the bot in Telegram.' : connection.status === 'expired' ? 'The connection link expired. Create a new one.' : connection.status === 'revoked' ? 'Telegram is disconnected.' : 'No Telegram chat is linked.'}</p>
      {!connection.available && <p className="text-sm text-muted-foreground">Telegram setup is not available in this release.</p>}
      {connection.available && connection.status !== 'active' && <Button variant={connection.status === 'pending' ? 'outline' : 'default'} disabled={busy} onClick={() => void run(async () => {
        const result = await api.post<{ url: string; expires_at: string }>('/assistant/connections/telegram/start');
        const target = new URL(result.url);
        if (target.origin !== 'https://t.me' || target.username || target.password) throw new Error('Invalid Telegram destination');
        setLink(result); await load();
      })}>{connection.status === 'pending' || connection.status === 'expired' ? 'Create a new connection link' : 'Link my Telegram'}</Button>}
      {link && connection.status === 'pending' && <div className="space-y-2">
        <a className="inline-flex min-h-11 items-center rounded-lg bg-primary px-4 text-primary-foreground" href={link.url} target="_blank" rel="noopener noreferrer">Open Telegram and tap Start</a>
        <p className="text-sm text-muted-foreground">Private link · expires at {new Date(link.expires_at).toLocaleTimeString()}. Do not share it.</p>
      </div>}
      {['active', 'pending', 'expired'].includes(connection.status) && <Button variant="outline" disabled={busy} onClick={() => void run(async () => {
        await api.delete('/assistant/connections/telegram'); setLink(null); await load(); setMessage('Telegram disconnected. Notification permission has been removed.');
      })}>{connection.status === 'active' ? 'Disconnect Telegram' : 'Cancel connection'}</Button>}
      <p className="text-xs text-muted-foreground">{connection.delivery_available ? 'You can disconnect here or send /stop to the linked bot.' : 'Reminder delivery is not available in this build. You can disconnect here or send /stop to the linked bot.'}</p>
      {connection.status === 'active' && connection.delivery_available && <TelegramPreferences />}
    </>}
    <Button variant="outline" disabled={busy} onClick={() => void run(load)}>Refresh Telegram status</Button>
    {error && <p role="alert" className="text-sm">{error}</p>}
    {message && <p role="status" className="text-sm">{message}</p>}
    <TelegramActivity />
  </section>;
}

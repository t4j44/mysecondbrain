'use client';
import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api/browser-client';
export default function GoogleCallbackPage() {
  const started = useRef(false);
  const [message, setMessage] = useState('Finishing Google connection…');
  useEffect(() => {
    if (started.current) return; started.current = true;
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code'); const state = params.get('state');
    // Remove temporary credentials from the URL and browser history immediately.
    window.history.replaceState({}, '', window.location.pathname);
    if (params.has('error') || !code || !state) { setMessage('Connection was cancelled or incomplete. You can try again.'); return; }
    api.post<{ message: string }>('/integrations/google/callback', { code, state }, { timeoutMs: 45000 })
      .then(result => setMessage(result.message)).catch(error => setMessage(error.message));
  }, []);
  return <div className="space-y-4"><h1 className="text-2xl font-semibold">Google connection</h1>
    <p role="status">{message}</p><Link href="/settings/integrations" className="underline">Return to connections</Link></div>;
}

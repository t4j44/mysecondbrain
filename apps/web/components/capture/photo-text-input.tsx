'use client';
import { useEffect, useRef, useState } from 'react';
import type { Worker } from 'tesseract.js';

export function PhotoTextInput({ onText, disabled }: { onText: (text: string) => void; disabled?: boolean }) {
  const worker = useRef<Worker | null>(null);
  const mounted = useRef(true);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState('');
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; void worker.current?.terminate(); }; }, []);
  async function extract(file: File) {
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 8 * 1024 * 1024) {
      setStatus('Choose a JPG, PNG, or WebP image smaller than 8 MB.'); return;
    }
    setBusy(true); setStatus('Loading text recognition. The photo stays in this browser.');
    try {
      const { createWorker } = await import('tesseract.js');
      const instance = await createWorker('eng', 1, { logger: progress => {
        if (mounted.current && progress.status === 'recognizing text') setStatus(`Reading photo: ${Math.round(progress.progress * 100)}%`);
      } });
      worker.current = instance;
      if (!mounted.current) { await instance.terminate(); return; }
      const result = await instance.recognize(file);
      if (mounted.current) {
        if (!result.data.text.trim()) setStatus('No readable text found. Try a sharper photo or type the details.');
        else { onText(result.data.text.trim().slice(0, 16000)); setStatus('Text added. Check names, numbers, and spelling before reviewing the capture.'); }
      }
    } catch { if (mounted.current) setStatus('Could not read this photo. Type the details or try again.'); }
    finally { await worker.current?.terminate(); worker.current = null; if (mounted.current) setBusy(false); }
  }
  return <section className="space-y-2 rounded-lg border p-3">
    <label className="block text-sm">Read a business card or photo<input type="file" accept="image/jpeg,image/png,image/webp" capture="environment" disabled={disabled || busy}
      className="mt-2 block max-w-full" onChange={event => { const file = event.target.files?.[0]; if (file) void extract(file); event.target.value = ''; }} /></label>
    <p className="text-xs text-muted-foreground">English text recognition runs on this device. The recognition engine downloads on first use. Only text you submit goes to Second Brain.</p>
    {status && <p role="status" className="text-sm">{status}</p>}
  </section>;
}

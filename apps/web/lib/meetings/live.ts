import { env } from '@/lib/env';
import type { LiveSegment } from './types';
export interface LiveTranscriptClient { start(id: string, getToken: () => Promise<string>, onText: (segment: LiveSegment) => void, onState: (state: string) => void): void; send(pcm: ArrayBuffer): void; stop(): void }
export class BrowserLiveTranscriptClient implements LiveTranscriptClient {
  private socket: WebSocket | null = null; private stopped = true;
  private timer: ReturnType<typeof setTimeout> | null = null; private rotate: ReturnType<typeof setTimeout> | null = null;
  private sequence = 0; private offset = 0; private sessionStart = 0; private lastEnd = 0; private attempts = 0;
  start(id: string, getToken: () => Promise<string>, onText: (segment: LiveSegment) => void, onState: (state: string) => void) {
    this.stopped = false;
    const open = async () => {
      if (this.stopped) return; onState(this.attempts ? 'Live transcript reconnecting...' : 'Connecting live transcript...');
      try {
        const token = await getToken(); if (this.stopped) return;
        const url = `${env.NEXT_PUBLIC_API_BASE_URL.replace(/\/$/, '')}/meetings/${id}/live`.replace(/^http/, 'ws');
        const socket = new WebSocket(url); this.socket = socket; this.sessionStart = this.offset;
        let sent = 0; const timeline: { remoteEnd: number; start: number; end: number }[] = [];
        socket.onopen = () => socket.send(JSON.stringify({ token })); let ready = false;
        socket.onmessage = event => {
          const data = JSON.parse(event.data);
          if (data.type === 'ready') { ready = true; this.attempts = 0; onState('Live transcript'); this.rotate = setTimeout(() => socket.close(), Math.min(500, data.session_seconds - 5) * 1000); }
          if (data.type === 'transcript') { const frame = timeline.find(value => value.remoteEnd >= data.end_offset) || timeline[timeline.length - 1]; const end = Math.max(this.lastEnd, frame ? frame.end - Math.max(0, frame.remoteEnd - data.end_offset) : this.sessionStart + data.end_offset); onText({ sequence: this.sequence++, start_offset: this.lastEnd, end_offset: end, text: data.text }); this.lastEnd = end; }
          if (data.type === 'rotate') socket.close(); if (data.type === 'unavailable') { ready = false; onState('Live transcript reconnecting...'); }
        };
        socket.onclose = () => { if (this.rotate) clearTimeout(this.rotate); this.socket = null; if (!this.stopped) { onState('Live transcript reconnecting...'); this.timer = setTimeout(open, Math.min(30000, 1000 * 2 ** this.attempts++)); } };
        socket.onerror = () => { ready = false; socket.close(); };
        this.send = pcm => { if (this.stopped) return; const duration = pcm.byteLength / 32000; const start = this.offset; this.offset += duration; if (ready && socket.readyState === WebSocket.OPEN && socket.bufferedAmount < 128000) { socket.send(pcm); sent += duration; timeline.push({ remoteEnd: sent, start, end: this.offset }); } };
      } catch { if (!this.stopped) { this.attempts++; onState('Live transcript reconnecting...'); this.timer = setTimeout(open, 10000); } }
    }; void open();
  }
  send(pcm: ArrayBuffer) { if (!this.stopped) this.offset += pcm.byteLength / 32000; }
  stop() { this.stopped = true; if (this.timer) clearTimeout(this.timer); if (this.rotate) clearTimeout(this.rotate); this.socket?.close(); this.socket = null; }
}

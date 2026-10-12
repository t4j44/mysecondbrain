import { afterEach, expect, it, vi } from 'vitest';
import { BrowserLiveTranscriptClient } from '@/lib/meetings/live';
class Socket {
  static OPEN=1; static all: Socket[]=[];
  readyState=1; bufferedAmount=0; sent: unknown[]=[];
  onopen?: () => void; onclose?: () => void; onerror?: () => void; onmessage?: (event: {data:string}) => void;
  constructor(public url: string) { Socket.all.push(this); }
  send(value: unknown) { this.sent.push(value); }
  close() { this.readyState=3; this.onclose?.(); }
  receive(value: object) { this.onmessage?.({data:JSON.stringify(value)}); }
}
afterEach(()=>{vi.unstubAllGlobals();vi.useRealTimers();Socket.all=[];});
it('keeps permanent keys out of the URL and preserves timing across dropped live frames',async()=>{
  vi.useFakeTimers();vi.stubGlobal('WebSocket',Socket);const segments=vi.fn();const state=vi.fn();const client=new BrowserLiveTranscriptClient();
  client.start('meeting',async()=>'user-jwt',segments,state);await Promise.resolve();const socket=Socket.all[0];
  expect(socket.url).not.toContain('jwt');expect(socket.url).not.toContain('key=');socket.onopen?.();expect(socket.sent[0]).toBe(JSON.stringify({token:'user-jwt'}));
  client.send(new ArrayBuffer(32000)); // One second before provider readiness is lost to live, not source audio.
  socket.receive({type:'ready',session_seconds:540});client.send(new ArrayBuffer(32000));socket.receive({type:'transcript',text:'বাংলা',end_offset:1});
  expect(segments.mock.calls[0][0].end_offset).toBe(2);
  socket.bufferedAmount=200000;client.send(new ArrayBuffer(32000));socket.bufferedAmount=0;client.send(new ArrayBuffer(32000));socket.receive({type:'transcript',text:'English',end_offset:2});
  expect(segments.mock.calls[1][0].end_offset).toBe(4);expect(segments.mock.calls[1][0].sequence).toBe(1);client.stop();
});
it('rotates before the ten-minute provider limit and reconnects without user action',async()=>{
  vi.useFakeTimers();vi.stubGlobal('WebSocket',Socket);const state=vi.fn();const client=new BrowserLiveTranscriptClient();client.start('meeting',async()=>'jwt',vi.fn(),state);await Promise.resolve();Socket.all[0].receive({type:'ready',session_seconds:540});
  await vi.advanceTimersByTimeAsync(500000);expect(state).toHaveBeenCalledWith('Live transcript reconnecting...');await vi.advanceTimersByTimeAsync(1000);expect(Socket.all).toHaveLength(2);client.stop();await vi.advanceTimersByTimeAsync(60000);expect(Socket.all).toHaveLength(2);
});

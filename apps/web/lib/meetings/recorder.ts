export interface RecorderAdapter {
  start(onPcm: (chunk: ArrayBuffer) => void, onChunk: (blob: Blob) => void, onEnded: () => void, onLiveUnavailable?: () => void): Promise<void>;
  pause(): void; resume(): void; stop(): Promise<Blob>; dispose(): Promise<void>;
}
/** Browser APIs are confined here; source recording never depends on AI. */
export class BrowserRecorderAdapter implements RecorderAdapter {
  private stream: MediaStream | null = null; private recorder: MediaRecorder | null = null;
  private context: AudioContext | null = null; private node: AudioWorkletNode | null = null;
  private chunks: Blob[] = []; private paused = false;
  async start(onPcm: (chunk: ArrayBuffer) => void, onChunk: (blob: Blob) => void, onEnded: () => void, onLiveUnavailable?: () => void) {
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') throw new Error('Recording is not available in this browser. Upload a recording instead.');
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true }, video: false });
      const mime = ['audio/webm;codecs=opus', 'audio/mp4', 'audio/webm'].find(m => MediaRecorder.isTypeSupported(m));
      this.recorder = new MediaRecorder(this.stream, mime ? { mimeType: mime } : undefined);
      this.recorder.ondataavailable = e => { if (e.data.size) { this.chunks.push(e.data); onChunk(new Blob(this.chunks, { type: this.recorder?.mimeType || e.data.type })); } };
      this.stream.getTracks().forEach(track => { track.onended = onEnded; }); this.recorder.start(2000);
      try {
        this.context = new AudioContext(); await this.context.audioWorklet.addModule('/meeting-pcm-worklet.js');
        const source = this.context.createMediaStreamSource(this.stream); this.node = new AudioWorkletNode(this.context, 'meeting-pcm');
        this.node.port.onmessage = e => { if (!this.paused) onPcm(e.data as ArrayBuffer); };
        const silent = this.context.createGain(); silent.gain.value = 0;
        source.connect(this.node).connect(silent).connect(this.context.destination); await this.context.resume();
      } catch { onLiveUnavailable?.(); }
    } catch (error) { await this.dispose(); throw error; }
  }
  pause() { if (this.recorder?.state === 'recording') { this.recorder.pause(); this.paused = true; } }
  resume() { if (this.recorder?.state === 'paused') { this.recorder.resume(); this.paused = false; } }
  async stop(): Promise<Blob> { const recorder = this.recorder; if (!recorder || recorder.state === 'inactive') throw new Error('No recording is running.'); const result = await new Promise<Blob>(resolve => { recorder.onstop = () => resolve(new Blob(this.chunks, { type: recorder.mimeType })); recorder.stop(); }); await this.dispose(); return result; }
  async dispose() { if (this.recorder && this.recorder.state !== 'inactive') { const current = this.recorder; await new Promise<void>(resolve => { current.addEventListener('stop', () => resolve(), { once: true }); current.stop(); }); } this.node?.disconnect(); this.node = null; if (this.context) { await this.context.close().catch(() => undefined); this.context = null; } this.stream?.getTracks().forEach(track => { track.onended = null; track.stop(); }); this.stream = null; }
}

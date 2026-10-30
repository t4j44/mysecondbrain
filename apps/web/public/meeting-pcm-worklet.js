/* Mono samples -> streaming 16 kHz signed 16-bit little-endian PCM. */
class MeetingPcmProcessor extends AudioWorkletProcessor {
  constructor() { super(); this.phase = 0; this.sum = 0; this.count = 0; this.samples = []; }
  process(inputs) {
    const channel = inputs[0]?.[0]; if (!channel) return true;
    for (const value of channel) {
      this.sum += value; this.count++; this.phase += 16000;
      if (this.phase >= sampleRate) { this.phase -= sampleRate; this.samples.push(Math.max(-1, Math.min(1, this.sum / this.count))); this.sum = 0; this.count = 0; }
      if (this.samples.length >= 2048) { const buffer = new ArrayBuffer(this.samples.length * 2); const view = new DataView(buffer); this.samples.forEach((sample, i) => view.setInt16(i * 2, Math.round(sample * (sample < 0 ? 32768 : 32767)), true)); this.port.postMessage(buffer, [buffer]); this.samples = []; }
    }
    return true;
  }
}
registerProcessor('meeting-pcm', MeetingPcmProcessor);

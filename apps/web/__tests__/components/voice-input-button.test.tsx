import * as React from 'react';
import '@testing-library/jest-dom/vitest';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { VoiceInputButton } from '@/components/chat/voice-input-button';

class FakeSpeechRecognition {
  continuous = false;
  interimResults = false;
  lang = '';
  onresult: ((event: any) => void) | null = null;
  onerror: ((event: any) => void) | null = null;
  onend: (() => void) | null = null;
  start = vi.fn();
  stop = vi.fn(() => this.onend?.());
  abort = vi.fn();
  addEventListener = vi.fn();
  removeEventListener = vi.fn();
  dispatchEvent = vi.fn(() => true);
}

afterEach(() => {
  delete window.SpeechRecognition;
  delete window.webkitSpeechRecognition;
});

describe('VoiceInputButton', () => {
  it('stays hidden when browser speech recognition is unavailable', () => {
    render(<VoiceInputButton value="" onChange={vi.fn()} />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('starts recognition and appends the transcript to existing input', async () => {
    const recognitionInstances: FakeSpeechRecognition[] = [];
    window.SpeechRecognition = class extends FakeSpeechRecognition {
      constructor() {
        super();
        recognitionInstances.push(this);
      }
    } as any;
    const onChange = vi.fn();

    render(<VoiceInputButton value="Remember" onChange={onChange} />);
    const button = await screen.findByRole('button', { name: 'Start voice input' });
    fireEvent.click(button);

    const recognition = recognitionInstances[0];
    expect(recognition.start).toHaveBeenCalledOnce();
    act(() => {
      recognition.onresult?.({ results: [{ 0: { transcript: 'call Yousuf tomorrow' }, length: 1 }] });
    });
    expect(onChange).toHaveBeenCalledWith('Remember call Yousuf tomorrow');

    act(() => recognition.onend?.());
    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'Start voice input' })).toBeInTheDocument()
    );
  });
});

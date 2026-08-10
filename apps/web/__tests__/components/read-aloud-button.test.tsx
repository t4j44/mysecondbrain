import * as React from 'react';
import '@testing-library/jest-dom/vitest';
import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ReadAloudButton } from '@/components/chat/read-aloud-button';

class FakeUtterance {
  lang = '';
  rate = 1;
  onend: (() => void) | null = null;
  onerror: (() => void) | null = null;

  constructor(public text: string) {}
}

afterEach(() => {
  delete (window as any).speechSynthesis;
  delete (window as any).SpeechSynthesisUtterance;
});

describe('ReadAloudButton', () => {
  it('stays hidden when speech synthesis is unavailable', () => {
    render(<ReadAloudButton text="Private response" />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('speaks and can stop an assistant response', async () => {
    const speak = vi.fn();
    const cancel = vi.fn();
    Object.defineProperty(window, 'speechSynthesis', {
      configurable: true,
      value: { speak, cancel },
    });
    Object.defineProperty(window, 'SpeechSynthesisUtterance', {
      configurable: true,
      value: FakeUtterance,
    });
    render(<ReadAloudButton text="Call Yousuf tomorrow" />);
    const startButton = await screen.findByRole('button', { name: 'Read response aloud' });
    fireEvent.click(startButton);

    expect(speak).toHaveBeenCalledOnce();
    expect(speak.mock.calls[0][0].text).toBe('Call Yousuf tomorrow');

    const stopButton = screen.getByRole('button', { name: 'Stop reading response' });
    act(() => fireEvent.click(stopButton));
    expect(cancel).toHaveBeenCalledTimes(2);
  });
});

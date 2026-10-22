'use client';

import * as React from 'react';
import { Volume2, VolumeX } from 'lucide-react';

export interface ReadAloudButtonProps {
  text: string;
}

export function ReadAloudButton({ text }: ReadAloudButtonProps) {
  const [isSupported, setIsSupported] = React.useState(false);
  const [isSpeaking, setIsSpeaking] = React.useState(false);

  React.useEffect(() => {
    setIsSupported(
      typeof window !== 'undefined' &&
        'speechSynthesis' in window &&
        'SpeechSynthesisUtterance' in window
    );

    return () => {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const toggleSpeech = () => {
    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = navigator.language || 'en-US';
    utterance.rate = 1;
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    setIsSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  if (!isSupported || !text.trim()) return null;

  return (
    <button
      type="button"
      onClick={toggleSpeech}
      aria-label={isSpeaking ? 'Stop reading response' : 'Read response aloud'}
      title={isSpeaking ? 'Stop reading' : 'Read aloud'}
      className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-lg border px-3 text-muted-foreground hover:text-foreground focus-ring"
    >
      {isSpeaking ? <VolumeX className="h-3.5 w-3.5" /> : <Volume2 className="h-3.5 w-3.5" />}
    </button>
  );
}

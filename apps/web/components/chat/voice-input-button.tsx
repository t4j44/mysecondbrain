'use client';

import * as React from 'react';
import { Mic, Square } from 'lucide-react';

interface SpeechRecognitionAlternativeLike {
  transcript: string;
}

interface SpeechRecognitionResultLike {
  readonly length: number;
  [index: number]: SpeechRecognitionAlternativeLike;
}

interface SpeechRecognitionResultListLike {
  readonly length: number;
  [index: number]: SpeechRecognitionResultLike;
}

interface SpeechRecognitionEventLike extends Event {
  results: SpeechRecognitionResultListLike;
}

interface SpeechRecognitionErrorEventLike extends Event {
  error: string;
}

interface SpeechRecognitionLike extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEventLike) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
}

type SpeechRecognitionConstructor = new () => SpeechRecognitionLike;

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionConstructor;
    webkitSpeechRecognition?: SpeechRecognitionConstructor;
  }
}

export interface VoiceInputButtonProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

function getSpeechRecognition(): SpeechRecognitionConstructor | undefined {
  if (typeof window === 'undefined') return undefined;
  return window.SpeechRecognition ?? window.webkitSpeechRecognition;
}

export function VoiceInputButton({ value, onChange, disabled = false }: VoiceInputButtonProps) {
  const [isSupported, setIsSupported] = React.useState(false);
  const [isListening, setIsListening] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const recognitionRef = React.useRef<SpeechRecognitionLike | null>(null);

  React.useEffect(() => {
    setIsSupported(Boolean(getSpeechRecognition()));
    return () => recognitionRef.current?.abort();
  }, []);

  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      return;
    }

    const SpeechRecognition = getSpeechRecognition();
    if (!SpeechRecognition) return;

    const recognition = new SpeechRecognition();
    const startingValue = value.trim();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = navigator.language || 'en-US';
    recognition.onresult = (event) => {
      let transcript = '';
      for (let index = 0; index < event.results.length; index += 1) {
        transcript += event.results[index][0]?.transcript ?? '';
      }
      onChange([startingValue, transcript.trim()].filter(Boolean).join(' '));
    };
    recognition.onerror = (event) => {
      setError(
        event.error === 'not-allowed'
          ? 'Microphone permission was denied.'
          : 'Voice input stopped unexpectedly.'
      );
      setIsListening(false);
    };
    recognition.onend = () => {
      setIsListening(false);
      recognitionRef.current = null;
    };

    setError(null);
    recognitionRef.current = recognition;
    setIsListening(true);
    recognition.start();
  };

  if (!isSupported) return null;

  return (
    <div className="relative shrink-0">
      <button
        type="button"
        onClick={toggleListening}
        disabled={disabled}
        aria-label={isListening ? 'Stop voice input' : 'Start voice input'}
        aria-pressed={isListening}
        title={isListening ? 'Stop listening' : 'Speak your prompt'}
        className={`inline-flex h-[50px] w-[50px] items-center justify-center rounded-xl border transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${
          isListening
            ? 'border-rose-400/50 bg-rose-600/80 text-white'
            : 'border-purple-400/30 bg-purple-950/60 text-purple-200 hover:border-purple-400 hover:bg-purple-900/60'
        }`}
      >
        {isListening ? <Square className="h-4 w-4" /> : <Mic className="h-5 w-5" />}
      </button>
      {error && (
        <p
          role="status"
          className="absolute bottom-full right-0 mb-2 w-56 rounded-lg border border-rose-500/30 bg-slate-950 p-2 text-xs text-rose-200 shadow-xl"
        >
          {error}
        </p>
      )}
    </div>
  );
}

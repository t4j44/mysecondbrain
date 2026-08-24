'use client';

import React, { useEffect, useRef, useState } from 'react';
import {
  CheckSquare,
  Brain,
  UserPlus,
  Lightbulb,
  Sparkles,
  Mic,
  MicOff,
  X,
  CornerDownLeft,
  Calendar,
  AlertCircle,
  Hash,
} from 'lucide-react';
import { useQuickCapture, CaptureType } from '@/hooks/useQuickCapture';

interface QuickCaptureModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialType?: CaptureType;
}

export function QuickCaptureModal({
  isOpen,
  onClose,
  initialType = 'auto',
}: QuickCaptureModalProps) {
  const {
    input,
    setInput,
    selectedType,
    setSelectedType,
    parsed,
    isSubmitting,
    submitCapture,
  } = useQuickCapture();

  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recognitionError, setRecognitionError] = useState<string | null>(null);
  const recognitionRef = useRef<any>(null);

  // Sync initial type
  useEffect(() => {
    if (isOpen) {
      setSelectedType(initialType);
      setTimeout(() => {
        inputRef.current?.focus();
      }, 50);
    } else {
      setIsRecording(false);
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {}
      }
    }
  }, [isOpen, initialType, setSelectedType]);

  // Global keydown handler inside modal
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (input.trim() && !isSubmitting) {
        submitCapture().then((success) => {
          if (success) onClose();
        });
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      onClose();
    }
  };

  // Voice dictation toggle via Web Speech API
  const toggleVoiceRecording = () => {
    if (isRecording) {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {}
      }
      setIsRecording(false);
      return;
    }

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setRecognitionError('Speech recognition not supported in this browser.');
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        setIsRecording(true);
        setRecognitionError(null);
      };

      recognition.onresult = (event: any) => {
        let transcript = '';
        for (let i = 0; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript;
        }
        setInput(prev => (prev ? `${prev} ${transcript}` : transcript));
      };

      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setIsRecording(false);
        setRecognitionError(`Mic error: ${event.error}`);
      };

      recognition.onend = () => {
        setIsRecording(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err: any) {
      setRecognitionError(err.message || 'Mic access failed');
      setIsRecording(false);
    }
  };

  if (!isOpen) return null;

  const typeConfig: Record<
    'task' | 'memory' | 'person' | 'idea',
    { label: string; icon: React.ElementType; color: string; bg: string }
  > = {
    task: {
      label: 'Task',
      icon: CheckSquare,
      color: 'text-amber-400',
      bg: 'bg-amber-400/10 border-amber-400/30',
    },
    memory: {
      label: 'Reflection / Memory',
      icon: Brain,
      color: 'text-purple-400',
      bg: 'bg-purple-400/10 border-purple-400/30',
    },
    person: {
      label: 'Network Contact',
      icon: UserPlus,
      color: 'text-cyan-400',
      bg: 'bg-cyan-400/10 border-cyan-400/30',
    },
    idea: {
      label: 'Idea Hypothesis',
      icon: Lightbulb,
      color: 'text-emerald-400',
      bg: 'bg-emerald-400/10 border-emerald-400/30',
    },
  };

  const detected = parsed?.detectedType ? typeConfig[parsed.detectedType] : null;

  return (
    <div className="fixed inset-0 z-[250] flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-150">
      {/* Click outside to close */}
      <div className="fixed inset-0" onClick={onClose} aria-hidden="true" />

      <div
        className="relative w-full max-w-2xl rounded-t-2xl sm:rounded-2xl border border-[#3b1e5a] bg-[#0a0510] shadow-[0_0_50px_rgba(0,255,157,0.15)] overflow-hidden animate-in slide-in-from-bottom sm:zoom-in-95 duration-200 z-10 font-sans"
        role="dialog"
        aria-modal="true"
        aria-label="ADHD Smart Quick Capture"
      >
        {/* Header Bar */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-[#251238] bg-[#0e0716]">
          <div className="flex items-center space-x-2">
            <div className="h-6 w-6 rounded-md bg-[#00ff9d]/10 border border-[#00ff9d]/40 flex items-center justify-center text-[#00ff9d]">
              <Sparkles className="h-3.5 w-3.5 animate-pulse" />
            </div>
            <span className="text-xs font-mono font-bold tracking-wider text-[#f7f4ea] uppercase">
              1-Tap Smart Capture
            </span>
            <span className="text-[10px] font-mono text-[#00ff9d] bg-[#00ff9d]/10 px-2 py-0.5 rounded border border-[#00ff9d]/20">
              Auto-Structuring
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <span className="hidden sm:inline text-[10px] font-mono text-muted-foreground">
              [ESC to close]
            </span>
            <button
              onClick={onClose}
              className="inline-flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:bg-[#251238] hover:text-[#f7f4ea] transition-colors"
              aria-label="Close capture"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Capture Body */}
        <div className="p-4 sm:p-6 space-y-4">
          {/* Main Input Textarea */}
          <div className="relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Dump your thought, task, or meeting note here... (e.g. 'Call Sarah tomorrow re: seed terms #high' or 'Met Dr. Aris CTO at Justor')"
              rows={4}
              className="w-full bg-[#12081d] border border-[#301642] focus:border-[#00ff9d] focus:ring-1 focus:ring-[#00ff9d] text-[#f7f4ea] placeholder:text-muted-foreground/60 p-4 rounded-xl text-base sm:text-lg resize-none outline-none transition-all leading-relaxed"
            />

            {/* Voice Dictation Button */}
            <div className="absolute right-3 bottom-3 flex items-center space-x-2">
              <button
                type="button"
                onClick={toggleVoiceRecording}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono transition-all ${
                  isRecording
                    ? 'bg-rose-500 text-white animate-pulse shadow-[0_0_15px_rgba(244,63,94,0.5)]'
                    : 'bg-[#251238] hover:bg-[#3b1e5a] text-[#00ff9d] border border-[#00ff9d]/30'
                }`}
                title="Voice Dictation"
              >
                {isRecording ? (
                  <>
                    <MicOff className="h-3.5 w-3.5" />
                    <span>Listening...</span>
                  </>
                ) : (
                  <>
                    <Mic className="h-3.5 w-3.5" />
                    <span>Voice</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {recognitionError && (
            <p className="text-[11px] font-mono text-rose-400 flex items-center gap-1">
              <AlertCircle className="h-3 w-3" />
              {recognitionError}
            </p>
          )}

          {/* Real-time Parsed Structure Card */}
          {parsed && input.trim() && (
            <div className="rounded-lg border border-[#301642] bg-[#0c0614] p-3 space-y-2 animate-in fade-in duration-150">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center space-x-2">
                  <span className="text-[10px] font-mono uppercase text-muted-foreground">
                    Detected Entity:
                  </span>
                  {detected && (
                    <span
                      className={`inline-flex items-center gap-1 text-xs font-mono font-semibold px-2 py-0.5 rounded border ${detected.bg} ${detected.color}`}
                    >
                      <detected.icon className="h-3 w-3" />
                      {detected.label}
                    </span>
                  )}
                </div>

                {/* Extracted Meta Pills */}
                <div className="flex items-center gap-1.5 flex-wrap">
                  {parsed.priority && (
                    <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-amber-500/15 border border-amber-500/30 text-amber-300">
                      Priority: {parsed.priority}
                    </span>
                  )}
                  {parsed.dueDate && (
                    <span className="text-[10px] font-mono flex items-center gap-1 px-2 py-0.5 rounded bg-blue-500/15 border border-blue-500/30 text-blue-300">
                      <Calendar className="h-2.5 w-2.5" />
                      {new Date(parsed.dueDate).toLocaleDateString()}
                    </span>
                  )}
                  {parsed.company && (
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/15 border border-cyan-500/30 text-cyan-300">
                      Org: {parsed.company}
                    </span>
                  )}
                  {parsed.tags.map((tag) => (
                    <span
                      key={tag}
                      className="text-[10px] font-mono flex items-center px-1.5 py-0.5 rounded bg-[#251238] border border-[#3b1e5a] text-[#00ff9d]"
                    >
                      <Hash className="h-2.5 w-2.5 mr-0.5" />
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Quick Override Type Switchers */}
          <div className="flex items-center justify-between flex-wrap gap-2 pt-1">
            <div className="flex items-center gap-1 sm:gap-1.5 overflow-x-auto">
              <span className="text-[10px] font-mono uppercase text-muted-foreground mr-1">
                Type:
              </span>
              {(['auto', 'task', 'memory', 'person', 'idea'] as CaptureType[]).map(
                (type) => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => setSelectedType(type)}
                    className={`px-2.5 py-1 rounded text-xs font-mono uppercase transition-all ${
                      selectedType === type
                        ? 'bg-[#00ff9d] text-[#0a0510] font-bold shadow-[0_0_10px_rgba(0,255,157,0.3)]'
                        : 'bg-[#1a0c28] text-muted-foreground hover:text-[#f7f4ea] hover:bg-[#251238]'
                    }`}
                  >
                    {type}
                  </button>
                )
              )}
            </div>

            {/* Submit Button */}
            <button
              type="button"
              disabled={!input.trim() || isSubmitting}
              onClick={async () => {
                const ok = await submitCapture();
                if (ok) onClose();
              }}
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-[#00ff9d] text-[#0a0510] font-mono text-xs font-bold uppercase tracking-wider hover:bg-[#00e08a] transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-[0_0_20px_rgba(0,255,157,0.2)] min-h-[44px]"
            >
              <span>{isSubmitting ? 'Structuring...' : 'Capture'}</span>
              <CornerDownLeft className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {/* Footer Hotkey Tips */}
        <div className="px-5 py-2.5 bg-[#050208] border-t border-[#251238] flex items-center justify-between text-[10px] font-mono text-muted-foreground">
          <span>Press ↵ Enter to save • ESC to cancel</span>
          <span className="text-[#00ff9d]">Zero Forms • Zero Cognitive Overhead</span>
        </div>
      </div>
    </div>
  );
}

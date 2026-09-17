'use client';

import Link from 'next/link';
import React, { useRef, useEffect, useState, useCallback } from 'react';
import { useChat } from '../../hooks/useChat';
import { ChatMessage, UseChatOptions } from '../../types/chat';
import { VoiceInputButton } from './voice-input-button';
import { ReadAloudButton } from './read-aloud-button';

export interface ChatAreaProps {
  api?: string;
  initialMessages?: ChatMessage[];
  title?: string;
  subtitle?: string;
  className?: string;
  options?: UseChatOptions;
}

const PRESET_PROMPTS = [
  'What is my primary execution bottleneck this week?',
  'Summarize my recent meetings',
  'What work evidence have I saved recently?',
  'What are my active task priorities across ventures?',
];

export function ChatArea({
  api = '/api/v1/ai/content-generate',
  initialMessages,
  title = "Taj's Second Brain",
  subtitle = 'AI Founder Coach & Executive Thinking Partner',
  className = '',
  options,
}: ChatAreaProps) {
  const chatHelpers = useChat({
    api,
    initialMessages,
    ...options,
  });

  const {
    messages,
    input,
    setInput,
    handleInputChange,
    handleSubmit,
    sendMessage,
    isLoading,
    isThinking,
    stop,
    clearMessages,
    error,
  } = chatHelpers;

  const messagesContainerRef = useRef<HTMLDivElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const [isScrolledUp, setIsScrolledUp] = useState<boolean>(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [showPrompts, setShowPrompts] = useState<boolean>(true);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = 'smooth') => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior });
    }
  }, []);

  const handleScroll = useCallback(() => {
    const container = messagesContainerRef.current;
    if (!container) return;

    const { scrollTop, scrollHeight, clientHeight } = container;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
    setIsScrolledUp(distanceFromBottom > 100);
  }, []);

  useEffect(() => {
    if (!isScrolledUp) {
      scrollToBottom('smooth');
    }
  }, [messages, isThinking, isScrolledUp, scrollToBottom]);

  const handleFormSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    setIsScrolledUp(false);
    setShowPrompts(false);
    await handleSubmit(e);
  };

  const handlePromptClick = (promptText: string) => {
    setIsScrolledUp(false);
    setShowPrompts(false);
    sendMessage(promptText);
  };

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const exportTranscript = () => {
    const transcriptText = messages
      .map((m) => `[${m.timestamp}] ${m.role.toUpperCase()}: ${m.content}`)
      .join('\n\n');
    const blob = new Blob([transcriptText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `taj-second-brain-transcript-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div
      className={`flex flex-col h-[700px] w-full bg-slate-950/80 border border-purple-900/30 backdrop-blur-2xl rounded-2xl shadow-2xl overflow-hidden font-sans text-slate-100 ${className}`}
    >
      <div className="flex items-center justify-between px-6 py-4 bg-slate-900/90 border-b border-white/10 select-none">
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-purple-950/80 border border-purple-500/40 text-purple-300 shadow-lg shadow-purple-900/30">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span
                className={`animate-ping absolute inline-flex h-full w-full rounded-full ${
                  isLoading ? 'bg-purple-400 opacity-75' : 'bg-emerald-400 opacity-75'
                }`}
              />
              <span
                className={`relative inline-flex rounded-full h-3 w-3 ${
                  isLoading ? 'bg-purple-500' : 'bg-emerald-500'
                }`}
              />
            </span>
          </div>

          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-white tracking-wide font-mono uppercase">
                {title}
              </h2>
              <span className="px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider rounded-md bg-purple-500/20 text-purple-300 border border-purple-500/30">
                AI RAG
              </span>
            </div>
            <p className="text-xs text-slate-400 font-sans">{subtitle}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {messages.length > 0 && (
            <>
              <button
                type="button"
                onClick={exportTranscript}
                className="px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg transition-all flex items-center gap-1.5"
                title="Export chat transcript"
              >
                Export
              </button>
              <button
                type="button"
                onClick={clearMessages}
                className="px-3 py-1.5 text-xs font-medium text-rose-300 hover:text-rose-100 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 rounded-lg transition-all flex items-center gap-1.5"
                title="Clear console output"
              >
                Clear
              </button>
            </>
          )}
        </div>
      </div>

      <div
        ref={messagesContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 scrollbar-thin scrollbar-thumb-purple-900/50 scrollbar-track-transparent relative"
      >
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-6">
            <div className="w-16 h-16 rounded-2xl bg-purple-950/60 border border-purple-500/30 flex items-center justify-center text-purple-400 shadow-xl shadow-purple-950/50">
              <svg className="w-8 h-8 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
            </div>
            <div className="max-w-md space-y-2">
              <h3 className="text-lg font-bold text-white font-mono uppercase tracking-wider">
                Founder Intelligence Terminal
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Ask questions about your ventures, relationships, tasks, or strategic decisions. Connected directly to your RAG vector memory via <code className="text-purple-300 font-mono">/api/v1/ai/search</code>.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-xl text-left pt-2">
              {PRESET_PROMPTS.map((promptText, idx) => (
                <button
                  key={idx}
                  onClick={() => handlePromptClick(promptText)}
                  className="p-3 rounded-xl bg-slate-900/60 hover:bg-purple-950/40 border border-white/5 hover:border-purple-500/30 text-xs text-slate-300 hover:text-white transition-all duration-200 group flex items-start justify-between gap-2 shadow-md"
                >
                  <span>{promptText}</span>
                  <svg
                    className="w-3.5 h-3.5 text-slate-500 group-hover:text-purple-400 transition-colors shrink-0 mt-0.5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => {
            const isUser = msg.role === 'user';
            return (
              <div
                key={msg.id}
                className={`flex flex-col space-y-2 ${isUser ? 'items-end' : 'items-start'}`}
              >
                <div className="flex items-center gap-2 px-1 text-[11px] text-slate-400 font-mono">
                  <span className="font-semibold uppercase tracking-wider">
                    {isUser ? 'Taj (Founder)' : 'Second Brain AI'}
                  </span>
                  <span>•</span>
                  <span>{msg.timestamp}</span>

                  {msg.status === 'streaming' && (
                    <span className="px-1.5 py-0.2 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20 text-[10px] flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-ping" />
                      Streaming
                    </span>
                  )}
                </div>

                <div
                  className={`relative group max-w-[85%] sm:max-w-[75%] p-4 rounded-2xl text-sm leading-relaxed ${
                    isUser
                      ? 'bg-purple-900/40 border border-purple-500/30 text-purple-50 rounded-tr-none shadow-lg shadow-purple-950/20'
                      : 'bg-slate-900/80 border border-white/10 text-slate-100 rounded-tl-none shadow-lg backdrop-blur-md'
                  }`}
                >
                  {!isUser && msg.content && (
                    <div className="absolute right-2.5 top-2.5 flex items-center gap-1.5">
                      <ReadAloudButton text={msg.content} />
                      <button
                        type="button"
                        onClick={() => handleCopy(msg.id, msg.content)}
                        className="rounded-md border border-white/10 bg-slate-950/60 p-1.5 text-[11px] text-slate-400 opacity-0 transition-all hover:text-white group-hover:opacity-100 focus:opacity-100"
                        title="Copy response"
                      >
                        {copiedId === msg.id ? 'Copied!' : 'Copy'}
                      </button>
                    </div>
                  )}

                  {msg.isThinking && !msg.content && (
                    <div className="flex items-center gap-3 py-1 text-purple-300">
                      <div className="flex space-x-1.5 items-center">
                        <div className="w-2 h-2 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                        <div className="w-2 h-2 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                        <div className="w-2 h-2 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                      <span className="text-xs font-mono text-purple-300/80 animate-pulse">
                        {msg.thinkingText || 'Thinking and analyzing knowledge graph...'}
                      </span>
                    </div>
                  )}

                  {msg.content && (
                    <div className="whitespace-pre-wrap font-sans">
                      {msg.content}
                    </div>
                  )}

                  {msg.status === 'error' && (
                    <div className="mt-2 p-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 flex items-center gap-2">
                      <span>{msg.error || 'Failed to finish response stream.'}</span>
                    </div>
                  )}

                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-3 pt-2.5 border-t border-white/10 flex flex-wrap items-center gap-1.5 text-xs">
                      <span className="text-[10px] uppercase font-mono text-slate-400 font-semibold">
                        Grounded Sources:
                      </span>
                      {msg.citations.map((citation, idx) => (
                          <Link
                            key={citation.id || idx}
                            href={`/sources/${encodeURIComponent(citation.entity_type)}/${encodeURIComponent(citation.id)}`}
                            className="min-h-11 px-2 py-2 rounded-md bg-purple-950/60 border border-purple-500/30 text-purple-300 text-xs flex items-center gap-1 underline"
                          >
                            [{idx + 1}] {citation.title || citation.entity_type}
                          </Link>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}

        {isThinking && (
          <div className="flex items-center gap-3 p-3.5 rounded-xl bg-purple-950/40 border border-purple-500/30 text-purple-300 max-w-sm shadow-xl">
            <div className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-3 w-3 bg-purple-500" />
            </div>
            <span className="text-xs font-mono text-purple-200">
              Querying RAG store & synthesizing answer...
            </span>
          </div>
        )}

        <div ref={messagesEndRef} className="h-2" />
      </div>

      <div className="p-4 sm:p-5 bg-slate-900/95 border-t border-white/10 space-y-3">
        {messages.length > 0 && (
          <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono px-1">
            <button
              type="button"
              onClick={() => setShowPrompts(!showPrompts)}
              className="hover:text-purple-300 transition-colors flex items-center gap-1"
            >
              <span>{showPrompts ? '▼ Hide Quick Prompts' : '▲ Show Quick Prompts'}</span>
            </button>
            <span>Press Enter to send • Shift+Enter for new line</span>
          </div>
        )}

        <form onSubmit={handleFormSubmit} className="flex items-end gap-2 sm:gap-3">
          <div className="relative flex-1">
            <textarea
              value={input}
              onChange={handleInputChange}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleFormSubmit(e as any);
                }
              }}
              placeholder="Ask your Second Brain about tasks, ventures, mentors, or strategic choices..."
              rows={2}
              className="w-full px-4 py-3 bg-slate-950/80 border border-white/10 hover:border-purple-500/40 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 rounded-xl text-sm text-slate-100 placeholder-slate-500 resize-none outline-none transition-all font-sans"
            />
          </div>

          <VoiceInputButton value={input} onChange={setInput} disabled={isLoading} />

          {isLoading ? (
            <button
              type="button"
              onClick={stop}
              className="px-5 py-3 rounded-xl bg-rose-600/80 hover:bg-rose-600 text-white font-mono text-xs font-bold tracking-wider uppercase border border-rose-400/40 shadow-lg transition-all flex items-center gap-2 h-[50px] shrink-0"
            >
              Stop
            </button>
          ) : (
            <button
              type="submit"
              disabled={!input.trim()}
              className={`px-6 py-3 rounded-xl font-mono text-xs font-bold tracking-wider uppercase border transition-all flex items-center gap-2 h-[50px] shrink-0 ${
                input.trim()
                  ? 'bg-purple-600 hover:bg-purple-500 text-white border-purple-400/40 shadow-lg shadow-purple-900/40 cursor-pointer'
                  : 'bg-slate-800 text-slate-500 border-white/5 cursor-not-allowed'
              }`}
            >
              <span>Send</span>
            </button>
          )}
        </form>
      </div>
    </div>
  );
}

export default ChatArea;

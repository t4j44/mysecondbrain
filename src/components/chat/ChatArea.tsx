'use client';

import React, { useRef, useEffect, useState, useCallback } from 'react';
import { useChat } from '../../hooks/useChat';
import { ChatMessage, Citation, UseChatOptions } from '../../types/chat';

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
  'Summarize recent insights from mentor Yousuf Imran',
  'Draft a LinkedIn founder update for Justor AI',
  'What are my active task priorities across ventures?',
];

export function ChatArea({
  api = '/api/analyze',
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

  // ---------------------------------------------------------------------------
  // Seamless Scrolling Logic
  // ---------------------------------------------------------------------------
  const scrollToBottom = useCallback((behavior: ScrollBehavior = 'smooth') => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior });
    }
  }, []);

  const handleScroll = useCallback(() => {
    const container = messagesContainerRef.current;
    if (!container) return;

    const { scrollTop, scrollHeight, clientHeight } = container;
    // User is considered scrolled up if more than 100px from the bottom
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
    setIsScrolledUp(distanceFromBottom > 100);
  }, []);

  // Auto-scroll on new messages or streaming chunks, ONLY if user hasn't scrolled up manually
  useEffect(() => {
    if (!isScrolledUp) {
      scrollToBottom('smooth');
    }
  }, [messages, isThinking, isScrolledUp, scrollToBottom]);

  // Always scroll to bottom when user sends a new message
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
      className={`flex flex-col h-[750px] w-full max-w-5xl mx-auto bg-slate-950/80 border border-purple-900/30 backdrop-blur-2xl rounded-2xl shadow-2xl overflow-hidden font-sans text-slate-100 ${className}`}
    >
      {/* ---------------------------------------------------------------- font/header Bar */}
      <div className="flex items-center justify-between px-6 py-4 bg-slate-900/90 border-b border-white/10 select-none">
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-purple-950/80 border border-purple-500/40 text-purple-300 shadow-lg shadow-purple-900/30">
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
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
                /api/analyze
              </span>
            </div>
            <p className="text-xs text-slate-400 font-sans">{subtitle}</p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          {messages.length > 0 && (
            <>
              <button
                type="button"
                onClick={exportTranscript}
                className="px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg transition-all flex items-center gap-1.5"
                title="Export chat transcript"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                  />
                </svg>
                Export
              </button>
              <button
                type="button"
                onClick={clearMessages}
                className="px-3 py-1.5 text-xs font-medium text-rose-300 hover:text-rose-100 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 rounded-lg transition-all flex items-center gap-1.5"
                title="Clear console output"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
                Clear
              </button>
            </>
          )}
        </div>
      </div>

      {/* ---------------------------------------------------------------- Chat History Container */}
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
                Ask questions about your ventures, relationships, tasks, or strategic decisions. Connected directly to your RAG vector memory via <code className="text-purple-300 font-mono">/api/analyze</code>.
              </p>
            </div>

            {/* Quick Prompt Cards */}
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
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M14 5l7 7m0 0l-7 7m7-7H3"
                    />
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

                  {msg.status === 'optimistic' && (
                    <span className="px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[10px]">
                      Sending...
                    </span>
                  )}
                  {msg.status === 'streaming' && (
                    <span className="px-1.5 py-0.2 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20 text-[10px] flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-ping" />
                      Streaming
                    </span>
                  )}
                </div>

                {/* Message Bubble Body */}
                <div
                  className={`relative group max-w-[85%] sm:max-w-[75%] p-4 rounded-2xl text-sm leading-relaxed ${
                    isUser
                      ? 'bg-purple-900/40 border border-purple-500/30 text-purple-50 rounded-tr-none shadow-lg shadow-purple-950/20'
                      : 'bg-slate-900/80 border border-white/10 text-slate-100 rounded-tl-none shadow-lg backdrop-blur-md'
                  }`}
                >
                  {/* Copy Button for Assistant */}
                  {!isUser && msg.content && (
                    <button
                      onClick={() => handleCopy(msg.id, msg.content)}
                      className="absolute top-2.5 right-2.5 opacity-0 group-hover:opacity-100 transition-opacity p-1.5 text-slate-400 hover:text-white bg-slate-950/60 rounded-md border border-white/10 text-[11px]"
                      title="Copy response"
                    >
                      {copiedId === msg.id ? 'Copied!' : 'Copy'}
                    </button>
                  )}

                  {/* Thinking state inside assistant message before text arrives */}
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

                  {/* Message Content Render */}
                  {msg.content && (
                    <div className="whitespace-pre-wrap font-sans">
                      {msg.content}
                    </div>
                  )}

                  {/* Error State */}
                  {msg.status === 'error' && (
                    <div className="mt-2 p-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 flex items-center gap-2">
                      <svg className="w-4 h-4 text-rose-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span>{msg.error || 'Failed to finish stream response.'}</span>
                    </div>
                  )}

                  {/* Citations Footer */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-3 pt-2.5 border-t border-white/10 flex flex-wrap items-center gap-1.5 text-xs">
                      <span className="text-[10px] uppercase font-mono text-slate-400 font-semibold">
                        Grounded Sources:
                      </span>
                      {msg.citations.map((citation, idx) => (
                        <span
                          key={citation.id || idx}
                          className="px-2 py-0.5 rounded-md bg-purple-950/60 border border-purple-500/30 text-purple-300 text-[11px] font-mono flex items-center gap-1"
                        >
                          <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                          {citation.title || citation.entity_type}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}

        {/* Global Floating Thinking Indicator when assistant is generating */}
        {isThinking && (
          <div className="flex items-center gap-3 p-3.5 rounded-xl bg-purple-950/40 border border-purple-500/30 text-purple-300 max-w-sm shadow-xl animate-fade-in">
            <div className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-3 w-3 bg-purple-500" />
            </div>
            <span className="text-xs font-mono text-purple-200">
              Querying RAG store & synthesizing answer...
            </span>
          </div>
        )}

        {/* Target ref for auto-scrolling */}
        <div ref={messagesEndRef} className="h-2" />
      </div>

      {/* ---------------------------------------------------------------- Floating "Scroll to bottom" button */}
      {isScrolledUp && (
        <div className="relative z-10">
          <button
            type="button"
            onClick={() => {
              setIsScrolledUp(false);
              scrollToBottom('smooth');
            }}
            className="absolute -top-12 left-1/2 -translate-x-1/2 px-3 py-1.5 rounded-full bg-purple-900/90 text-white text-xs font-mono border border-purple-400/40 shadow-xl backdrop-blur-md flex items-center gap-1.5 hover:bg-purple-800 transition-all cursor-pointer animate-bounce"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
            </svg>
            Scroll to bottom
          </button>
        </div>
      )}

      {/* Error Toast Bar */}
      {error && (
        <div className="px-6 py-2 bg-rose-950/80 border-t border-rose-500/30 text-rose-200 text-xs font-mono flex items-center justify-between">
          <span>Error: {error.message}</span>
          <button
            type="button"
            onClick={() => sendMessage()}
            className="underline hover:text-white"
          >
            Retry
          </button>
        </div>
      )}

      {/* ---------------------------------------------------------------- Input Control Form */}
      <div className="p-4 sm:p-5 bg-slate-900/95 border-t border-white/10 space-y-3">
        {/* Preset suggestions toggler when conversation started */}
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

        {showPrompts && messages.length > 0 && (
          <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
            {PRESET_PROMPTS.map((promptText, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handlePromptClick(promptText)}
                className="px-3 py-1 rounded-lg bg-white/5 hover:bg-purple-950/40 border border-white/10 text-xs text-slate-300 hover:text-purple-200 whitespace-nowrap transition-all shrink-0"
              >
                {promptText}
              </button>
            ))}
          </div>
        )}

        <form onSubmit={handleFormSubmit} className="flex items-end gap-3">
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

          {isLoading ? (
            <button
              type="button"
              onClick={stop}
              className="px-5 py-3 rounded-xl bg-rose-600/80 hover:bg-rose-600 text-white font-mono text-xs font-bold tracking-wider uppercase border border-rose-400/40 shadow-lg transition-all flex items-center gap-2 h-[50px] shrink-0"
            >
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
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
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </button>
          )}
        </form>
      </div>
    </div>
  );
}

export default ChatArea;

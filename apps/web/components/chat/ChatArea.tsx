'use client';

import Link from 'next/link';
import React, { memo, useRef, useEffect, useState, useCallback } from 'react';
import * as Menu from '@radix-ui/react-dropdown-menu';
import { ArrowDown, ArrowUp, MoreHorizontal, Square } from 'lucide-react';
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

const PRESET_PROMPTS = ['Who should I follow up with?', 'What did I promise recently?', 'Summarize my saved meetings'];
const control = 'inline-flex min-h-11 min-w-11 items-center justify-center rounded-lg border px-3 text-sm focus-ring disabled:opacity-50';
const iconControl = 'inline-flex h-[48px] w-[48px] shrink-0 items-center justify-center rounded-lg border focus-ring disabled:opacity-50';

// Typing in the composer must not rerender the complete conversation history.
const Message = memo(function Message({ message }: { message: ChatMessage }) {
  const [copyStatus, setCopyStatus] = useState('Copy');
  const isUser = message.role === 'user';
  return <article className={`min-w-0 ${isUser ? 'ml-auto w-[94%] sm:w-[85%]' : 'w-full'}`} aria-label={isUser ? 'Your question' : 'Second Brain answer'}>
    <p className="mb-2 text-sm text-muted-foreground">{isUser ? 'You' : 'Second Brain'} <span className="ml-2">{message.timestamp}</span></p>
    <div className={`min-w-0 rounded-xl p-3 sm:p-4 ${isUser ? 'bg-secondary/50' : 'bg-card'}`}>
      <div className="whitespace-pre-wrap break-words text-base leading-relaxed [overflow-wrap:anywhere]">{message.content || (message.isThinking ? 'Checking your saved context…' : '')}</div>
      {message.status === 'error' && <p className="mt-3 text-sm text-destructive">{message.error || 'Could not finish this answer. Try again below.'}</p>}
      {!!message.citations?.length && <nav aria-label="Supporting sources" className="mt-4 flex min-w-0 flex-wrap gap-2 border-t pt-3">
        {message.citations.map((citation, i) => <Link key={`${citation.entity_type}:${citation.id}:${i}`}
          href={citation.entity_type === 'meeting' ? `/meetings/${encodeURIComponent(citation.id)}${citation.segment_id ? `#segment-${encodeURIComponent(citation.segment_id)}` : ''}` : `/sources/${encodeURIComponent(citation.entity_type)}/${encodeURIComponent(citation.id)}`}
          className="inline-flex min-h-11 max-w-full items-center rounded-lg border px-3 py-2 text-sm text-primary underline [overflow-wrap:anywhere]">{i + 1}. {citation.title || citation.entity_type}</Link>)}
      </nav>}
      {!isUser && !!message.content && <div className="mt-2 flex flex-wrap gap-2">
        <ReadAloudButton text={message.content} />
        <button type="button" className={control} onClick={async () => {
          try { await navigator.clipboard.writeText(message.content); setCopyStatus('Copied'); }
          catch { setCopyStatus('Copy unavailable'); }
        }}>{copyStatus}</button>
      </div>}
    </div>
  </article>;
});

export function ChatArea({ api = '/api/v1/ai/content-generate', initialMessages, title = 'Ask Second Brain', subtitle = 'Answers from your saved context', className = '', options }: ChatAreaProps) {
  const { messages, input, setInput, handleInputChange, handleSubmit, sendMessage, isLoading, stop, reload, clearMessages, error } = useChat({ api, initialMessages, ...options });
  const containerRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const atBottom = useRef(true);
  const [scrolledUp, setScrolledUp] = useState(false);
  const scrollToBottom = useCallback(() => {
    const container = containerRef.current;
    if (container) container.scrollTop = container.scrollHeight;
  }, []);
  useEffect(() => { if (atBottom.current) scrollToBottom(); }, [messages, scrollToBottom]);
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) { textarea.style.height = 'auto'; textarea.style.height = `${Math.min(textarea.scrollHeight, 128)}px`; }
  }, [input]);
  function exportTranscript() {
    const blob = new Blob([messages.map(m => `${m.role}: ${m.content}`).join('\n\n')], { type:'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'second-brain-conversation.txt'; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return <section aria-label="Conversation" className={`chat-surface mx-auto flex w-full min-w-0 max-w-5xl flex-col ${className}`}>
    <header className="flex shrink-0 items-center justify-between gap-2 border-b px-4 py-3 sm:px-6">
      <div className="min-w-0"><h1 className="text-xl font-semibold">{title}</h1><p className="text-sm text-muted-foreground">{subtitle}</p></div>
      <Menu.Root><Menu.Trigger asChild><button type="button" aria-label="Conversation options" className={iconControl}><MoreHorizontal className="h-5 w-5" /></button></Menu.Trigger>
        <Menu.Portal><Menu.Content align="end" sideOffset={8} className="z-[250] min-w-44 rounded-lg border bg-popover p-1 text-popover-foreground shadow-lg">
          <Menu.Item disabled={!messages.length} onSelect={exportTranscript} className="flex min-h-11 cursor-pointer items-center rounded px-3 text-sm outline-none focus:bg-muted data-[disabled]:opacity-50">Export conversation</Menu.Item>
          <Menu.Item disabled={!messages.length} onSelect={clearMessages} className="flex min-h-11 cursor-pointer items-center rounded px-3 text-sm outline-none focus:bg-muted data-[disabled]:opacity-50">Clear conversation</Menu.Item>
        </Menu.Content></Menu.Portal>
      </Menu.Root>
    </header>
    <div ref={containerRef} tabIndex={0} aria-label="Messages" onScroll={() => {
      const container = containerRef.current;
      if (!container) return;
      atBottom.current = container.scrollHeight - container.scrollTop - container.clientHeight < 80;
      setScrolledUp(!atBottom.current);
    }} className="min-h-0 flex-1 space-y-5 overflow-y-auto overscroll-contain px-4 py-4 sm:px-6">
      {!messages.length ? <div className="mx-auto max-w-xl space-y-5 py-3 sm:py-8">
        <div><h2 className="text-lg font-medium">What would you like to recall?</h2><p className="mt-2 text-base leading-relaxed text-muted-foreground">Ask about people, conversations or work you have saved. Answers link to their supporting sources.</p></div>
        <div className="grid gap-2">{PRESET_PROMPTS.map(prompt => <button key={prompt} type="button" disabled={isLoading} onClick={() => { atBottom.current = true; void sendMessage(prompt); }} className="min-h-11 rounded-xl border px-4 py-3 text-left text-base hover:bg-muted focus-ring">{prompt}</button>)}</div>
        <p className="text-sm leading-relaxed text-muted-foreground">No saved context yet? <Link className="inline-flex min-h-11 items-center underline text-primary" href="/capture">Capture a note</Link></p>
      </div> : messages.map(message => <Message key={message.id} message={message} />)}
    </div>
    <div className="shrink-0 border-t bg-background px-[16px] pb-3 pt-2 sm:px-6">
      {scrolledUp && <button type="button" className={`${control} mb-2 w-full`} onClick={() => { atBottom.current = true; setScrolledUp(false); scrollToBottom(); }}><ArrowDown className="mr-2 h-4 w-4" />Latest answer</button>}
      {error && <div role="alert" className="mb-2 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-destructive p-2 text-sm"><span>Could not get an answer. Your question is kept above.</span><button type="button" disabled={isLoading} className={control} onClick={() => void reload()}>Try again</button></div>}
      <form onSubmit={event => { atBottom.current = true; void handleSubmit(event); }} className="flex min-w-0 items-end gap-[8px]">
        <textarea ref={textareaRef} aria-label="Your question" value={input} onChange={handleInputChange} rows={1} maxLength={16000} placeholder="Ask a question…"
          onKeyDown={event => {
            // Touch keyboards keep Enter for multiline text. Hardware keyboards
            // send with Enter; Shift+Enter always inserts a line break.
            if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing && !window.matchMedia('(pointer: coarse)').matches) {
              event.preventDefault(); if (!isLoading) { atBottom.current = true; void sendMessage(); }
            }
          }} className="min-h-12 min-w-0 flex-1 resize-none rounded-xl border bg-card px-[12px] py-3 text-base leading-6 placeholder:text-muted-foreground focus-ring" />
        <VoiceInputButton value={input} onChange={setInput} disabled={isLoading} />
        {isLoading ? <button type="button" aria-label="Stop answer" className={`${iconControl} bg-destructive text-destructive-foreground`} onClick={stop}><Square className="h-5 w-5" /></button>
          : <button type="submit" aria-label="Send question" disabled={!input.trim()} className={`${iconControl} bg-primary text-primary-foreground`}><ArrowUp className="h-5 w-5" /></button>}
      </form>
      <p role="status" className="mt-2 text-sm leading-snug text-muted-foreground">{isLoading ? 'Checking your saved context… You can stop at any time.' : 'Review sources. If AI is unavailable, answers may show saved excerpts.'}</p>
    </div>
  </section>;
}
export default ChatArea;

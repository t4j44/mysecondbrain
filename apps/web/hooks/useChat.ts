'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { createClient } from '@/lib/supabase/client';
import { env } from '@/lib/env';
import { ChatMessage, UseChatOptions, UseChatHelpers, Citation, Capsule } from '../types/chat';

const MAX_CAPSULES = 4;

export function isCapsule(value: unknown): value is Capsule {
  const item = value as Capsule | null;
  return !!item && typeof item.question === 'string' && typeof item.answer === 'string' && Array.isArray(item.sources);
}

/** The newest few capsules from finished answers; the full transcript is never uploaded. */
export function recentCapsules(messages: ChatMessage[]): Capsule[] {
  return messages
    .filter((message) => message.role === 'assistant' && message.status === 'completed' && isCapsule(message.capsule))
    .slice(-MAX_CAPSULES)
    .map((message) => message.capsule as Capsule);
}

/**
 * Custom hook `useChat` for managing real-time AI conversation streams.
 * Connected to `/api/v1/ai/search` or streaming backend by default.
 * Handles optimistic UI updates, streaming response parsing, and thinking states.
 */
export function useChat(options: UseChatOptions = {}): UseChatHelpers {
  const {
    api = '/api/v1/ai/content-generate',
    initialMessages = [],
    onFinish,
    onError,
    headers = {},
    body = {},
  } = options;

  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [input, setInput] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isThinking, setIsThinking] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);
  const inFlightRef = useRef(false);
  const generationRef = useRef(0);
  useEffect(() => () => { generationRef.current++; abortControllerRef.current?.abort(); }, []);
  const messagesRef = useRef<ChatMessage[]>(messages);
  useEffect(() => { messagesRef.current = messages; }, [messages]);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      setInput(e.target.value);
    },
    []
  );

  const stop = useCallback(() => {
    generationRef.current++;
    inFlightRef.current = false;
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsLoading(false);
    setIsThinking(false);
    setMessages(previous => previous.map(message => message.status === 'thinking' || message.status === 'streaming'
      ? { ...message, status: 'completed', isThinking: false, content: message.content ? `${message.content}\n[Stopped]` : 'Answer stopped.' } : message));
  }, []);

  const sendMessage = useCallback(
    async (customContent?: string) => {
      const messageText = (customContent !== undefined ? customContent : input).trim();
      if (!messageText || isLoading || inFlightRef.current) return;
      inFlightRef.current = true;
      const generation = ++generationRef.current;

      setError(null);
      if (customContent === undefined) {
        setInput('');
      }

      const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      const userMessageId = `user-${crypto.randomUUID()}`;
      const assistantMessageId = `assistant-${crypto.randomUUID()}`;

      const userMessage: ChatMessage = {
        id: userMessageId,
        role: 'user',
        content: messageText,
        timestamp,
        status: 'completed',
      };

      const pendingAssistantMessage: ChatMessage = {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        status: 'thinking',
        isThinking: true,
        thinkingText: 'Checking your saved context…',
        citations: [],
      };

      // Read before queueing the new messages: state updaters run lazily, so a value
      // captured inside one may not exist yet when the request body is built.
      const conversation = recentCapsules(messagesRef.current);
      setMessages((prev) => [...prev, userMessage, pendingAssistantMessage]);

      setIsLoading(true);
      setIsThinking(true);

      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      try {
        const {
          data: { session },
        } = await createClient().auth.getSession();
        const token = session?.access_token;

        // Fail loudly instead of sending an anonymous request. Previously the
        // Authorization header was spread in conditionally, so a missing session
        // produced an unauthenticated call and the backend's opaque
        // "401 AUTHENTICATION_REQUIRED / Missing authentication Bearer token".
        if (!token) {
          throw new Error(
            'Your session has expired. Please sign in again to use the assistant.'
          );
        }

        // Resolve against the configured API origin rather than relying on the
        // Next.js rewrite. The rewrite is evaluated at BUILD time from
        // NEXT_PUBLIC_API_BASE_URL, so a preview build or a missing build-time
        // variable silently sends this request to the frontend origin instead of
        // the backend. Every other call already goes through FastApiClient,
        // which builds absolute URLs the same way.
        const requestUrl = /^https?:\/\//i.test(api)
          ? api
          : `${env.NEXT_PUBLIC_API_BASE_URL.replace(/\/$/, '')}/${api
              .replace(/^\/?api\/v1\/?/, '')
              .replace(/^\//, '')}`;

        const response = await fetch(requestUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...headers,
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            query: messageText,
            prompt: messageText,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
            conversation,
            ...body,
          }),
          signal: abortController.signal,
          cache: 'no-store',
        });
        if (generation !== generationRef.current) return;

        if (!response.ok) {
          const requestId = response.headers.get('x-request-id');
          throw new Error(`The answer service could not complete this request (HTTP ${response.status})${requestId ? `. Request: ${requestId}` : ''}.`);
        }

        if (response.headers.get('content-type')?.includes('application/json')) {
          const result = await response.json();
          if (typeof result.generated_text !== 'string' || !result.generated_text.trim()) {
            throw new Error('The assistant returned an unexpected response. Please try again.');
          }
          const finalMessage: ChatMessage = {
            ...pendingAssistantMessage, content: result.generated_text,
            status: 'completed', isThinking: false, citations: result.citations || [],
            capsule: isCapsule(result.capsule) ? result.capsule : undefined,
          };
          setMessages(prev => prev.map(message => message.id === assistantMessageId ? finalMessage : message));
          setIsThinking(false);
          setIsLoading(false);
          abortControllerRef.current = null;
          inFlightRef.current = false;
          onFinish?.(finalMessage);
          return;
        }

        if (!response.body) {
          throw new Error('Response body is empty, readable stream unavailable.');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let accumulatedContent = '';
        let accumulatedCitations: Citation[] = [];
        let hasReceivedFirstChunk = false;
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (generation !== generationRef.current) { await reader.cancel(); return; }
          const chunk = done ? decoder.decode() : decoder.decode(value, { stream: true });
          buffer += chunk;

          const lines = buffer.split('\n');
          buffer = done ? '' : lines.pop() || '';

          for (const line of lines) {
            const trimmedLine = line.trim();
            if (!trimmedLine) continue;

            let textDelta = '';
            let citationPayload: Citation | null = null;
            let streamError: string | null = null;

            if (trimmedLine.startsWith('0:')) {
              try {
                textDelta = JSON.parse(trimmedLine.slice(2));
              } catch {
                textDelta = trimmedLine.slice(2).replace(/^"(.*)"$/, '$1');
              }
            } else if (trimmedLine.startsWith('e:')) {
              try {
                citationPayload = JSON.parse(trimmedLine.slice(2));
              } catch {}
            } else if (trimmedLine.startsWith('3:')) {
              try {
                streamError = JSON.parse(trimmedLine.slice(2));
              } catch {
                streamError = trimmedLine.slice(2);
              }
            } else if (trimmedLine.startsWith('data:')) {
              const dataContent = trimmedLine.slice(5).trim();
              if (dataContent === '[DONE]') break;
              try {
                const parsed = JSON.parse(dataContent);
                if (typeof parsed === 'string') {
                  textDelta = parsed;
                } else if (parsed.text) {
                  textDelta = parsed.text;
                } else if (parsed.content) {
                  textDelta = parsed.content;
                } else if (parsed.answer) {
                  textDelta = parsed.answer;
                } else if (parsed.delta) {
                  textDelta = parsed.delta;
                }
                if (parsed.citations) {
                  accumulatedCitations = parsed.citations;
                } else if (parsed.citation) {
                  citationPayload = parsed.citation;
                }
              } catch {
                textDelta = dataContent;
              }
            } else if (!trimmedLine.startsWith(':') && !trimmedLine.startsWith('f:') && !trimmedLine.startsWith('d:')) {
              textDelta = line;
            }

            if (streamError) {
              throw new Error(streamError);
            }

            if (citationPayload) {
              accumulatedCitations.push(citationPayload);
            }

            if (textDelta) {
              if (!hasReceivedFirstChunk) {
                hasReceivedFirstChunk = true;
                setIsThinking(false);
              }

              accumulatedContent += textDelta;

              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMessageId
                    ? {
                        ...msg,
                        content: accumulatedContent,
                        citations: accumulatedCitations,
                        status: 'streaming',
                        isThinking: false,
                      }
                    : msg
                )
              );
            }
          }
          if (done) break;
        }

        setIsThinking(false);
        setIsLoading(false);
        abortControllerRef.current = null;
        inFlightRef.current = false;
        if (!accumulatedContent.trim()) throw new Error('No answer was returned. Try again.');

        const finalMessage: ChatMessage = {...pendingAssistantMessage,content:accumulatedContent,
          citations:accumulatedCitations,status:'completed',isThinking:false};
        setMessages(previous=>previous.map(message=>message.id===assistantMessageId?finalMessage:message));
        onFinish?.(finalMessage);
      } catch (err: any) {
        if (generation !== generationRef.current) return;
        if (err.name === 'AbortError') {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? {
                    ...msg,
                    status: 'completed',
                    isThinking: false,
                    content: msg.content ? `${msg.content} [Stopped by user]` : 'Generation stopped.',
                  }
                : msg
            )
          );
        } else {
          const errorObj = err instanceof Error ? err : new Error(String(err));
          setError(errorObj);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? {
                    ...msg,
                    status: 'error',
                    isThinking: false,
                    error: errorObj.message,
                    content: msg.content || 'An error occurred while streaming response.',
                  }
                : msg
            )
          );
          if (onError) {
            onError(errorObj);
          }
        }
        setIsThinking(false);
        setIsLoading(false);
        abortControllerRef.current = null;
        inFlightRef.current = false;
      }
    },
    [api, body, headers, input, isLoading, onError, onFinish]
  );

  const handleSubmit = useCallback(
    async (e?: React.FormEvent<HTMLFormElement>) => {
      if (e) {
        e.preventDefault();
      }
      await sendMessage();
    },
    [sendMessage]
  );

  const reload = useCallback(async () => {
    if (messages.length === 0 || isLoading) return;
    const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user');
    if (lastUserMsg) {
      await sendMessage(lastUserMsg.content);
    }
  }, [isLoading, messages, sendMessage]);

  const clearMessages = useCallback(() => {
    stop();
    setMessages([]);
    setError(null);
  }, [stop]);

  return {
    messages,
    input,
    setInput,
    handleInputChange,
    handleSubmit,
    sendMessage,
    isLoading,
    isThinking,
    stop,
    reload,
    clearMessages,
    setMessages,
    error,
  };
}

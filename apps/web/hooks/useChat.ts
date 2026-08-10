'use client';

import { useState, useRef, useCallback } from 'react';
import { ChatMessage, UseChatOptions, UseChatHelpers, Citation } from '../types/chat';

/**
 * Custom hook `useChat` for managing real-time AI conversation streams.
 * Connected to `/api/v1/ai/search` or streaming backend by default.
 * Handles optimistic UI updates, streaming response parsing, and thinking states.
 */
export function useChat(options: UseChatOptions = {}): UseChatHelpers {
  const {
    api = '/api/v1/ai/search',
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

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      setInput(e.target.value);
    },
    []
  );

  const stop = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsLoading(false);
    setIsThinking(false);
  }, []);

  const sendMessage = useCallback(
    async (customContent?: string) => {
      const messageText = (customContent !== undefined ? customContent : input).trim();
      if (!messageText || isLoading) return;

      setError(null);
      if (customContent === undefined) {
        setInput('');
      }

      const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      const userMessageId = `user-${Date.now()}`;
      const assistantMessageId = `assistant-${Date.now() + 1}`;

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
        thinkingText: 'Querying Second Brain & Vector Memory...',
        citations: [],
      };

      let currentMessagesState: ChatMessage[] = [];
      setMessages((prev) => {
        currentMessagesState = [...prev, userMessage, pendingAssistantMessage];
        return currentMessagesState;
      });

      setIsLoading(true);
      setIsThinking(true);

      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      try {
        const response = await fetch(api, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...headers,
          },
          body: JSON.stringify({
            query: messageText,
            prompt: messageText,
            messages: currentMessagesState.filter(
              (m) => m.id !== assistantMessageId && m.status !== 'error'
            ),
            ...body,
          }),
          signal: abortController.signal,
        });

        if (!response.ok) {
          const errorText = await response.text().catch(() => response.statusText);
          throw new Error(`API returned ${response.status}: ${errorText}`);
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
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          buffer += chunk;

          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

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
        }

        if (buffer.trim()) {
          let textDelta = buffer.trim();
          if (textDelta.startsWith('0:')) {
            try { textDelta = JSON.parse(textDelta.slice(2)); } catch {}
          }
          if (textDelta && !textDelta.startsWith('data:') && !textDelta.startsWith('e:')) {
            accumulatedContent += textDelta;
          }
        }

        setIsThinking(false);
        setIsLoading(false);
        abortControllerRef.current = null;

        let finalMessage: ChatMessage | null = null;
        setMessages((prev) =>
          prev.map((msg) => {
            if (msg.id === assistantMessageId) {
              finalMessage = {
                ...msg,
                content: accumulatedContent || msg.content || 'Response complete.',
                citations: accumulatedCitations,
                status: 'completed',
                isThinking: false,
              };
              return finalMessage;
            }
            return msg;
          })
        );

        if (onFinish && finalMessage) {
          onFinish(finalMessage);
        }
      } catch (err: any) {
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

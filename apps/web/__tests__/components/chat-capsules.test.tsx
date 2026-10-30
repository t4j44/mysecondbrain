import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { isCapsule, recentCapsules, useChat } from '@/hooks/useChat';
import type { Capsule, ChatMessage } from '@/types/chat';

vi.mock('@/lib/supabase/client', () => ({createClient: () => ({auth: {getSession: async () => ({data: {session: {access_token: 'synthetic'}}})}})}));
vi.mock('@/lib/env', () => ({env: {NEXT_PUBLIC_API_BASE_URL: 'https://api.test/api/v1'}}));

const capsule = (n: number): Capsule => ({question: `Question ${n}`, answer: `Answer ${n}`, sources: [{entity_type: 'person', title: `Person ${n}`}]});
const answer = (n: number, extra: Partial<ChatMessage> = {}): ChatMessage => ({
  id: `a${n}`, role: 'assistant', content: `Answer ${n}`, timestamp: '10:00', status: 'completed', capsule: capsule(n), ...extra});

describe('chat capsules', () => {
  const fetchMock = vi.fn();
  beforeEach(() => { vi.stubGlobal('fetch', fetchMock); fetchMock.mockReset(); });
  afterEach(() => vi.unstubAllGlobals());

  it('validates the capsule shape before trusting it', () => {
    expect(isCapsule(capsule(1))).toBe(true);
    for (const bad of [null, undefined, 'text', {question: 'q'}, {question: 'q', answer: 'a', sources: 'x'}]) expect(isCapsule(bad)).toBe(false);
  });

  it('keeps only the newest four capsules from finished answers', () => {
    const messages: ChatMessage[] = [
      ...[1, 2, 3, 4, 5].map(n => answer(n)),
      answer(6, {status: 'error'}), answer(7, {capsule: undefined}),
      {id: 'u', role: 'user', content: 'hi', timestamp: '10:00', capsule: capsule(9)}];
    expect(recentCapsules(messages).map(item => item.question)).toEqual(['Question 2', 'Question 3', 'Question 4', 'Question 5']);
  });

  it('sends short capsules, not the transcript, and keeps the server capsule for the next question', async () => {
    fetchMock.mockImplementation(async (_url: string, init: RequestInit) => {
      const sent = JSON.parse(String(init.body));
      const n = fetchMock.mock.calls.length;
      return new Response(JSON.stringify({generated_text: `Answer ${n}`, citations: [], capsule: capsule(n), echoed: sent.conversation.length}),
        {status: 200, headers: {'content-type': 'application/json'}});
    });
    const {result} = renderHook(() => useChat());
    await act(async () => { await result.current.sendMessage('Tell me about Ahmed'); });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    await act(async () => { await result.current.sendMessage('what about him?'); });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    const [first, second] = fetchMock.mock.calls.map(([, init]) => JSON.parse(String(init.body)));
    expect(first.conversation).toEqual([]);
    expect(second.conversation).toEqual([capsule(1)]);
    expect(second.prompt).toBe('what about him?');
    expect(second).not.toHaveProperty('messages');
    expect(JSON.stringify(second)).not.toContain('Tell me about Ahmed');
    expect(result.current.messages.filter(message => message.role === 'assistant').map(message => message.capsule)).toEqual([capsule(1), capsule(2)]);
  });

  it('ignores a malformed capsule from the server', async () => {
    fetchMock.mockResolvedValue(new Response(JSON.stringify({generated_text: 'Fine.', citations: [], capsule: {question: 5}}),
      {status: 200, headers: {'content-type': 'application/json'}}));
    const {result} = renderHook(() => useChat());
    await act(async () => { await result.current.sendMessage('hello there'); });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.messages.at(-1)?.capsule).toBeUndefined();
    expect(recentCapsules(result.current.messages)).toEqual([]);
  });
});

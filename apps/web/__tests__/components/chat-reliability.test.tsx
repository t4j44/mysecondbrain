import {act,renderHook,waitFor} from '@testing-library/react';
import {afterEach,beforeEach,describe,expect,it,vi} from 'vitest';
import {useChat} from '@/hooks/useChat';

vi.mock('@/lib/supabase/client',()=>({createClient:()=>({auth:{getSession:async()=>({data:{session:{access_token:'synthetic'}}})}})}));
vi.mock('@/lib/env',()=>({env:{NEXT_PUBLIC_API_BASE_URL:'https://api.test/api/v1'}}));

describe('assistant request reliability',()=>{
 const fetchMock=vi.fn();
 beforeEach(()=>{vi.stubGlobal('fetch',fetchMock);fetchMock.mockReset();});
 afterEach(()=>vi.unstubAllGlobals());
 it('locks synchronously against two sends in the same render',async()=>{
  fetchMock.mockImplementation(async()=>new Response(JSON.stringify({generated_text:'Saved excerpt.',citations:[]}),{headers:{'content-type':'application/json'}}));
  const {result}=renderHook(()=>useChat());
  await act(async()=>{await Promise.all([result.current.sendMessage('first'),result.current.sendMessage('duplicate')]);});
  expect(fetchMock).toHaveBeenCalledTimes(1);
  expect(fetchMock.mock.calls[0][1].cache).toBe('no-store');
 });
 it('treats an empty JSON answer as failure and retains the question for retry',async()=>{
  fetchMock.mockResolvedValue(new Response(JSON.stringify({generated_text:'  '}),{headers:{'content-type':'application/json'}}));
  const {result}=renderHook(()=>useChat());
  await act(async()=>{await result.current.sendMessage('Keep my question');});
  expect(result.current.error).not.toBeNull();
  expect(result.current.messages[0].content).toBe('Keep my question');
  expect(result.current.messages.at(-1)?.status).toBe('error');
 });
 it('decodes an SSE final line without a newline and calls onFinish once',async()=>{
  const finish=vi.fn();
  const bytes=new TextEncoder().encode('data: {"text":"বাংলা saved answer"}');
  fetchMock.mockResolvedValue(new Response(new ReadableStream({start(controller){controller.enqueue(bytes.slice(0,25));controller.enqueue(bytes.slice(25));controller.close();}}),{headers:{'content-type':'text/event-stream'}}));
  const {result}=renderHook(()=>useChat({onFinish:finish}));
  await act(async()=>{await result.current.sendMessage('What was saved?');});
  expect(result.current.messages.at(-1)?.content).toBe('বাংলা saved answer');
  expect(finish).toHaveBeenCalledTimes(1);
 });
 it('cannot resurrect an answer after Stop even if a transport ignores abort',async()=>{
  let resolveResponse:(value:Response)=>void=()=>{};
  fetchMock.mockReturnValue(new Promise<Response>(resolve=>{resolveResponse=resolve;}));
  const {result}=renderHook(()=>useChat());let pending:Promise<void>;
  act(()=>{pending=result.current.sendMessage('Stop this answer');});
  await waitFor(()=>expect(fetchMock).toHaveBeenCalledTimes(1));
  act(()=>result.current.stop());
  await act(async()=>{resolveResponse(new Response(JSON.stringify({generated_text:'Late stale answer'}),{headers:{'content-type':'application/json'}}));await pending;});
  expect(result.current.isLoading).toBe(false);
  expect(result.current.messages.at(-1)?.content).toBe('Answer stopped.');
 });
});

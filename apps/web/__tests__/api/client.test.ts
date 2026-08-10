import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { FastApiClient } from '@/lib/api/client';

describe('FastAPI REST Client & Error Parsing', () => {
  const originalFetch = global.fetch;
  const mockFetch = vi.fn();

  beforeEach(() => {
    global.fetch = mockFetch as unknown as typeof fetch;
    vi.clearAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('unwraps data field from standard FastAPI response', async () => {
    const fakeResponse = {
      data: { id: 'venture-101', title: 'Neural Operating System', status: 'ACTIVE' },
      meta: { timestamp: 1722800000 },
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => fakeResponse,
    });

    const client = new FastApiClient(async () => 'mock.jwt.token', 'https://api.test/api/v1');
    const result = await client.get<{ id: string; title: string; status: string }>('/ventures/101');

    expect(result).toEqual(fakeResponse.data);
    expect(mockFetch).toHaveBeenCalledWith('https://api.test/api/v1/ventures/101', expect.objectContaining({
      method: 'GET',
      headers: expect.objectContaining({
        'Authorization': 'Bearer mock.jwt.token',
      }),
    }));
  });

  it('throws structured ApiError with error code and request_id upon failure', async () => {
    const fakeErrorResponse = {
      error: {
        code: 'ERR_VENTURE_LOCKED',
        message: 'Insufficient operator authorization to edit target venture.',
        request_id: 'req-fastapi-998877',
      },
    };

    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 403,
      statusText: 'Forbidden',
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => fakeErrorResponse,
    });

    const client = new FastApiClient(async () => null, 'https://api.test/api/v1');

    await expect(client.post('/ventures/101/edit', { title: 'New Name' })).rejects.toMatchObject({
      status: 403,
      code: 'ERR_VENTURE_LOCKED',
      message: 'Insufficient operator authorization to edit target venture.',
      requestId: 'req-fastapi-998877',
    });
  });
});

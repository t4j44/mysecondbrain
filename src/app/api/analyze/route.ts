import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'edge';

/**
 * Route Handler for `/api/analyze`
 * Streams real-time SSE AI Founder Coach responses with RAG citations
 */
export async function POST(req: NextRequest) {
  try {
    const { prompt } = await req.json();

    const textEncoder = new TextEncoder();

    // Simulated Founder Intelligence streaming tokens & citations based on prompt
    const responseStream = new ReadableStream({
      async start(controller) {
        // 1. Initial Vercel AI Data-Stream frame
        controller.enqueue(
          textEncoder.encode(`f:{"conversationId":"conv-${Date.now()}","model":"gemini-1.5-pro"}\n`)
        );

        // 2. Citation frame
        const citation = {
          id: 'mem-104',
          entity_type: 'interaction',
          title: 'Yousuf Imran Mentor Session',
          uri: '/people/yousuf-imran#interaction-104',
        };
        controller.enqueue(textEncoder.encode(`e:${JSON.stringify(citation)}\n`));

        // Simulated thinking pause
        await new Promise((r) => setTimeout(r, 600));

        // Response chunks
        const responseChunks = [
          `Analysis complete for your prompt: "${prompt || 'General Founder Status'}".\n\n`,
          `Based on stored RAG context from your venture **Justor AI** and recent discussions with mentor Yousuf Imran:\n\n`,
          `1. **Primary Bottleneck**: Execution speed on MVP validation and customer acquisition pipeline.\n`,
          `2. **Strategic Action**: Narrow feature scope to legal document summarization before launching broad marketing campaigns.\n`,
          `3. **Relationship Touchpoint**: Share product roadmap update with Yousuf Imran before Friday.\n\n`,
          `Your Second Brain will keep monitoring task velocity across active ventures. Let me know if you would like me to draft a LinkedIn update or generate a weekly review!`,
        ];

        for (const chunk of responseChunks) {
          controller.enqueue(textEncoder.encode(`0:${JSON.stringify(chunk)}\n`));
          await new Promise((r) => setTimeout(r, 200));
        }

        // Usage billing metrics frame
        controller.enqueue(
          textEncoder.encode(
            `d:${JSON.stringify({ finishReason: 'stop', usage: { promptTokens: 64, completionTokens: 120 } })}\n`
          )
        );

        controller.close();
      },
    });

    return new NextResponse(responseStream, {
      headers: {
        'Content-Type': 'text/event-stream; charset=utf-8',
        'Cache-Control': 'no-cache, no-transform',
        Connection: 'keep-alive',
      },
    });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}

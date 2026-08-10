'use client';

import React from 'react';
import ChatArea from '../../components/chat/ChatArea';

export default function ChatDemoPage() {
  return (
    <main className="min-h-screen bg-slate-950 p-4 sm:p-8 flex flex-col items-center justify-center">
      <div className="w-full max-w-5xl space-y-4">
        <div className="text-center space-y-2 mb-6">
          <h1 className="text-3xl font-extrabold text-white tracking-tight font-mono">
            TAJ'S SECOND BRAIN // CHAT TERMINAL
          </h1>
          <p className="text-sm text-slate-400">
            Interactive demo of the <code className="text-purple-300">ChatArea</code> component connected to <code className="text-purple-300">useChat</code> hook and <code className="text-purple-300">/api/analyze</code> stream endpoint.
          </p>
        </div>

        <ChatArea api="/api/analyze" />
      </div>
    </main>
  );
}

import * as React from 'react';
import Link from 'next/link';
import { Terminal } from 'lucide-react';

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-[#12081d] text-[#f7f4ea] font-sans">
      {/* Left Column - Founder Philosophy & Terminal Branding */}
      <div className="hidden lg:flex w-1/2 flex-col justify-between border-r border-[#251238] bg-[#0a0510] p-12 relative overflow-hidden">
        {/* Subtle Decorative Grid Background */}
        <div className="absolute inset-0 bg-[radial-gradient(#251238_1px,transparent_1px)] [background-size:24px_24px] opacity-30 pointer-events-none" />
        
        <div className="relative z-10 flex items-center space-x-3">
          <div className="h-10 w-10 rounded-lg bg-[#00ff9d]/10 border border-[#00ff9d] flex items-center justify-center text-[#00ff9d] shadow-[0_0_15px_rgba(0,255,157,0.2)]">
            <Terminal className="h-5 w-5" />
          </div>
          <div>
            <span className="text-xl font-bold font-sans tracking-tight text-[#f7f4ea]">Taj’s Second Brain</span>
            <span className="block text-xs font-mono text-[#00ff9d] uppercase tracking-widest">OS / v2.0 // FOUNDER TERMINAL</span>
          </div>
        </div>

        <div className="relative z-10 my-auto max-w-md space-y-6">
          <div className="inline-block rounded-full bg-[#251238] px-3 py-1 text-xs font-mono text-[#00ff9d] border border-[#00ff9d]/30">
            [ SYSTEM STATUS: ONLINE & PREDICTIVE ]
          </div>
          <h1 className="text-4xl font-extrabold leading-tight tracking-tight font-sans text-cream">
            AI-Native OS for Multi-Venture Mastery & Execution.
          </h1>
          <p className="text-base text-muted-foreground leading-relaxed">
            Synthesize your network, automate repetitive operational overhead, and harness proactive intelligence across all your high-velocity projects and ventures.
          </p>

          <div className="pt-4 border-t border-[#251238]/60 flex items-center space-x-6 text-xs font-mono text-muted-foreground">
            <div><strong className="text-[#f7f4ea] block">ZERO DATA LEAKS</strong> RLS Isolated Security</div>
            <div><strong className="text-[#00ff9d] block">REAL-TIME</strong> RAG & Graph Insights</div>
          </div>
        </div>

        <div className="relative z-10 flex items-center justify-between text-xs text-muted-foreground font-mono">
          <span>© 2026 Taj’s Second Brain. All rights reserved.</span>
          <Link href="https://tajssecondbrain.ai/privacy" className="hover:text-[#00ff9d] transition-colors">
            Privacy Protocol
          </Link>
        </div>
      </div>

      {/* Right Column - Authentication Interfaces */}
      <div className="flex w-full lg:w-1/2 items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-md space-y-8">
          <div className="lg:hidden flex items-center space-x-3 mb-8">
            <div className="h-9 w-9 rounded bg-[#00ff9d]/10 border border-[#00ff9d] flex items-center justify-center text-[#00ff9d]">
              <Terminal className="h-5 w-5" />
            </div>
            <span className="text-lg font-bold">Taj’s Second Brain</span>
          </div>
          {children}
        </div>
      </div>
    </div>
  );
}

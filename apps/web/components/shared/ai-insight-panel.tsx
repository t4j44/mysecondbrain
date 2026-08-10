import * as React from 'react';
import { Sparkles, Brain, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface AIInsightPanelProps {
  title?: string;
  insight: string;
  confidence?: number;
  sourceCount?: number;
  onAction?: () => void;
  actionLabel?: string;
  className?: string;
}

export function AIInsightPanel({
  title = 'RAG GROUNDED INTELLIGENCE',
  insight,
  confidence = 94,
  sourceCount = 3,
  onAction,
  actionLabel = 'APPLY TO VENTURE',
  className = '',
}: AIInsightPanelProps) {
  return (
    <div className={`rounded-lg border border-[#00ff9d]/40 bg-[#0d0716] p-6 shadow-[0_0_25px_rgba(0,255,157,0.1)] relative overflow-hidden my-6 ${className}`}>
      {/* Decorative neon corner accent */}
      <div className="absolute top-0 right-0 h-12 w-12 bg-gradient-to-bl from-[#00ff9d]/20 to-transparent pointer-events-none" />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[#251238] gap-2">
        <div className="flex items-center space-x-2.5">
          <div className="h-8 w-8 rounded-md bg-[#00ff9d]/15 border border-[#00ff9d] flex items-center justify-center text-[#00ff9d]">
            <Sparkles className="h-4 w-4 animate-pulse-slow" />
          </div>
          <div>
            <span className="text-xs font-mono font-bold text-[#00ff9d] uppercase tracking-widest block">
              [ {title} ]
            </span>
            <span className="text-[11px] font-mono text-muted-foreground block">
              Synthesized via Vector RAG // Zero-Hallucination Protocol
            </span>
          </div>
        </div>

        <div className="flex items-center space-x-3 text-xs font-mono text-muted-foreground">
          <div className="flex items-center space-x-1" title="Confidence rating based on vector relevance distance">
            <Brain className="h-3.5 w-3.5 text-[#00ff9d]" />
            <span>Conf: <strong className="text-[#f7f4ea]">{confidence}%</strong></span>
          </div>
          <span>•</span>
          <span>Sources: <strong className="text-[#f7f4ea]">{sourceCount}</strong></span>
        </div>
      </div>

      <div className="py-4">
        <p className="text-sm font-sans text-cream leading-relaxed whitespace-pre-wrap">
          {insight}
        </p>
      </div>

      {onAction && (
        <div className="pt-2 border-t border-[#251238]/80 flex justify-end">
          <Button
            onClick={onAction}
            variant="terminal"
            className="text-xs h-9 font-mono tracking-wider font-semibold"
          >
            {actionLabel}
            <ArrowRight className="ml-2 h-3.5 w-3.5" />
          </Button>
        </div>
      )}
    </div>
  );
}

import React from 'react';

export default function DashboardSkeleton() {
  return (
    <div className="space-y-6 animate-pulse font-mono">
      {/* Header bar placeholder */}
      <div className="h-20 bg-terminal-panel border border-terminal-border rounded-xl p-5 flex flex-col justify-between" />

      {/* Mission card placeholder */}
      <div className="h-24 bg-terminal-panel border border-terminal-border rounded-xl" />

      {/* Numerical count summaries */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-16 bg-terminal-panel border border-terminal-border rounded-xl" />
        ))}
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 columns: Focus, Projects, Ventures */}
        <div className="lg:col-span-2 space-y-6">
          <div className="h-56 bg-terminal-panel border border-terminal-border rounded-xl" />
          <div className="h-64 bg-terminal-panel border border-terminal-border rounded-xl" />
          <div className="h-64 bg-terminal-panel border border-terminal-border rounded-xl" />
        </div>

        {/* Right column: AI insights, CRM, Calendar */}
        <div className="space-y-6">
          <div className="h-56 bg-terminal-panel border border-terminal-border rounded-xl" />
          <div className="h-44 bg-terminal-panel border border-terminal-border rounded-xl" />
          <div className="h-44 bg-terminal-panel border border-terminal-border rounded-xl" />
          <div className="h-44 bg-terminal-panel border border-terminal-border rounded-xl" />
        </div>
      </div>
    </div>
  );
}

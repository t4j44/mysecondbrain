'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  AlertCircle, 
  Calendar, 
  TrendingUp, 
  TrendingDown, 
  Brain, 
  Users, 
  RefreshCw, 
  Sparkles,
  Link2,
  Lock
} from 'lucide-react';
import { Card, Button } from '../ui/CustomUi';
import { mockApi } from '../../lib/mockApi';
import { AIInsights } from '../../types/execution';

// --- Task Summary Card ---
interface TaskSummaryCardProps {
  counts: {
    today: number;
    overdue: number;
    upcoming: number;
    completed: number;
  };
}

export const TaskSummaryCard: React.FC<TaskSummaryCardProps> = ({ counts }) => {
  const items = [
    { label: 'Due Today', count: counts.today, href: '/tasks?filter=today', color: 'text-white' },
    { label: 'Overdue', count: counts.overdue, href: '/tasks?filter=today', color: 'text-terminal-alert font-bold' },
    { label: 'Upcoming', count: counts.upcoming, href: '/tasks?filter=upcoming', color: 'text-terminal-muted' },
    { label: 'Completed', count: counts.completed, href: '/tasks?filter=completed', color: 'text-terminal-accent' },
  ];

  return (
    <Card className="grid grid-cols-2 sm:grid-cols-4 gap-4 divide-y-0 sm:divide-x divide-terminal-border/20">
      {items.map((item, idx) => (
        <Link 
          key={idx} 
          href={item.href}
          className="flex flex-col items-center justify-center p-2 text-center group hover:bg-terminal-fg/5 rounded-lg transition-all"
        >
          <span className="text-[10px] uppercase font-mono tracking-wider text-terminal-muted mb-1">{item.label}</span>
          <span className={`text-2xl font-mono ${item.color} group-hover:scale-105 transition-transform`}>
            {item.count}
          </span>
        </Link>
      ))}
    </Card>
  );
};

// --- KPI Overview Card ---
interface KPIOverviewCardProps {
  kpis: Array<{
    metric_name: string;
    current_value: number;
    target_value: number;
    unit: string;
  }>;
}

export const KPIOverviewCard: React.FC<KPIOverviewCardProps> = ({ kpis }) => {
  return (
    <Card 
      header={
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <TrendingUp size={14} className="text-terminal-accent" />
            <span className="font-mono text-xs font-bold text-white uppercase tracking-wider">KPI Highlights</span>
          </div>
          <Link href="/kpis" className="text-[10px] font-mono text-terminal-accent hover:underline">
            View All &rarr;
          </Link>
        </div>
      }
    >
      <div className="space-y-4">
        {kpis.slice(0, 3).map((kpi, idx) => {
          const pct = Math.min(100, Math.round((kpi.current_value / kpi.target_value) * 100));
          return (
            <div key={idx} className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="font-medium text-terminal-fg">{kpi.metric_name}</span>
                <span className="font-mono text-terminal-muted">
                  {kpi.current_value}/{kpi.target_value}{kpi.unit === 'count' ? '' : kpi.unit} ({pct}%)
                </span>
              </div>
              <div className="w-full bg-terminal-panel h-1.5 rounded-full overflow-hidden border border-terminal-border">
                <div 
                  className="bg-terminal-accent h-full rounded-full transition-all duration-500" 
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};

// --- Recent Memories Preview ---
interface RecentMemoriesPanelProps {
  memories: Array<{
    id: string;
    title: string;
    category?: string;
    created_at: string;
  }>;
}

export const RecentMemoriesPanel: React.FC<RecentMemoriesPanelProps> = ({ memories }) => {
  return (
    <Card 
      header={
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <Brain size={14} className="text-terminal-accent" />
            <span className="font-mono text-xs font-bold text-white uppercase tracking-wider">Recent Memories</span>
          </div>
          <Link href="/memories" className="text-[10px] font-mono text-terminal-accent hover:underline">
            Search Stream &rarr;
          </Link>
        </div>
      }
    >
      <div className="space-y-3 font-sans">
        {memories.slice(0, 3).map((mem) => (
          <div key={mem.id} className="text-xs border-b border-terminal-border/10 pb-2 last:border-b-0 last:pb-0">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[9px] uppercase px-1 rounded bg-terminal-fg/5 text-terminal-muted border border-terminal-border/20">
                {mem.category || 'Capture'}
              </span>
              <span className="text-[9px] text-terminal-muted font-mono">
                {new Date(mem.created_at).toLocaleDateString(undefined, {month: 'short', day: 'numeric'})}
              </span>
            </div>
            <p className="mt-1 text-terminal-fg leading-relaxed truncate font-medium">
              {mem.title}
            </p>
          </div>
        ))}
      </div>
    </Card>
  );
};

// --- Relationship Follow-Ups Preview ---
interface RelationshipFollowUpsPanelProps {
  followUps: Array<{
    id: string;
    name: string;
    role?: string;
    follow_up_date: string;
    next_action?: string;
    overdue: boolean;
  }>;
}

export const RelationshipFollowUpsPanel: React.FC<RelationshipFollowUpsPanelProps> = ({ followUps }) => {
  return (
    <Card 
      header={
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <Users size={14} className="text-terminal-accent" />
            <span className="font-mono text-xs font-bold text-white uppercase tracking-wider">CRM Follow-ups</span>
          </div>
          <Link href="/people" className="text-[10px] font-mono text-terminal-accent hover:underline">
            Network &rarr;
          </Link>
        </div>
      }
    >
      <div className="space-y-3 font-sans">
        {followUps.slice(0, 3).map((item) => (
          <div key={item.id} className="flex items-start justify-between gap-3 text-xs border-b border-terminal-border/10 pb-2 last:border-b-0 last:pb-0">
            <div>
              <p className="font-bold text-terminal-fg leading-snug">{item.name}</p>
              {item.next_action && (
                <p className="text-[10px] text-terminal-muted truncate mt-0.5 max-w-[140px]">{item.next_action}</p>
              )}
            </div>
            {item.overdue ? (
              <span className="text-[9px] px-1 bg-terminal-alert/10 border border-terminal-alert/30 text-terminal-alert rounded font-mono animate-pulse">
                OVERDUE
              </span>
            ) : (
              <span className="text-[9px] text-terminal-muted font-mono">
                Today
              </span>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
};

// --- Calendar & Warnings ---
interface CalendarPreviewProps {
  events: Array<{
    id: string;
    title: string;
    time: string;
    duration?: number;
    source?: string;
  }>;
  isConnected: boolean;
}

export const CalendarPreview: React.FC<CalendarPreviewProps> = ({ events, isConnected }) => {
  if (!isConnected) {
    return (
      <Card 
        header={
          <div className="flex items-center gap-2">
            <Calendar size={14} className="text-terminal-accent" />
            <span className="font-mono text-xs font-bold text-white uppercase tracking-wider">Upcoming Events</span>
          </div>
        }
      >
        <div className="py-4 text-center space-y-3">
          <Lock className="w-7 h-7 text-terminal-muted mx-auto" />
          <p className="text-xs text-terminal-muted leading-relaxed max-w-[200px] mx-auto">
            Google Calendar integration not connected. Link your schedule.
          </p>
          <Link href="/settings">
            <Button size="sm" className="w-full text-[10px] font-mono py-1.5">
              <Link2 size={12} className="mr-1.5" /> CONNECT CALENDAR
            </Button>
          </Link>
        </div>
      </Card>
    );
  }

  return (
    <Card 
      header={
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <Calendar size={14} className="text-terminal-accent" />
            <span className="font-mono text-xs font-bold text-white uppercase tracking-wider">Google Schedule</span>
          </div>
          <span className="text-[9px] text-terminal-accent bg-terminal-accent/5 px-1 border border-terminal-accent/20 rounded font-mono">SYNCED</span>
        </div>
      }
    >
      <div className="space-y-3 font-sans">
        {events.length === 0 ? (
          <p className="text-xs text-terminal-muted italic py-2 text-center">No meetings scheduled today.</p>
        ) : (
          events.map(event => {
            const timeStr = new Date(event.time).toLocaleTimeString(undefined, {hour: '2-digit', minute:'2-digit', hour12: false});
            return (
              <div key={event.id} className="text-xs border-b border-terminal-border/10 pb-2 last:border-b-0 last:pb-0">
                <div className="flex justify-between items-baseline">
                  <span className="font-mono font-bold text-terminal-fg text-[11px] truncate max-w-[130px]">{event.title}</span>
                  <span className="font-mono text-[10px] text-terminal-accent">{timeStr}</span>
                </div>
                <span className="text-[9px] text-terminal-muted font-mono">{event.duration} mins</span>
              </div>
            );
          })
        )}
      </div>
    </Card>
  );
};

// --- AI Insight Panel ---
export const AIInsightPanel: React.FC = () => {
  const [insight, setInsight] = useState<AIInsights | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchInsight = async () => {
    setLoading(true);
    try {
      const data = await mockApi.getDashboardInsights();
      setInsight(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInsight();
  }, []);

  return (
    <Card 
      header={
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <Sparkles size={15} className="text-terminal-accent animate-pulse" />
            <span className="font-mono text-xs font-bold text-white uppercase tracking-wider">AI Executive Advisor</span>
          </div>
          <button 
            onClick={fetchInsight}
            disabled={loading}
            className={`text-terminal-muted hover:text-terminal-accent transition-colors ${loading ? 'animate-spin' : ''}`}
            title="Refresh Advisor Insights"
          >
            <RefreshCw size={12} />
          </button>
        </div>
      }
    >
      {loading ? (
        <div className="py-8 text-center text-xs font-mono text-terminal-muted animate-pulse">
          Ingesting RAG context memory, auditing compliance checklists...
        </div>
      ) : insight ? (
        <div className="space-y-4 font-sans">
          {/* Main Insight */}
          <div className="p-3 bg-terminal-accent/5 border border-terminal-accent/15 rounded-lg">
            <p className="text-xs text-terminal-fg leading-relaxed">
              "{insight.ai_insight}"
            </p>
          </div>
          
          {/* Recommendations checklist */}
          <div className="space-y-2">
            <h4 className="font-mono text-[10px] text-terminal-muted uppercase tracking-wider">Recommended Next Actions:</h4>
            <ul className="space-y-2">
              {insight.recommended_actions.map((act, i) => (
                <li key={i} className="text-xs flex items-start gap-2 text-terminal-fg leading-snug">
                  <span className="text-terminal-accent mt-0.5 font-bold font-mono">&#8250;</span>
                  <span>{act}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}
    </Card>
  );
};

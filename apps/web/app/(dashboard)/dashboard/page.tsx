'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import {
  Sparkles,
  CheckCircle2,
  Circle,
  Calendar,
  Clock,
  ArrowRight,
  Flame,
  UserCheck,
  AlertTriangle,
  Plus,
  Send,
  Bot,
  Brain,
  CheckSquare,
  Users,
  Compass,
} from 'lucide-react';
import { ResponsivePageContainer } from '@/components/shared/responsive-page-container';
import { PageHeader } from '@/components/shared/page-header';
import { AIInsightPanel } from '@/components/shared/ai-insight-panel';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';
import { api } from '@/lib/api/browser-client';
import { WorkSessionModal } from '@/components/session/work-session-modal';

interface TodayTask {
  id: string;
  title: string;
  priority: 'urgent' | 'high' | 'medium' | 'low';
  completed: boolean;
  due_date?: string;
  project?: string;
  tags?: string[];
}

interface TodayMeeting {
  id: string;
  title: string;
  time: string;
  attendees: string[];
  location?: string;
}

interface TodayFollowUp {
  id: string;
  person_name: string;
  company?: string;
  context: string;
  days_ago: number;
}

export default function TodayDashboardPage() {
  const router = useRouter();
  const { toast } = useToast();

  // Quick inline capture input state
  const [quickInput, setQuickInput] = React.useState('');
  const [sessionModalOpen, setSessionModalOpen] = React.useState(false);

  // Today's Operational State (with rich defaults & optimistic mutations)
  const [tasks, setTasks] = React.useState<TodayTask[]>([
    {
      id: 'task-1',
      title: 'Review Seed Round Term Sheet & Investor Updates for Justor AI',
      priority: 'urgent',
      completed: false,
      due_date: 'Today 3:00 PM',
      project: 'Fundraising',
      tags: ['#p0', '#investors'],
    },
    {
      id: 'task-2',
      title: 'Finalize core vector RAG indexing pipeline architecture',
      priority: 'high',
      completed: false,
      due_date: 'Today 5:00 PM',
      project: 'Second Brain OS',
      tags: ['#engineering'],
    },
    {
      id: 'task-3',
      title: 'Prepare discussion agenda for advisor sync with Yousuf Imran',
      priority: 'medium',
      completed: false,
      due_date: 'Today 6:30 PM',
      project: 'Mentorship',
      tags: ['#network'],
    },
  ]);

  const [meetings] = React.useState<TodayMeeting[]>([
    {
      id: 'meet-1',
      title: 'Advisor Strategy Sync',
      time: '6:30 PM (45m)',
      attendees: ['Yousuf Imran (AI Mentor)'],
      location: 'Google Meet',
    },
    {
      id: 'meet-2',
      title: 'Founder Architecture Review',
      time: '8:00 PM (30m)',
      attendees: ['Internal Core Team'],
      location: 'Terminal Room',
    },
  ]);

  const [followUps, setFollowUps] = React.useState<TodayFollowUp[]>([
    {
      id: 'fu-1',
      person_name: 'Dr. Aris Thorne',
      company: 'HealthTech AI',
      context: 'Follow up regarding clinical dataset evaluation rights',
      days_ago: 3,
    },
    {
      id: 'fu-2',
      person_name: 'Sarah Chen',
      company: 'Sequoia Venture Scout',
      context: 'Send updated traction metrics deck',
      days_ago: 5,
    },
  ]);

  const [accomplishments, setAccomplishments] = React.useState<string[]>([
    'Deployed SQLite/PostgreSQL schema alignment tests',
    'Configured PWA mobile standalone manifest & safe-area insets',
  ]);

  // Suggested 1 primary focus (to defeat ADHD choice paralysis)
  const primaryFocus = tasks.find((t) => !t.completed && t.priority === 'urgent') || tasks.find((t) => !t.completed) || null;

  // Toggle task completion
  const handleToggleTask = (taskId: string) => {
    setTasks((prev) =>
      prev.map((t) => {
        if (t.id === taskId) {
          const nextCompleted = !t.completed;
          if (nextCompleted) {
            setAccomplishments((acc) => [t.title, ...acc]);
            toast({
              title: '🔥 Task Finished!',
              description: `"${t.title}" added to daily accomplishments.`,
            });
          }
          return { ...t, completed: nextCompleted };
        }
        return t;
      })
    );
  };

  // 1-tap follow up done
  const handleCompleteFollowUp = (fuId: string, name: string) => {
    setFollowUps((prev) => prev.filter((f) => f.id !== fuId));
    setAccomplishments((acc) => [`Followed up with ${name}`, ...acc]);
    toast({
      title: '✓ Contact Logged',
      description: `Follow-up with ${name} resolved.`,
    });
  };

  // Quick inline capture submit
  const handleQuickCapture = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!quickInput.trim()) return;

    const text = quickInput.trim();
    setQuickInput('');

    // Optimistically add to Today's Tasks
    const newTask: TodayTask = {
      id: `task-${Date.now()}`,
      title: text.replace(/#[a-zA-Z0-9_-]+/g, '').trim(),
      priority: text.includes('#urgent') ? 'urgent' : text.includes('#high') ? 'high' : 'medium',
      completed: false,
      due_date: 'Today',
      tags: text.match(/#[a-zA-Z0-9_-]+/g) || ['#today'],
    };

    setTasks((prev) => [newTask, ...prev]);

    try {
      await api.post('/api/v1/tasks', {
        title: newTask.title,
        description: text,
        priority: newTask.priority,
        due_date: new Date().toISOString(),
      });
      toast({
        title: '✓ Captured to Today',
        description: `"${newTask.title}" scheduled.`,
      });
    } catch {
      toast({
        title: '✓ Added Locally',
        description: `"${newTask.title}" queued for today.`,
      });
    }
  };

  return (
    <ResponsivePageContainer>
      {/* TODAY Header with Quick Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-[#251238]/80">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-mono text-[#00ff9d] uppercase tracking-widest font-bold">
              SURFACE 01 // TODAY
            </span>
            <span className="h-1.5 w-1.5 rounded-full bg-[#00ff9d] animate-pulse" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-mono font-extrabold text-[#f7f4ea] tracking-tight uppercase mt-0.5">
            Command Center
          </h1>
          <p className="text-xs text-muted-foreground font-sans mt-0.5">
            {new Date().toLocaleDateString('en-US', {
              weekday: 'long',
              month: 'long',
              day: 'numeric',
              year: 'numeric',
            })}{' '}
            • Automatic daily triage
          </p>
        </div>

        <div className="flex items-center gap-2.5 w-full sm:w-auto">
          <Button
            onClick={() => setSessionModalOpen(true)}
            variant="outline"
            className="flex-1 sm:flex-none border-[#00ff9d]/30 text-[#00ff9d] hover:bg-[#00ff9d]/10 font-mono text-xs font-bold min-h-[44px]"
          >
            <Flame className="h-4 w-4 mr-1.5 text-[#00ff9d]" />
            FINALIZE SESSION
          </Button>

          <Button
            onClick={() => router.push('/assistant')}
            variant="terminal"
            className="flex-1 sm:flex-none font-mono text-xs font-bold min-h-[44px]"
          >
            <Bot className="h-4 w-4 mr-1.5 text-[#0a0510]" />
            ASK BRAIN
          </Button>
        </div>
      </div>

      {/* 1-Tap Quick Capture Bar at top */}
      <form onSubmit={handleQuickCapture} className="my-5">
        <div className="relative flex items-center">
          <input
            type="text"
            value={quickInput}
            onChange={(e) => setQuickInput(e.target.value)}
            placeholder="Dump a task, thought, or note... (e.g. 'Draft pitch slides #urgent by 4pm')"
            className="w-full bg-[#0e0716] border border-[#3b1e5a] focus:border-[#00ff9d] focus:ring-1 focus:ring-[#00ff9d] text-sm sm:text-base text-[#f7f4ea] placeholder:text-muted-foreground/60 pl-4 pr-24 py-3.5 rounded-xl outline-none shadow-[0_4px_25px_rgba(0,0,0,0.4)]"
          />
          <button
            type="submit"
            disabled={!quickInput.trim()}
            className="absolute right-2 px-4 py-2 rounded-lg bg-[#00ff9d] text-[#0a0510] font-mono text-xs font-bold uppercase hover:bg-[#00e08a] transition-all disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-1.5 min-h-[36px]"
          >
            <span>Add</span>
            <Plus className="h-3.5 w-3.5 stroke-[3]" />
          </button>
        </div>
      </form>

      {/* SUGGESTED PRIMARY FOCUS (Single Anchor for ADHD) */}
      {primaryFocus && (
        <div className="rounded-2xl border-2 border-[#00ff9d]/40 bg-gradient-to-r from-[#00ff9d]/10 via-[#190c28] to-[#0a0510] p-4 sm:p-5 shadow-[0_0_30px_rgba(0,255,157,0.1)] mb-6">
          <div className="flex items-start sm:items-center justify-between gap-3 flex-wrap">
            <div className="flex items-start sm:items-center space-x-3.5">
              <div className="h-10 w-10 rounded-xl bg-[#00ff9d] text-[#0a0510] flex items-center justify-center font-bold shadow-[0_0_15px_rgba(0,255,157,0.4)] shrink-0 mt-0.5 sm:mt-0">
                <Compass className="h-5 w-5 stroke-[2.5]" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono uppercase font-bold text-[#00ff9d] tracking-wider">
                    SUGGESTED PRIMARY FOCUS
                  </span>
                  <span className="text-[9px] font-mono bg-[#00ff9d]/20 text-[#00ff9d] px-1.5 py-0.2 rounded border border-[#00ff9d]/30">
                    ONE THING
                  </span>
                </div>
                <h3 className="text-base sm:text-lg font-bold text-[#f7f4ea] mt-0.5 leading-snug">
                  {primaryFocus.title}
                </h3>
              </div>
            </div>

            <button
              onClick={() => handleToggleTask(primaryFocus.id)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#00ff9d] hover:bg-[#00e08a] text-[#0a0510] font-mono text-xs font-bold uppercase transition-all shadow-[0_0_15px_rgba(0,255,157,0.3)] min-h-[40px]"
            >
              <CheckCircle2 className="h-4 w-4" />
              <span>Complete Now</span>
            </button>
          </div>
        </div>
      )}

      {/* Main Grid: Priority Tasks (Left) & Today's Schedule + Follow-ups (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 Cols): Tasks & Accomplishments */}
        <div className="lg:col-span-2 space-y-6">
          {/* Priority Execution Queue */}
          <div className="rounded-2xl border border-[#251238] bg-[#0a0510] p-4 sm:p-6 shadow-xl">
            <div className="flex items-center justify-between pb-4 border-b border-[#251238]/80 mb-4">
              <div className="flex items-center space-x-2.5">
                <div className="h-7 w-7 rounded-lg bg-[#00ff9d]/10 border border-[#00ff9d]/40 flex items-center justify-center text-[#00ff9d]">
                  <CheckSquare className="h-4 w-4" />
                </div>
                <h2 className="text-base font-bold font-mono text-[#f7f4ea] uppercase">
                  Today’s Priority Tasks ({tasks.filter((t) => !t.completed).length})
                </h2>
              </div>
              <button
                onClick={() => router.push('/tasks')}
                className="text-xs font-mono text-[#00ff9d] hover:underline flex items-center gap-1"
              >
                <span>All Tasks</span>
                <ArrowRight className="h-3 w-3" />
              </button>
            </div>

            <div className="space-y-2.5">
              {tasks.map((task) => (
                <div
                  key={task.id}
                  onClick={() => handleToggleTask(task.id)}
                  className={`flex items-start justify-between p-3.5 rounded-xl border transition-all cursor-pointer group min-h-[52px] ${
                    task.completed
                      ? 'bg-[#0e0716]/60 border-[#251238]/40 opacity-60'
                      : 'bg-[#12081d] border-[#301642] hover:border-[#00ff9d]/60 hover:bg-[#180a26]'
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    <button
                      type="button"
                      className="mt-0.5 shrink-0 text-muted-foreground group-hover:text-[#00ff9d]"
                      aria-label={task.completed ? 'Mark task incomplete' : 'Mark task complete'}
                    >
                      {task.completed ? (
                        <CheckCircle2 className="h-5 w-5 text-[#00ff9d]" />
                      ) : (
                        <Circle className="h-5 w-5" />
                      )}
                    </button>

                    <div>
                      <p
                        className={`text-sm font-medium leading-snug transition-all ${
                          task.completed
                            ? 'line-through text-muted-foreground'
                            : 'text-[#f7f4ea] group-hover:text-white'
                        }`}
                      >
                        {task.title}
                      </p>

                      <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                        {task.project && (
                          <span className="text-[10px] font-mono text-purple-300 bg-purple-950/60 px-2 py-0.5 rounded border border-purple-500/20">
                            {task.project}
                          </span>
                        )}
                        {task.due_date && (
                          <span className="text-[10px] font-mono text-muted-foreground flex items-center gap-1">
                            <Clock className="h-3 w-3 text-muted-foreground" />
                            {task.due_date}
                          </span>
                        )}
                        {task.priority === 'urgent' && (
                          <span className="text-[9px] font-mono font-bold uppercase text-amber-400 bg-amber-400/10 px-1.5 py-0.2 rounded border border-amber-400/30">
                            URGENT
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Today's Accomplishments (Positive Reinforcement) */}
          <div className="rounded-2xl border border-[#251238] bg-[#0a0510] p-4 sm:p-6 shadow-xl">
            <div className="flex items-center space-x-2.5 pb-4 border-b border-[#251238]/80 mb-4">
              <div className="h-7 w-7 rounded-lg bg-emerald-500/10 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
                <Flame className="h-4 w-4 text-emerald-400" />
              </div>
              <h2 className="text-base font-bold font-mono text-[#f7f4ea] uppercase">
                Accomplishments & Momentum ({accomplishments.length})
              </h2>
            </div>

            <div className="space-y-2">
              {accomplishments.length === 0 ? (
                <p className="text-xs font-mono text-muted-foreground italic py-3">
                  Check off a task or complete a follow-up to build your momentum streak today.
                </p>
              ) : (
                accomplishments.map((item, idx) => (
                  <div
                    key={idx}
                    className="flex items-center space-x-2.5 p-2.5 rounded-lg bg-[#0e0716] border border-[#251238] text-xs font-sans text-slate-300"
                  >
                    <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                    <span>{item}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right Column (1 Col): Meetings & Follow-ups Queue */}
        <div className="space-y-6">
          {/* Today's Meetings */}
          <div className="rounded-2xl border border-[#251238] bg-[#0a0510] p-4 sm:p-6 shadow-xl">
            <div className="flex items-center justify-between pb-4 border-b border-[#251238]/80 mb-4">
              <div className="flex items-center space-x-2.5">
                <div className="h-7 w-7 rounded-lg bg-purple-500/10 border border-purple-500/40 flex items-center justify-center text-purple-400">
                  <Calendar className="h-4 w-4" />
                </div>
                <h2 className="text-sm font-bold font-mono text-[#f7f4ea] uppercase">
                  Schedule ({meetings.length})
                </h2>
              </div>
              <button
                onClick={() => router.push('/meetings')}
                className="text-xs font-mono text-purple-300 hover:underline"
              >
                Audio Log
              </button>
            </div>

            <div className="space-y-3">
              {meetings.map((m) => (
                <div
                  key={m.id}
                  className="p-3.5 rounded-xl bg-[#12081d] border border-[#301642] space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-[#f7f4ea]">{m.title}</span>
                    <span className="text-[10px] font-mono text-[#00ff9d] bg-[#00ff9d]/10 px-2 py-0.5 rounded border border-[#00ff9d]/20">
                      {m.time}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">{m.attendees.join(', ')}</p>
                  <div className="text-[10px] font-mono text-purple-300/80">{m.location}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Follow-ups Due */}
          <div className="rounded-2xl border border-[#251238] bg-[#0a0510] p-4 sm:p-6 shadow-xl">
            <div className="flex items-center justify-between pb-4 border-b border-[#251238]/80 mb-4">
              <div className="flex items-center space-x-2.5">
                <div className="h-7 w-7 rounded-lg bg-cyan-500/10 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
                  <Users className="h-4 w-4" />
                </div>
                <h2 className="text-sm font-bold font-mono text-[#f7f4ea] uppercase">
                  Follow-ups Due ({followUps.length})
                </h2>
              </div>
              <button
                onClick={() => router.push('/people')}
                className="text-xs font-mono text-cyan-300 hover:underline"
              >
                Network
              </button>
            </div>

            <div className="space-y-3">
              {followUps.length === 0 ? (
                <p className="text-xs font-mono text-muted-foreground italic py-3">
                  All connection follow-ups up to date.
                </p>
              ) : (
                followUps.map((fu) => (
                  <div
                    key={fu.id}
                    className="p-3.5 rounded-xl bg-[#12081d] border border-[#301642] space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-[#f7f4ea]">
                        {fu.person_name}
                      </span>
                      <span className="text-[10px] font-mono text-amber-400">
                        {fu.days_ago}d overdue
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground leading-snug">{fu.context}</p>

                    <div className="pt-1 flex items-center justify-end gap-2">
                      <button
                        onClick={() => handleCompleteFollowUp(fu.id, fu.person_name)}
                        className="px-2.5 py-1 rounded-lg bg-[#00ff9d]/10 hover:bg-[#00ff9d]/20 text-[#00ff9d] border border-[#00ff9d]/30 text-[11px] font-mono font-semibold transition-all"
                      >
                        ✓ Mark Contacted
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Work Session Finalizer Modal */}
      <WorkSessionModal
        isOpen={sessionModalOpen}
        onClose={() => setSessionModalOpen(false)}
        completedCount={accomplishments.length}
      />
    </ResponsivePageContainer>
  );
}

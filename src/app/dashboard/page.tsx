'use client';

import React, { useState, useEffect } from 'react';
import { 
  RefreshCw, 
  Terminal, 
  AlertCircle,
  HelpCircle,
  TrendingUp,
  Brain,
  Layers,
  Activity,
  Plus
} from 'lucide-react';
import LayoutShell from '../../components/layout/Sidebar';
import MissionCard from '../../components/dashboard/MissionCard';
import TodayFocusPanel from '../../components/dashboard/TodayFocusPanel';
import DashboardSkeleton from '../../components/dashboard/DashboardSkeleton';
import { 
  TaskSummaryCard, 
  KPIOverviewCard, 
  RecentMemoriesPanel, 
  RelationshipFollowUpsPanel, 
  CalendarPreview,
  AIInsightPanel
} from '../../components/dashboard/DashboardWidgets';
import { ActiveVenturesPanel, ProjectPulsePanel } from '../../components/dashboard/DashboardVentureProjectWidgets';
import { mockApi } from '../../lib/mockApi';
import { Venture, Project, Task, DashboardSummary } from '../../types/execution';
import { Button } from '../../components/ui/CustomUi';

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<any>(null);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  
  // Ventures and projects counts
  const [activeVentures, setActiveVentures] = useState<Venture[]>([]);
  const [activeProjects, setActiveProjects] = useState<Project[]>([]);
  
  // Task summary counts
  const [taskCounts, setTaskCounts] = useState({ today: 0, overdue: 0, upcoming: 0, completed: 0 });

  const loadData = async () => {
    setLoading(true);
    try {
      const profileData = await mockApi.getProfile();
      const summaryData = await mockApi.getDashboardSummary();
      const allVentures = await mockApi.getVentures();
      const allProjects = await mockApi.getProjects();
      const allTasks = await mockApi.getTasks();

      setProfile(profileData);
      setSummary(summaryData);
      setActiveVentures(allVentures.filter(v => v.status === 'active'));
      setActiveProjects(allProjects.filter(p => p.status === 'in_progress'));

      // Calculate task metrics
      const todayStr = new Date().toISOString().split('T')[0];
      const todayTasks = allTasks.filter(t => t.status !== 'done' && t.due_date && t.due_date.split('T')[0] === todayStr);
      const overdueTasks = allTasks.filter(t => t.status !== 'done' && t.due_date && t.due_date.split('T')[0] < todayStr);
      const upcomingTasks = allTasks.filter(t => t.status !== 'done' && t.due_date && t.due_date.split('T')[0] > todayStr);
      const completedTasks = allTasks.filter(t => t.status === 'done');

      setTaskCounts({
        today: todayTasks.length,
        overdue: overdueTasks.length,
        upcoming: upcomingTasks.length,
        completed: completedTasks.length
      });
    } catch (e) {
      console.error('Failed to load dashboard data', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    
    // Listen to data update events
    window.addEventListener('second-brain-data-updated', loadData);
    return () => window.removeEventListener('second-brain-data-updated', loadData);
  }, []);

  return (
    <LayoutShell>
      {loading ? (
        <DashboardSkeleton />
      ) : (
        <div className="space-y-6">
          {/* Header Bar */}
          <div className="flex flex-col sm:flex-row justify-between sm:items-center p-5 bg-terminal-panel border border-terminal-border rounded-xl gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-1.5 text-xs text-terminal-accent font-mono font-semibold">
                <Terminal size={14} className="animate-pulse" />
                <span>COMMAND CENTER ACTIVE</span>
              </div>
              <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white font-mono uppercase">
                Taj's Second Brain
              </h1>
              <p className="text-xs text-terminal-muted">
                Executive overview of startup ventures, project deliverables, and network CRM touches.
              </p>
            </div>
            <div className="flex gap-2">
              <Button size="sm" onClick={loadData} className="flex items-center gap-1.5">
                <RefreshCw size={13} />
                <span className="font-mono text-xs">REFRESH [F5]</span>
              </Button>
            </div>
          </div>

          {/* Primary Zone: Current Mission, Today's Focus */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              {/* Mission Card */}
              <MissionCard 
                initialMission={profile?.settings.current_mission} 
                onUpdate={(newMission) => {
                  setProfile((prev: any) => ({
                    ...prev,
                    settings: { ...prev.settings, current_mission: newMission }
                  }));
                }}
              />

              {/* Today's Focus Panel */}
              <TodayFocusPanel 
                tasks={summary?.today_focus_tasks || []} 
                onTaskUpdated={loadData}
              />
            </div>

            {/* Intelligence Zone: AI Advisor panel */}
            <div className="space-y-6">
              <AIInsightPanel />
            </div>
          </div>

          {/* Execution Zone: Task summary metrics, Active projects */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              {/* Numeric task counts dashboard links */}
              <TaskSummaryCard counts={taskCounts} />

              {/* Active Projects pulse */}
              <ProjectPulsePanel projects={activeProjects} />

              {/* Active Ventures Panel */}
              <ActiveVenturesPanel ventures={activeVentures} />
            </div>

            {/* Side Column: CRM summaries & Schedule events */}
            <div className="space-y-6">
              {/* Google Schedule */}
              <CalendarPreview 
                events={summary?.calendar_events_today || []} 
                isConnected={true} 
              />

              {/* CRM Followups list */}
              <RelationshipFollowUpsPanel 
                followUps={summary?.relationship_follow_ups || []} 
              />

              {/* Recent Memories stream */}
              <RecentMemoriesPanel 
                memories={summary?.recent_memory_stream || []} 
              />
            </div>
          </div>
        </div>
      )}
    </LayoutShell>
  );
}

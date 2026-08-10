'use client';

import React from 'react';
import Link from 'next/link';
import { Briefcase, FolderGit2, Calendar, Target, CheckSquare } from 'lucide-react';
import { Card, StatusBadge, PriorityBadge } from '../ui/CustomUi';
import { Venture, Project } from '../../types/execution';

// --- Active Ventures Panel ---
interface ActiveVenturesPanelProps {
  ventures: Venture[];
}

export const ActiveVenturesPanel: React.FC<ActiveVenturesPanelProps> = ({ ventures }) => {
  return (
    <Card
      header={
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <Briefcase size={14} className="text-terminal-accent" />
            <span className="font-mono text-xs font-bold text-white uppercase tracking-wider">Active Ventures</span>
          </div>
          <Link href="/ventures" className="text-[10px] font-mono text-terminal-accent hover:underline">
            Manage Portfolio &rarr;
          </Link>
        </div>
      }
    >
      {ventures.length === 0 ? (
        <p className="text-xs text-terminal-muted italic py-6 text-center">
          Create your first venture to define a mission and organize related projects.
        </p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {ventures.slice(0, 4).map(venture => (
            <Link 
              key={venture.id} 
              href={`/ventures/${venture.id}`}
              className="p-4 rounded-lg border border-terminal-border bg-terminal-panel/30 hover:border-terminal-accent/30 transition-all flex flex-col justify-between space-y-3 group"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <h4 className="font-mono font-bold text-sm text-white group-hover:text-terminal-accent transition-colors truncate">
                    {venture.name}
                  </h4>
                  <StatusBadge status={venture.status} />
                </div>
                {venture.mission && (
                  <p className="text-xs text-terminal-muted line-clamp-2 mt-1.5 font-sans leading-relaxed">
                    {venture.mission}
                  </p>
                )}
              </div>
              
              <div className="flex items-center justify-between pt-2 border-t border-terminal-border/10 text-[10px] font-mono text-terminal-muted">
                <span className="flex items-center gap-1">
                  <FolderGit2 size={12} /> {venture.project_count || 0} Projects
                </span>
                <span className="flex items-center gap-1">
                  <CheckSquare size={12} /> {venture.open_task_count || 0} Tasks
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </Card>
  );
};

// --- Project Pulse Panel ---
interface ProjectPulsePanelProps {
  projects: Array<Project & { venture_name?: string }>;
}

export const ProjectPulsePanel: React.FC<ProjectPulsePanelProps> = ({ projects }) => {
  return (
    <Card
      header={
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <FolderGit2 size={14} className="text-terminal-accent" />
            <span className="font-mono text-xs font-bold text-white uppercase tracking-wider">Project Pulse Tracker</span>
          </div>
          <Link href="/projects" className="text-[10px] font-mono text-terminal-accent hover:underline">
            Pipeline Pipelines &rarr;
          </Link>
        </div>
      }
    >
      {projects.length === 0 ? (
        <p className="text-xs text-terminal-muted italic py-6 text-center">
          Create a project to turn a venture goal into structured execution.
        </p>
      ) : (
        <div className="space-y-4">
          {projects.slice(0, 3).map(proj => {
            const isCompleted = proj.status === 'completed';
            return (
              <Link
                key={proj.id}
                href={`/projects/${proj.id}`}
                className="block p-3.5 rounded-lg border border-terminal-border bg-terminal-panel/20 hover:bg-terminal-panel/50 hover:border-terminal-accent/30 transition-all space-y-2 group"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h4 className="text-xs font-bold text-white group-hover:text-terminal-accent transition-colors font-mono">
                      {proj.name}
                    </h4>
                    <p className="text-[10px] text-terminal-muted font-mono mt-0.5">
                      Venture: <span className="text-terminal-fg">{proj.venture_name || 'Independent'}</span>
                    </p>
                  </div>
                  <StatusBadge status={proj.status} />
                </div>

                {/* Progress bar */}
                <div className="space-y-1">
                  <div className="flex justify-between text-[10px] font-mono">
                    <span className="text-terminal-muted">Execution Progress</span>
                    <span className="text-terminal-accent font-bold">{proj.progress}%</span>
                  </div>
                  <div className="w-full bg-terminal-panel h-1.5 rounded-full overflow-hidden border border-terminal-border">
                    <div 
                      className={`h-full rounded-full transition-all duration-500 ${isCompleted ? 'bg-terminal-accent' : 'bg-purple-500'}`}
                      style={{ width: `${proj.progress}%` }}
                    />
                  </div>
                </div>

                {/* Details Footer */}
                {proj.target_date && (
                  <div className="flex justify-between text-[9px] font-mono text-terminal-muted pt-1">
                    <span className="flex items-center gap-1">
                      <Calendar size={11} /> Target: {proj.target_date}
                    </span>
                    {proj.open_task_count !== undefined && (
                      <span>{proj.open_task_count} Tasks Remaining</span>
                    )}
                  </div>
                )}
              </Link>
            );
          })}
        </div>
      )}
    </Card>
  );
};

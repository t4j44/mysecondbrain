'use client';

import React, { useState } from 'react';
import { CheckSquare, Square, Calendar, AlertCircle, ArrowUpRight, CheckCircle2 } from 'lucide-react';
import { Card, PriorityBadge, Button } from '../ui/CustomUi';
import { Task } from '../../types/execution';
import { mockApi } from '../../lib/mockApi';

interface TodayFocusPanelProps {
  tasks: Task[];
  onTaskUpdated?: () => void;
}

export default function TodayFocusPanel({ tasks, onTaskUpdated }: TodayFocusPanelProps) {
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const handleToggleComplete = async (task: Task) => {
    setUpdatingId(task.id);
    // Optimistic UI updates
    const prevStatus = task.status;
    task.status = 'done';
    
    try {
      await mockApi.updateTaskStatus(task.id, 'done');
      if (onTaskUpdated) onTaskUpdated();
    } catch (err) {
      console.error('Failed to complete task', err);
      task.status = prevStatus; // Rollback
    } finally {
      setUpdatingId(null);
    }
  };

  const handleRescheduleToday = async (task: Task) => {
    setUpdatingId(task.id);
    const newDueDate = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString();
    try {
      await mockApi.updateTask(task.id, { due_date: newDueDate });
      if (onTaskUpdated) onTaskUpdated();
    } catch (err) {
      console.error('Failed to reschedule task', err);
    } finally {
      setUpdatingId(null);
    }
  };

  const today = new Date().toISOString().split('T')[0];

  return (
    <Card 
      header={
        <div className="flex items-center gap-2">
          <CheckSquare className="text-terminal-accent w-4 h-4" />
          <h3 className="font-mono text-xs font-bold text-white uppercase tracking-wider">Today's Focus Core</h3>
        </div>
      }
    >
      {tasks.length === 0 ? (
        <div className="py-8 text-center text-terminal-muted text-sm italic space-y-2">
          <CheckCircle2 className="w-8 h-8 text-terminal-accent/30 mx-auto" />
          <p>Nothing is due today. Review upcoming work or choose a focus task.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {tasks.map(task => {
            const isOverdue = task.due_date && task.due_date.split('T')[0] < today;
            const isCompleted = task.status === 'done';

            return (
              <div
                key={task.id}
                className={`p-3.5 rounded-lg border transition-all flex items-start gap-3 bg-terminal-panel/50 ${
                  isOverdue 
                    ? 'border-terminal-alert/20 hover:border-terminal-alert/40' 
                    : 'border-terminal-border hover:border-terminal-accent/30'
                } ${updatingId === task.id ? 'opacity-50 pointer-events-none' : ''}`}
              >
                {/* Completion Checkbox */}
                <button
                  onClick={() => handleToggleComplete(task)}
                  className="mt-0.5 text-terminal-muted hover:text-terminal-accent transition-colors flex-shrink-0"
                >
                  {isCompleted ? (
                    <CheckSquare size={17} className="text-terminal-accent" />
                  ) : (
                    <Square size={17} />
                  )}
                </button>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <p className={`text-xs font-medium text-terminal-fg leading-snug ${isCompleted ? 'line-through text-terminal-muted' : ''}`}>
                      {task.title}
                    </p>
                    <PriorityBadge priority={task.priority} />
                  </div>

                  <div className="flex items-center gap-3 mt-2 text-[10px] font-mono text-terminal-muted">
                    {/* Focus Type Tag */}
                    <span className="text-terminal-accent bg-terminal-accent/5 px-1.5 py-0.5 rounded border border-terminal-accent/10">
                      Suggested focus
                    </span>

                    {/* Deadline tag */}
                    {task.due_date && (
                      <span className={`flex items-center gap-1 ${isOverdue ? 'text-terminal-alert font-bold' : ''}`}>
                        <Calendar size={11} />
                        {isOverdue ? 'OVERDUE' : 'Due Today'}
                      </span>
                    )}
                  </div>
                </div>

                {/* Quick actions hover */}
                <div className="flex flex-col gap-1 flex-shrink-0 self-center">
                  {isOverdue && (
                    <Button 
                      size="sm" 
                      onClick={() => handleRescheduleToday(task)}
                      className="px-2 py-1 text-[9px] font-mono border-terminal-warn/30 text-terminal-warn hover:bg-terminal-warn/10"
                    >
                      Defer +1D
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
}

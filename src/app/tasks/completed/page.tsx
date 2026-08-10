'use client';

import React from 'react';
import LayoutShell from '../../../components/layout/Sidebar';
import TaskManager from '../../../components/tasks/TaskManager';

export default function TasksCompletedPage() {
  return (
    <LayoutShell>
      <TaskManager initialView="completed" />
    </LayoutShell>
  );
}

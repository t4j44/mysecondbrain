import { getMockDB, saveMockDB, delay } from './mockDb';
import { Venture, Project, Task, DashboardSummary, AIInsights, TaskStatus, TaskPriority, VentureStatus, ProjectStatus } from '../types/execution';

export const mockApi = {
  // --- Profile / Settings ---
  getProfile: async () => {
    await delay();
    const db = getMockDB();
    return db.profile;
  },

  updateMission: async (mission: string) => {
    await delay();
    const db = getMockDB();
    db.profile.settings.current_mission = mission;
    saveMockDB(db);
    return db.profile;
  },

  // --- Dashboard Summary ---
  getDashboardSummary: async (ventureId?: string): Promise<DashboardSummary> => {
    await delay(300);
    const db = getMockDB();
    
    // Filter elements if ventureId is present
    let activeTasks = db.tasks.filter(t => t.status !== 'done' && t.status !== 'archived');
    if (ventureId) {
      activeTasks = activeTasks.filter(t => t.venture_id === ventureId);
    }
    
    // Urgent/overdue tasks or due today
    const today = new Date().toISOString().split('T')[0];
    const todayFocusTasks = activeTasks.filter(t => {
      const isUrgent = t.priority === 'urgent';
      const isDueToday = t.due_date && t.due_date.split('T')[0] === today;
      const isOverdue = t.due_date && t.due_date.split('T')[0] < today;
      return isUrgent || isDueToday || isOverdue;
    });

    const activeProjectsCount = db.projects.filter(p => p.status === 'in_progress' && (!ventureId || p.venture_id === ventureId)).length;
    const currentMissionVenture = ventureId ? db.ventures.find(v => v.id === ventureId) : db.ventures.find(v => v.id === 'v-1');

    return {
      current_mission_venture: currentMissionVenture || null,
      today_focus_tasks: todayFocusTasks.slice(0, 3), // max 3 priority tasks
      calendar_events_today: db.calendarEvents,
      active_projects_count: activeProjectsCount,
      kpi_highlights: db.kpis,
      recent_memory_stream: db.memories,
      relationship_follow_ups: db.followUps,
    };
  },

  getDashboardInsights: async (): Promise<AIInsights> => {
    await delay(400);
    return {
      ai_insight: "Execution velocity on Justor AI has increased 15% due to completed structural layouts, but SOC2 compliance check items remain a pending bottleneck.",
      recommended_actions: [
        "Complete database access isolation validations on Zqtion",
        "Follow up with Yousuf Imran regarding term sheet review",
        "Re-evaluate CMOOS paused state objectives next week"
      ]
    };
  },

  // --- Ventures ---
  getVentures: async (includeArchived = false) => {
    await delay();
    const db = getMockDB();
    const ventures = db.ventures.filter(v => includeArchived || v.status !== 'archived');
    
    // Enrich with count meta
    return ventures.map(v => ({
      ...v,
      project_count: db.projects.filter(p => p.venture_id === v.id && p.status !== 'archived').length,
      open_task_count: db.tasks.filter(t => t.venture_id === v.id && t.status !== 'done' && t.status !== 'archived').length
    }));
  },

  getVentureById: async (id: string): Promise<Venture & { projects: Project[]; tasks: Task[] }> => {
    await delay();
    const db = getMockDB();
    const venture = db.ventures.find(v => v.id === id);
    if (!venture) throw new Error('Venture not found');
    
    const projects = db.projects.filter(p => p.venture_id === id && p.status !== 'archived');
    const tasks = db.tasks.filter(t => t.venture_id === id && t.status !== 'archived');

    return {
      ...venture,
      project_count: projects.length,
      open_task_count: tasks.filter(t => t.status !== 'done').length,
      projects,
      tasks
    };
  },

  createVenture: async (data: Omit<Venture, 'id' | 'created_at' | 'updated_at'>) => {
    await delay();
    const db = getMockDB();
    const newVenture: Venture = {
      ...data,
      id: 'v-' + Math.random().toString(36).substr(2, 9),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    db.ventures.push(newVenture);
    saveMockDB(db);
    return newVenture;
  },

  updateVenture: async (id: string, data: Partial<Omit<Venture, 'id' | 'created_at' | 'updated_at'>>) => {
    await delay();
    const db = getMockDB();
    const idx = db.ventures.findIndex(v => v.id === id);
    if (idx === -1) throw new Error('Venture not found');
    
    db.ventures[idx] = {
      ...db.ventures[idx],
      ...data,
      updated_at: new Date().toISOString(),
    };
    saveMockDB(db);
    return db.ventures[idx];
  },

  archiveVenture: async (id: string) => {
    await delay();
    const db = getMockDB();
    const idx = db.ventures.findIndex(v => v.id === id);
    if (idx === -1) throw new Error('Venture not found');
    
    db.ventures[idx].status = 'archived';
    db.ventures[idx].deleted_at = new Date().toISOString();
    
    // Soft archive projects and tasks under this venture
    db.projects = db.projects.map(p => p.venture_id === id ? { ...p, status: 'archived', deleted_at: new Date().toISOString() } : p);
    db.tasks = db.tasks.map(t => t.venture_id === id ? { ...t, status: 'archived', deleted_at: new Date().toISOString() } : t);
    
    saveMockDB(db);
    return db.ventures[idx];
  },

  // --- Projects ---
  getProjects: async (includeArchived = false) => {
    await delay();
    const db = getMockDB();
    const projects = db.projects.filter(p => includeArchived || p.status !== 'archived');
    
    return projects.map(p => ({
      ...p,
      venture_name: db.ventures.find(v => v.id === p.venture_id)?.name || 'Independent',
      open_task_count: db.tasks.filter(t => t.project_id === p.id && t.status !== 'done' && t.status !== 'archived').length,
      blocked_task_count: db.tasks.filter(t => t.project_id === p.id && t.status === 'in_progress' && t.priority === 'urgent').length // Derived representation of blocked
    }));
  },

  getProjectById: async (id: string): Promise<Project & { venture_name: string; tasks: Task[] }> => {
    await delay();
    const db = getMockDB();
    const project = db.projects.find(p => p.id === id);
    if (!project) throw new Error('Project not found');
    
    const venture_name = db.ventures.find(v => v.id === project.venture_id)?.name || 'Independent';
    const tasks = db.tasks.filter(t => t.project_id === id && t.status !== 'archived');

    return {
      ...project,
      venture_name,
      tasks
    };
  },

  createProject: async (data: Omit<Project, 'id' | 'created_at' | 'updated_at'>) => {
    await delay();
    const db = getMockDB();
    const newProject: Project = {
      ...data,
      id: 'p-' + Math.random().toString(36).substr(2, 9),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    db.projects.push(newProject);
    saveMockDB(db);
    return newProject;
  },

  updateProject: async (id: string, data: Partial<Omit<Project, 'id' | 'created_at' | 'updated_at'>>) => {
    await delay();
    const db = getMockDB();
    const idx = db.projects.findIndex(p => p.id === id);
    if (idx === -1) throw new Error('Project not found');
    
    db.projects[idx] = {
      ...db.projects[idx],
      ...data,
      updated_at: new Date().toISOString(),
    };
    saveMockDB(db);
    return db.projects[idx];
  },

  archiveProject: async (id: string) => {
    await delay();
    const db = getMockDB();
    const idx = db.projects.findIndex(p => p.id === id);
    if (idx === -1) throw new Error('Project not found');
    
    db.projects[idx].status = 'archived';
    db.projects[idx].deleted_at = new Date().toISOString();
    
    // Soft archive tasks under this project
    db.tasks = db.tasks.map(t => t.project_id === id ? { ...t, status: 'archived', deleted_at: new Date().toISOString() } : t);
    
    saveMockDB(db);
    return db.projects[idx];
  },

  // --- Tasks ---
  getTasks: async (filters?: { venture_id?: string; project_id?: string; status?: TaskStatus; priority?: TaskPriority }) => {
    await delay();
    const db = getMockDB();
    let tasks = db.tasks.filter(t => t.status !== 'archived');
    
    if (filters) {
      if (filters.venture_id) tasks = tasks.filter(t => t.venture_id === filters.venture_id);
      if (filters.project_id) tasks = tasks.filter(t => t.project_id === filters.project_id);
      if (filters.status) tasks = tasks.filter(t => t.status === filters.status);
      if (filters.priority) tasks = tasks.filter(t => t.priority === filters.priority);
    }
    
    return tasks.map(t => ({
      ...t,
      venture_name: db.ventures.find(v => v.id === t.venture_id)?.name || 'Independent',
      project_name: db.projects.find(p => p.id === t.project_id)?.name || 'Independent'
    }));
  },

  createTask: async (data: Omit<Task, 'id' | 'created_at' | 'updated_at'>) => {
    await delay();
    const db = getMockDB();
    const newTask: Task = {
      ...data,
      id: 't-' + Math.random().toString(36).substr(2, 9),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    db.tasks.push(newTask);
    
    // Re-calculate project progress if linked to project
    if (newTask.project_id) {
      recalculateProjectProgress(db, newTask.project_id);
    }
    
    saveMockDB(db);
    return newTask;
  },

  updateTask: async (id: string, data: Partial<Omit<Task, 'id' | 'created_at' | 'updated_at'>>) => {
    await delay();
    const db = getMockDB();
    const idx = db.tasks.findIndex(t => t.id === id);
    if (idx === -1) throw new Error('Task not found');
    
    const oldTask = db.tasks[idx];
    const updatedTask = {
      ...oldTask,
      ...data,
      updated_at: new Date().toISOString(),
    };
    
    if (data.status === 'done' && oldTask.status !== 'done') {
      updatedTask.completed_at = new Date().toISOString();
    } else if (data.status && data.status !== 'done') {
      updatedTask.completed_at = null;
    }
    
    db.tasks[idx] = updatedTask;
    
    // Handle progress changes if project linked
    if (oldTask.project_id) recalculateProjectProgress(db, oldTask.project_id);
    if (updatedTask.project_id && updatedTask.project_id !== oldTask.project_id) {
      recalculateProjectProgress(db, updatedTask.project_id);
    }
    
    saveMockDB(db);
    return updatedTask;
  },

  updateTaskStatus: async (id: string, status: TaskStatus) => {
    return mockApi.updateTask(id, { status });
  },

  deleteTask: async (id: string) => {
    await delay();
    const db = getMockDB();
    const idx = db.tasks.findIndex(t => t.id === id);
    if (idx === -1) throw new Error('Task not found');
    
    const task = db.tasks[idx];
    db.tasks[idx].status = 'archived';
    db.tasks[idx].deleted_at = new Date().toISOString();
    
    if (task.project_id) {
      recalculateProjectProgress(db, task.project_id);
    }
    
    saveMockDB(db);
    return db.tasks[idx];
  }
};

// Helper: Derived Progress calculation based on tasks state
function recalculateProjectProgress(db: any, projectId: string) {
  const projectIdx = db.projects.findIndex((p: any) => p.id === projectId);
  if (projectIdx === -1) return;
  
  const projectTasks = db.tasks.filter((t: any) => t.project_id === projectId && t.status !== 'archived');
  if (projectTasks.length === 0) return;
  
  const completedCount = projectTasks.filter((t: any) => t.status === 'done').length;
  const newProgress = Math.round((completedCount / projectTasks.length) * 100);
  
  db.projects[projectIdx].progress = newProgress;
}

import { Venture, Project, Task, DashboardSummary, AIInsights } from '../types/execution';

const MOCK_STORAGE_KEY = 'taj_second_brain_mock_db';

const defaultVentures: Venture[] = [
  {
    id: 'v-1',
    name: 'Justor AI',
    slug: 'justor-ai',
    vision: 'Empower creators with private autonomous multi-agent execution engines.',
    mission: 'Build the world\'s first sovereign multi-agent developer operating system.',
    status: 'active',
    created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'v-2',
    name: 'Zqtion',
    slug: 'zqtion',
    vision: 'Zero trust continuous security posture audits for enterprise networks.',
    mission: 'Real-time API and infrastructure compliance monitoring & auto-mitigation.',
    status: 'active',
    created_at: new Date(Date.now() - 20 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'v-3',
    name: 'IEXF',
    slug: 'iexf',
    vision: 'Immutable evidence-backed file exchanges for distributed legal operations.',
    mission: 'Decentralized legal agreement exchange with cryptographically signed trails.',
    status: 'active',
    created_at: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'v-4',
    name: 'CMOOS',
    slug: 'cmoos',
    vision: 'Community owned growth marketing pipelines that scale without advertising fees.',
    mission: 'Decentralized open-source growth engines driven by reward tokens.',
    status: 'paused',
    created_at: new Date(Date.now() - 40 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 12 * 24 * 60 * 60 * 1000).toISOString(),
  }
];

const defaultProjects: Project[] = [
  {
    id: 'p-1',
    venture_id: 'v-1',
    name: 'Justor MVP Release',
    description: 'Bundle agent execution layers and command menus for the public beta release.',
    status: 'in_progress',
    target_date: new Date(Date.now() + 10 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    progress: 70,
    created_at: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'p-2',
    venture_id: 'v-2',
    name: 'Zqtion Compliance Engine',
    description: 'Implement radial progress charts and live compliance audit streams.',
    status: 'in_progress',
    target_date: new Date(Date.now() + 18 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    progress: 45,
    created_at: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'p-3',
    venture_id: 'v-3',
    name: 'IEXF Smart Contract Audit',
    description: 'Verify Solidity contracts and security audit parameters.',
    status: 'planning',
    target_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    progress: 10,
    created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'p-4',
    venture_id: 'v-4',
    name: 'Global Marketing Campaign',
    description: 'Initialize influencer campaigns and community token bounty channels.',
    status: 'on_hold',
    target_date: new Date(Date.now() + 50 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    progress: 90,
    created_at: new Date(Date.now() - 35 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
  }
];

const defaultTasks: Task[] = [
  {
    id: 't-1',
    venture_id: 'v-1',
    project_id: 'p-1',
    title: 'Review pitch deck with Lead Orchestrator',
    description: 'Review the technical roadmap section and seed round requirements.',
    status: 'todo',
    priority: 'urgent',
    due_date: new Date().toISOString(), // Today
    created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 't-2',
    venture_id: 'v-2',
    project_id: 'p-2',
    title: 'Complete SOC2 audit checklist items',
    description: 'Fulfill database access isolation items and encryption validations.',
    status: 'todo',
    priority: 'high',
    due_date: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // Yesterday (Overdue)
    created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 't-3',
    venture_id: 'v-1',
    project_id: 'p-1',
    title: 'Align with Agent 4 on design layouts',
    description: 'Confirm the terminal colors and borders align on mobile viewports.',
    status: 'todo',
    priority: 'medium',
    due_date: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // Tomorrow
    created_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 't-4',
    venture_id: 'v-1',
    project_id: 'p-1',
    title: 'Deploy Vercel serverless app skeleton',
    description: 'Establish initial router configurations and basic CSS scanline overlay.',
    status: 'done',
    priority: 'medium',
    due_date: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    completed_at: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
    created_at: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 't-5',
    venture_id: 'v-3',
    project_id: 'p-3',
    title: 'Define smart contract auditor parameters',
    description: 'Outline Solidity variables and state channels needing review.',
    status: 'todo',
    priority: 'low',
    due_date: new Date(Date.now() + 4 * 24 * 60 * 60 * 1000).toISOString(), // in 4 days
    created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 't-6',
    venture_id: 'v-4',
    project_id: 'p-4',
    title: 'Setup community bounty channels',
    description: 'Install Discord bots and set up reward allocation scripts.',
    status: 'done',
    priority: 'high',
    due_date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    completed_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    created_at: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date().toISOString(),
  }
];

const defaultMemories = [
  { id: 'm-1', title: 'Bangladesh developer ecosystem shows high execution speed', category: 'observation', created_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString() },
  { id: 'm-2', title: 'Design system rules should remain highly constrained to prevent color bloat', category: 'lesson', created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString() },
  { id: 'm-3', title: 'Decoupling REST API routing from DB persist structures was critical for scale', category: 'win', created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString() }
];

const defaultFollowUps = [
  { id: 'f-1', name: 'Yousuf Imran', role: 'Lead Architect, Brain.ai', follow_up_date: new Date().toISOString(), next_action: 'MVP design token validation', overdue: false },
  { id: 'f-2', name: 'Al-Amin Ahmed', role: 'Venture Partner, Bengal VC', follow_up_date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(), next_action: 'Review seed term sheet', overdue: true }
];

const defaultKpis = [
  { metric_name: 'Ventures Active', current_value: 3, target_value: 5, unit: 'count' },
  { metric_name: 'Weekly Task Velocity', current_value: 82, target_value: 100, unit: '%' },
  { metric_name: 'Advisors Engaged', current_value: 8, target_value: 12, unit: 'people' }
];

const defaultCalendarEvents = [
  { id: 'c-1', title: 'Lead Orchestration Session', time: new Date(new Date().setHours(14, 0, 0, 0)).toISOString(), duration: 60, source: 'Google Calendar' },
  { id: 'c-2', title: 'Taj & Yousuf Alignment Sync', time: new Date(new Date().setHours(16, 30, 0, 0)).toISOString(), duration: 30, source: 'Google Calendar' }
];

interface MockDB {
  profile: {
    email: string;
    full_name: string;
    avatar_url: string;
    settings: {
      theme: string;
      timezone: string;
      current_mission?: string;
    };
  };
  ventures: Venture[];
  projects: Project[];
  tasks: Task[];
  memories: typeof defaultMemories;
  followUps: typeof defaultFollowUps;
  kpis: typeof defaultKpis;
  calendarEvents: typeof defaultCalendarEvents;
}

export function getMockDB(): MockDB {
  if (typeof window === 'undefined') {
    return {
      profile: {
        email: 'taj@founder.ai',
        full_name: 'Tajul Islam',
        avatar_url: '',
        settings: {
          theme: 'retro-terminal',
          timezone: 'Asia/Dhaka',
          current_mission: 'Build Taj\'s Second Brain to capture 100% of start-up memories and operations.'
        }
      },
      ventures: defaultVentures,
      projects: defaultProjects,
      tasks: defaultTasks,
      memories: defaultMemories,
      followUps: defaultFollowUps,
      kpis: defaultKpis,
      calendarEvents: defaultCalendarEvents
    };
  }

  const stored = localStorage.getItem(MOCK_STORAGE_KEY);
  if (stored) {
    try {
      return JSON.parse(stored);
    } catch (e) {
      console.error('Failed to parse mock DB, recreating defaults', e);
    }
  }

  const newDB: MockDB = {
    profile: {
      email: 'taj@founder.ai',
      full_name: 'Tajul Islam',
      avatar_url: '',
      settings: {
        theme: 'retro-terminal',
        timezone: 'Asia/Dhaka',
        current_mission: 'Build Taj\'s Second Brain to capture 100% of start-up memories and operations.'
      }
    },
    ventures: defaultVentures,
    projects: defaultProjects,
    tasks: defaultTasks,
    memories: defaultMemories,
    followUps: defaultFollowUps,
    kpis: defaultKpis,
    calendarEvents: defaultCalendarEvents
  };

  saveMockDB(newDB);
  return newDB;
}

export function saveMockDB(db: MockDB) {
  if (typeof window !== 'undefined') {
    localStorage.setItem(MOCK_STORAGE_KEY, JSON.stringify(db));
  }
}

// Simulates network latency
export function delay(ms = 250): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

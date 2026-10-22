import React, { Profiler } from 'react';
import { createRoot } from 'react-dom/client';
import { AppShell } from '../components/layout/app-shell';
import Home from '../app/(dashboard)/dashboard/page';
import People from '../app/(dashboard)/people/page';
import Ask from '../app/(dashboard)/assistant/page';
import Work from '../app/(dashboard)/work/page';
import Capture from '../app/(dashboard)/capture/page';
import NewPerson from '../app/(dashboard)/people/new/page';
import EditPerson from '../app/(dashboard)/people/[personId]/edit/page';
import PersonDetail from '../app/(dashboard)/people/[personId]/page';
import { ChatArea } from '../components/chat/ChatArea';
import Organizations from '../app/(dashboard)/organizations/page';
import Memories from '../app/(dashboard)/memories/page';
import Ideas from '../app/(dashboard)/ideas/page';
import Achievements from '../app/(dashboard)/achievements/page';
import Metrics from '../app/(dashboard)/kpis/page';
import Content from '../app/(dashboard)/content/page';
import NewMemory from '../app/(dashboard)/memories/new/page';
import Source from '../app/(dashboard)/sources/[kind]/[id]/page';

const pages: Record<string, React.ComponentType> = { '/dashboard': Home, '/people': People, '/assistant': Ask, '/work': Work, '/capture': Capture,'/organizations':Organizations,'/memories':Memories,'/memories/new':NewMemory,'/ideas':Ideas,'/achievements':Achievements,'/kpis':Metrics,'/content':Content };
const Page = location.pathname==='/people/new'?NewPerson:/^\/people\/[^/]+\/edit$/.test(location.pathname)?EditPerson:/^\/people\/[^/]+$/.test(location.pathname)?PersonDetail:location.pathname.startsWith('/sources/')?Source:pages[location.pathname] || Home;
declare global { interface Window { __renders: { phase: string; duration: number }[]; __messageRenders: number } }
window.__renders = [];
window.__messageRenders = 0;
const history = Array.from({length:60},(_,i)=>({id:`synthetic-${i}`,role:i%2?'assistant' as const:'user' as const,content:`Synthetic saved conversation ${i}. `+'Only fictional context. '.repeat(12),timestamp:'10:00',status:'completed' as const}));
createRoot(document.getElementById('root')!).render(
  <Profiler id="mobile" onRender={(_id, phase, duration) => window.__renders.push({ phase, duration })}>
    <AppShell>{new URLSearchParams(location.search).has('history')?<ChatArea initialMessages={history}/>:<Page />}</AppShell>
  </Profiler>,
);

'use client';

import Link from 'next/link';
import {usePathname} from 'next/navigation';
import {ArrowLeft} from 'lucide-react';

const titles:Record<string,string>={dashboard:'Home',capture:'Capture',people:'People',work:'Work',assistant:'Ask',projects:'Projects',ventures:'Ventures',tasks:'Tasks',meetings:'Meetings',documents:'Documents',settings:'Settings',organizations:'Organizations',memories:'Memories',sources:'Sources',portfolio:'Portfolio'};
export function Breadcrumbs(){
 const segments=usePathname().split('/').filter(Boolean);
 const first=segments[0]||'dashboard';
 const nested=segments.length>1;
 return <nav aria-label="Breadcrumb" className="flex min-w-0 items-center gap-2 text-sm">
  {nested&&<Link href={`/${first}`} aria-label={`Back to ${titles[first]||'workspace'}`} className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-lg"><ArrowLeft className="h-4 w-4"/></Link>}
  <span aria-current="page" className="truncate font-medium">{nested?(segments.at(-1)==='new'?'Add new':segments.at(-1)==='edit'?'Edit':titles[segments.at(-1)||'']||titles[first]||'Details'):titles[first]||'Second Brain'}</span>
 </nav>;
}

'use client';

import * as React from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import Link from 'next/link';
import {usePathname} from 'next/navigation';
import {Search,X} from 'lucide-react';
import {primaryNavigation,workNavigation} from '@/lib/navigation';

const destinations=Array.from(new Map([...primaryNavigation,...workNavigation,{title:'Organizations',href:'/organizations'},{title:'Settings',href:'/settings'},{title:'Privacy',href:'/settings/privacy'},{title:'AI connections',href:'/settings/ai-access'}].map(item=>[item.href,item])).values());
export function CommandMenu(){
 const [open,setOpen]=React.useState(false);
 const [query,setQuery]=React.useState('');
 const pathname=usePathname();
 React.useEffect(()=>{setOpen(false);setQuery('');},[pathname]);
 React.useEffect(()=>{const listener=(event:KeyboardEvent)=>{if(event.key==='k'&&(event.metaKey||event.ctrlKey)){event.preventDefault();setOpen(previous=>!previous);}};window.addEventListener('keydown',listener);return()=>window.removeEventListener('keydown',listener);},[]);
 const items=destinations.filter(item=>item.title.toLowerCase().includes(query.trim().toLowerCase()));
 return <Dialog.Root open={open} onOpenChange={setOpen}>
  <Dialog.Trigger asChild><button type="button" className="inline-flex h-[44px] w-[44px] shrink-0 items-center justify-center rounded-lg border bg-card text-muted-foreground hover:text-foreground xl:w-56 xl:justify-between xl:px-3" aria-label="Find a page"><Search className="h-5 w-5"/><span className="hidden text-sm xl:inline">Find a page…</span><kbd className="hidden text-sm xl:inline">⌘K</kbd></button></Dialog.Trigger>
  <Dialog.Portal><Dialog.Overlay className="fixed inset-0 z-[200] bg-black/70"/><Dialog.Content aria-describedby={undefined} className="fixed inset-x-4 top-4 z-[201] mx-auto flex max-h-[calc(100dvh-2rem)] max-w-xl flex-col rounded-xl border bg-popover p-4 text-popover-foreground shadow-xl">
   <div className="mb-3 flex items-center justify-between gap-2"><Dialog.Title className="font-semibold">Find a page</Dialog.Title><Dialog.Close asChild><button type="button" aria-label="Close page search" className="inline-flex h-11 w-11 items-center justify-center rounded-lg border"><X className="h-5 w-5"/></button></Dialog.Close></div>
   <label className="block"><span className="sr-only">Search pages</span><input type="search" value={query} onChange={event=>setQuery(event.target.value)} placeholder="People, work, settings…" className="min-h-12 w-full rounded-lg border bg-background px-3 text-base"/></label>
   <nav aria-label="Page search results" className="mt-3 min-h-0 overflow-y-auto">{items.length?items.map(item=><Dialog.Close key={item.href} asChild><Link href={item.href} className="flex min-h-12 items-center rounded-lg px-3 text-base hover:bg-muted">{item.title}</Link></Dialog.Close>):<p role="status" className="py-4 text-muted-foreground">No matching pages.</p>}</nav>
  </Dialog.Content></Dialog.Portal>
 </Dialog.Root>;
}

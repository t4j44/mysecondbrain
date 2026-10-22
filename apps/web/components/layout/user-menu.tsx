'use client';

import * as React from 'react';
import * as Menu from '@radix-ui/react-dropdown-menu';
import {useRouter} from 'next/navigation';
import {User} from 'lucide-react';
import {useTheme} from 'next-themes';
import {createClient} from '@/lib/supabase/client';

const item='flex min-h-11 cursor-pointer items-center rounded px-3 text-sm outline-none focus:bg-muted';
export function UserMenu(){
 const [name,setName]=React.useState('Account');
 const [failure,setFailure]=React.useState('');
 const {theme,setTheme}=useTheme();const router=useRouter();
 React.useEffect(()=>{let active=true;void createClient().auth.getUser().then(({data:{user}})=>{if(active&&user)setName(user.user_metadata?.full_name||'Account');});return()=>{active=false;};},[]);
 async function signOut(){
  const {error}=await createClient().auth.signOut();
  if(error){setFailure('Could not sign out. Try again.');return;}
  try{Object.keys(sessionStorage).filter(key=>key.startsWith('second-brain:capture:')).forEach(key=>sessionStorage.removeItem(key));}catch{/* Browser storage can be disabled. */}
  router.push('/login');router.refresh();
 }
 return <><Menu.Root><Menu.Trigger asChild><button type="button" aria-label="Account options" className="inline-flex h-[44px] min-w-[44px] shrink-0 items-center justify-center gap-2 rounded-lg border bg-card px-2 text-sm"><User className="h-5 w-5"/><span className="hidden max-w-24 truncate xl:inline">{name}</span></button></Menu.Trigger>
  <Menu.Portal><Menu.Content align="end" sideOffset={8} className="z-[250] w-60 max-w-[calc(100vw-2rem)] rounded-xl border bg-popover p-2 text-popover-foreground shadow-xl">
   <Menu.Label className="px-3 py-2 text-sm font-medium">{name}</Menu.Label>
   <Menu.Item className={item} onSelect={()=>router.push('/settings')}>Settings and connections</Menu.Item>
   <Menu.Item className={item} onSelect={()=>router.push('/settings/profile')}>Your profile</Menu.Item>
   <Menu.Separator className="my-1 border-t"/>
   <Menu.RadioGroup value={theme} onValueChange={setTheme} aria-label="Appearance">{['dark','light','system'].map(value=><Menu.RadioItem key={value} value={value} className={`${item} capitalize`}><Menu.ItemIndicator className="mr-2">✓</Menu.ItemIndicator>{value==='system'?'Device theme':value+' theme'}</Menu.RadioItem>)}</Menu.RadioGroup>
   <Menu.Separator className="my-1 border-t"/>
   <Menu.Item className={item} onSelect={()=>void signOut()}>Sign out</Menu.Item>
  </Menu.Content></Menu.Portal>
 </Menu.Root>{failure&&<p role="alert" className="absolute right-4 top-16 z-50 max-w-xs rounded-lg border bg-card p-3 text-sm">{failure}</p>}</>;
}

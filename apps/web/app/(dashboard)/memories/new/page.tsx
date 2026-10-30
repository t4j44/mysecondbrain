'use client';
import Link from 'next/link';
import {useRef,useState} from 'react';
import {useRouter} from 'next/navigation';
import {api} from '@/lib/api/browser-client';
export default function NewMemoryPage(){
 const router=useRouter();
 const [title,setTitle]=useState(''),[body,setBody]=useState(''),[tags,setTags]=useState('');
 const [busy,setBusy]=useState(false),[error,setError]=useState('');const pending=useRef(false);
 return <div className="mx-auto max-w-2xl space-y-5"><Link href="/memories" className="inline-flex min-h-11 items-center text-primary underline">Back to saved notes</Link><h1 className="text-2xl font-semibold">Add a note</h1><p className="text-base text-muted-foreground">Save what happened in your own words. You can ask about it later.</p>
  <form className="space-y-5" onSubmit={async event=>{
   event.preventDefault();if(pending.current||!title.trim()||!body.trim())return;pending.current=true;setBusy(true);setError('');
   try{const saved=await api.post<{id:string}>('/memories',{title:title.trim(),body:body.trim(),type:'note',tags:tags.split(',').map(value=>value.trim()).filter(Boolean),visibility:'private'});router.push('/sources/memory/'+encodeURIComponent(saved.id));}
   catch{setError('Could not save this note. Your text is kept here. Try again.');}
   finally{pending.current=false;setBusy(false);}
  }}>
   <label className="block space-y-2"><span>Title</span><input required maxLength={255} value={title} onChange={event=>setTitle(event.target.value)} className="min-h-12 w-full rounded-lg border bg-card px-3 text-base"/></label>
   <label className="block space-y-2"><span>Note</span><textarea required rows={8} value={body} onChange={event=>setBody(event.target.value)} className="w-full rounded-lg border bg-card p-3 text-base"/></label>
   <details className="rounded-lg border px-4"><summary className="min-h-12 cursor-pointer py-3">Tags (optional)</summary><label className="mb-4 block space-y-2"><span className="text-sm">Separate tags with commas</span><input value={tags} onChange={event=>setTags(event.target.value)} className="min-h-12 w-full rounded-lg border bg-card px-3 text-base"/></label></details>
   {error&&<p role="alert" className="rounded-lg border border-destructive p-3">{error}</p>}
   <button type="submit" disabled={busy||!title.trim()||!body.trim()} className="min-h-12 rounded-lg bg-primary px-5 text-primary-foreground disabled:opacity-50">{busy?'Saving…':'Save note'}</button>
  </form>
 </div>;
}
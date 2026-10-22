'use client';

import {useEffect,useId,useState} from 'react';
import Link from 'next/link';
import type {Person} from '@/lib/api/domains';

export type PersonFormValues={name:string;role:string|null;company:string|null;email:string|null;phone:string|null;linkedin_url:string|null;relationship_type:string;notes:string|null;location:string|null};
export function PersonForm({person,onSave,saving,error,cancelHref='/people'}:{person?:Person;onSave:(values:PersonFormValues)=>void;saving:boolean;error?:string;cancelHref?:string}){
 const prefix=useId();
 const [ready,setReady]=useState(false);
 useEffect(()=>setReady(true),[]);
 const [values,setValues]=useState<PersonFormValues>({name:person?.name||'',role:person?.role||null,company:person?.company||null,email:person?.email||null,phone:person?.phone||null,linkedin_url:person?.linkedin_url||null,relationship_type:person?.relationship_type||'contact',notes:person?.notes||null,location:person?.location||null});
 const [shortNote,setShortNote]=useState('');
 function field(key:Exclude<keyof PersonFormValues,'notes'|'relationship_type'>,label:string,type='text',required=false){return <div className="space-y-2"><label htmlFor={`${prefix}-${key}`} className="block text-sm font-medium">{label}{required?' *':''}</label><input id={`${prefix}-${key}`} name={key} type={type} required={required} value={values[key]||''} onChange={event=>setValues(previous=>({...previous,[key]:key==='name'?event.target.value:event.target.value||null}))} className="min-h-12 w-full rounded-lg border bg-card px-3 text-base" autoComplete={key==='name'?'name':key==='email'?'email':key==='phone'?'tel':undefined}/></div>;}
 return <form className="space-y-5" onSubmit={event=>{event.preventDefault();if(!saving&&values.name?.trim())onSave({...values,name:values.name.trim()});}}><fieldset disabled={!ready} className="min-w-0 space-y-5">
  {field('name','Full name','text',true)}
  <div className="grid gap-4 sm:grid-cols-2">{field('company','Company')}{field('role','Role')}</div>
  <label className="block space-y-2"><span className="text-sm font-medium">Notes</span><textarea name="notes" value={values.notes||''} onChange={event=>setValues(previous=>({...previous,notes:event.target.value||null}))} rows={4} className="w-full rounded-lg border bg-card p-3 text-base" placeholder="How you met, what you discussed, or a useful detail"/></label>
  <details className="rounded-xl border px-4"><summary className="flex min-h-12 cursor-pointer items-center">More details</summary><div className="space-y-4 pb-4">
   {field('email','Email','email')}{field('phone','Phone','tel')}{field('linkedin_url','Professional profile URL','url')}{field('location','Location')}
   <label className="block space-y-2"><span className="text-sm font-medium">Relationship</span><select name="relationship_type" value={values.relationship_type} onChange={event=>setValues(previous=>({...previous,relationship_type:event.target.value}))} className="min-h-12 w-full rounded-lg border bg-card px-3 text-base">{['contact','mentor','investor','peer','collaborator','lead','client'].map(value=><option key={value} value={value}>{value}</option>)}</select></label>
  </div></details>
  {!person&&<details className="rounded-xl border px-4"><summary className="flex min-h-12 cursor-pointer items-center text-sm">Fill from a short note</summary><div className="space-y-3 pb-4"><label className="block space-y-2"><span className="text-sm">Name, role @ company — note</span><input value={shortNote} onChange={event=>setShortNote(event.target.value)} className="min-h-12 w-full rounded-lg border bg-card px-3 text-base"/></label><button type="button" className="min-h-11 rounded-lg border px-3" onClick={()=>{const match=shortNote.match(/^(.+?)(?:,\s*(.+?))?\s*@\s*(.+?)(?:\s+-\s+(.*))?$/u);if(match)setValues(previous=>({...previous,name:match[1].trim(),role:match[2]?.trim()||previous.role,company:match[3].trim(),notes:match[4]?.trim()||previous.notes}));else if(shortNote.trim())setValues(previous=>({...previous,name:shortNote.trim()}));}}>Fill fields</button><p className="text-sm text-muted-foreground">Check the fields before saving.</p></div></details>}
  {error&&<p role="alert" className="rounded-lg border border-destructive/50 p-3 text-sm">{error}</p>}
  <div className="flex flex-wrap items-center gap-3"><button type="submit" disabled={saving||!values.name?.trim()} className="min-h-12 rounded-lg bg-primary px-5 text-primary-foreground disabled:opacity-50">{saving?'Saving…':person?'Save changes':'Save person'}</button><Link href={cancelHref} className="inline-flex min-h-11 items-center px-3 text-sm underline">Cancel</Link></div>
 </fieldset></form>;
}

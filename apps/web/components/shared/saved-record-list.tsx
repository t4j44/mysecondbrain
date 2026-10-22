'use client';

import Link from 'next/link';
import {useCallback,useEffect,useState} from 'react';
import {api} from '@/lib/api/browser-client';
import {PageHeader} from './page-header';
import {RequestError} from './request-error';

type SavedRecord={id:string;title?:string;name?:string;description?:string;summary?:string;body?:string;problem?:string;status?:string;current_value?:number;target?:number;unit?:string};
type Page={items:SavedRecord[];total:number};
const detailLabels:Record<string,string>={problem:'Problem',solution:'Proposed solution',target_users:'Intended users',industry:'Industry',website:'Website',description:'Description',content:'Content',body:'Note',notes:'Notes',category:'Category',period:'Period',platform:'Platform'};
export function SavedRecordList({title,description,endpoint,kind,createHref='/capture',createLabel='Capture a note'}:{title:string;description:string;endpoint:string;kind?:string;createHref?:string;createLabel?:string}){
 const [rows,setRows]=useState<SavedRecord[]>([]),[total,setTotal]=useState(0),[busy,setBusy]=useState(true),[error,setError]=useState<unknown>(null);
 const load=useCallback(async(offset=0)=>{
  setBusy(true);setError(null);
  try{const result=await api.get<Page>(endpoint,{params:{limit:20,offset}});setRows(previous=>offset?[...previous,...result.items.filter(row=>!previous.some(item=>item.id===row.id))]:result.items);setTotal(result.total);}
  catch(failure){setError(failure);}finally{setBusy(false);}
 },[endpoint]);
 useEffect(()=>{void load();},[load]);
 return <div className="mx-auto max-w-3xl space-y-5"><PageHeader title={title} description={description} actions={<Link href={createHref} className="inline-flex min-h-11 items-center rounded-lg bg-primary px-4 text-base text-primary-foreground">{createLabel}</Link>}/>
  {error?<RequestError error={error} onRetry={()=>void load()}/>:null}
  {!error&&busy&&!rows.length?<p role="status">Loading saved records…</p>:null}
  {!error&&!busy&&!rows.length?<p className="rounded-xl border p-4 text-base">No records saved here yet. Capture a note to keep useful context.</p>:null}
  <div className="space-y-3">{rows.map(row=><article key={row.id} className="min-w-0 rounded-xl border bg-card p-4"><h2 className="text-lg font-medium">{row.title||row.name||'Saved record'}</h2>{row.status&&<p className="mt-1 text-sm text-muted-foreground">{row.status.replaceAll('_',' ')}</p>}
   {typeof row.current_value==='number'&&<p className="mt-2">{row.current_value} {row.unit} · Target {row.target}</p>}
   {(row.summary||row.description||row.body||row.problem)&&<p className="mt-2 whitespace-pre-wrap text-base leading-relaxed">{(row.summary||row.description||row.body||row.problem)?.slice(0,600)}</p>}
   {kind?<Link href={`/sources/${kind}/${encodeURIComponent(row.id)}`} className="mt-2 inline-flex min-h-11 items-center text-primary underline">Open saved record</Link>:<details className="mt-2"><summary className="min-h-11 cursor-pointer py-2 text-sm underline">Saved details</summary><dl className="space-y-2 text-sm">{Object.entries(row).filter(([key,value])=>key in detailLabels&&value!==null&&['string','number','boolean'].includes(typeof value)).map(([key,value])=><div key={key}><dt className="font-medium">{detailLabels[key]}</dt><dd className="whitespace-pre-wrap">{String(value)}</dd></div>)}</dl></details>}
  </article>)}</div>
  {rows.length<total&&!error&&<button type="button" disabled={busy} onClick={()=>void load(rows.length)} className="min-h-11 w-full rounded-lg border px-4">{busy?'Loading…':'Load more saved records'}</button>}
 </div>;
}

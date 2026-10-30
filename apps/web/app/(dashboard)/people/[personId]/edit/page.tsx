'use client';

import {useCallback,useEffect,useRef,useState} from 'react';
import {useParams,useRouter} from 'next/navigation';
import {api} from '@/lib/api/browser-client';
import type {Person} from '@/lib/api/domains';
import {PageHeader} from '@/components/shared/page-header';
import {ErrorState} from '@/components/shared/error-state';
import {PersonForm,type PersonFormValues} from '@/components/people/person-form';

export default function EditPersonPage(){
 const params=useParams();const id=String(params?.personId||'');const router=useRouter();
 const [person,setPerson]=useState<Person|null>(null),[loading,setLoading]=useState(true),[loadError,setLoadError]=useState<Error|undefined>(),[error,setError]=useState(''),[saving,setSaving]=useState(false);const pending=useRef(false);
 const load=useCallback(async()=>{setLoading(true);setLoadError(undefined);try{setPerson(await api.get<Person>(`/people/${id}`));}catch(failure){setLoadError(failure instanceof Error?failure:new Error('Could not load person'));}finally{setLoading(false);}},[id]);
 useEffect(()=>{if(id)void load();},[id,load]);
 async function save(values:PersonFormValues){
  if(pending.current)return;pending.current=true;setSaving(true);setError('');
  try{await api.patch(`/people/${id}`,values);router.push(`/people/${id}`);}
  catch{setError('Could not save your changes. Your entries are kept. Try again.');}
  finally{pending.current=false;setSaving(false);}
 }
 return <div className="mx-auto max-w-2xl"><PageHeader title="Edit person"/>{loading?<p role="status">Loading person…</p>:loadError?<ErrorState error={loadError} onRetry={()=>void load()}/>:person?<PersonForm person={person} onSave={values=>void save(values)} saving={saving} error={error} cancelHref={`/people/${id}`}/>:<ErrorState onRetry={()=>void load()}/>}</div>;
}

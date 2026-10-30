'use client';

import {useRef,useState} from 'react';
import {useRouter} from 'next/navigation';
import {api} from '@/lib/api/browser-client';
import type {Person} from '@/lib/api/domains';
import {PageHeader} from '@/components/shared/page-header';
import {PersonForm,type PersonFormValues} from '@/components/people/person-form';

export default function NewPersonPage(){
 const router=useRouter();const [saving,setSaving]=useState(false);const [error,setError]=useState('');const pending=useRef(false);
 async function save(values:PersonFormValues){
  if(pending.current)return;pending.current=true;setSaving(true);setError('');
  try{const person=await api.post<Person>('/people',values);router.push(`/people/${person.id}`);}
  catch{setError('Could not save this person. Your entries are kept. Try again.');}
  finally{pending.current=false;setSaving(false);}
 }
 return <div className="mx-auto max-w-2xl"><PageHeader title="Add person" description="Start with a name. Add other details when they are useful."/><PersonForm onSave={values=>void save(values)} saving={saving} error={error}/></div>;
}

'use client';

import * as React from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import {Button} from '@/components/ui/button';

interface ConfirmActionDialogProps{open:boolean;onOpenChange:(value:boolean)=>void;title:string;description:string;confirmLabel?:string;onConfirm:()=>void|Promise<void>;isDestructive?:boolean;}
export function ConfirmActionDialog({open,onOpenChange,title,description,confirmLabel='Confirm',onConfirm,isDestructive=true}:ConfirmActionDialogProps){
 const [busy,setBusy]=React.useState(false),[error,setError]=React.useState('');
 const pending=React.useRef(false),cancel=React.useRef<HTMLButtonElement>(null);
 React.useEffect(()=>{if(open)setError('');},[open]);
 async function confirm(){
  if(pending.current)return;pending.current=true;setBusy(true);setError('');
  try{await onConfirm();onOpenChange(false);}catch{setError('Could not complete this action. Try again.');}finally{pending.current=false;setBusy(false);}
 }
 return <Dialog.Root open={open} onOpenChange={value=>{if(!busy)onOpenChange(value);}}><Dialog.Portal>
  <Dialog.Overlay className="fixed inset-0 z-[300] bg-black/70"/>
  <Dialog.Content role="alertdialog" onOpenAutoFocus={event=>{event.preventDefault();cancel.current?.focus();}} className="fixed inset-x-4 top-1/2 z-[301] mx-auto max-h-[90dvh] max-w-md -translate-y-1/2 overflow-y-auto rounded-xl border bg-popover p-4 text-popover-foreground shadow-xl [overflow-wrap:anywhere]">
   <Dialog.Title className="text-xl font-semibold">{title}</Dialog.Title><Dialog.Description className="mt-3 text-base leading-relaxed text-muted-foreground">{description}</Dialog.Description>
   {error&&<p role="alert" className="mt-3 text-sm">{error}</p>}
   <div className="mt-5 flex flex-wrap justify-end gap-3"><Button ref={cancel} type="button" variant="outline" disabled={busy} onClick={()=>onOpenChange(false)}>Cancel</Button><Button type="button" variant={isDestructive?'destructive':'default'} disabled={busy} onClick={()=>void confirm()}>{busy?'Working…':confirmLabel}</Button></div>
  </Dialog.Content>
 </Dialog.Portal></Dialog.Root>;
}

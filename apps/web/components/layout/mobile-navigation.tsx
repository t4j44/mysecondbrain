'use client';

import * as React from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { usePathname } from 'next/navigation';
import { Ellipsis, X } from 'lucide-react';
import { Sidebar } from './sidebar';
import { isMoreActive } from '@/lib/navigation';

export function MobileNavigation() {
  const [open, setOpen] = React.useState(false);
  const pathname = usePathname();
  React.useEffect(() => { setOpen(false); }, [pathname]);
  return <Dialog.Root open={open} onOpenChange={setOpen}>
    <Dialog.Trigger asChild><button type="button" aria-current={isMoreActive(pathname) ? 'true' : undefined} className={`sb-interactive flex min-h-12 min-w-0 flex-col items-center justify-center gap-1 rounded-xl px-1 py-1 text-[11px] hover:bg-muted/60 ${isMoreActive(pathname) ? 'text-primary' : 'text-muted-foreground'}`}><span className="flex h-7 w-10 items-center justify-center"><Ellipsis className="h-5 w-5" aria-hidden="true" /></span><span>More</span></button></Dialog.Trigger>
    <Dialog.Portal>
      <Dialog.Overlay className="fixed inset-0 z-[200] bg-black/70" />
      <Dialog.Content aria-describedby={undefined} className="fixed inset-y-0 left-0 z-[201] w-80 max-w-[90vw] overflow-y-auto bg-background shadow-xl">
        <Dialog.Title className="sr-only">Navigation</Dialog.Title>
        <Dialog.Close asChild><button type="button" className="absolute right-2 top-2 z-10 inline-flex h-11 w-11 items-center justify-center rounded-lg bg-background" aria-label="Close navigation"><X className="h-5 w-5" /></button></Dialog.Close>
        <Sidebar className="min-h-full w-full border-none" />
      </Dialog.Content>
    </Dialog.Portal>
  </Dialog.Root>;
}

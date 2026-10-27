'use client';

import * as React from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { usePathname } from 'next/navigation';
import { Menu, X } from 'lucide-react';
import { Sidebar } from './sidebar';

export function MobileNavigation() {
  const [open, setOpen] = React.useState(false);
  const pathname = usePathname();
  React.useEffect(() => { setOpen(false); }, [pathname]);
  return <Dialog.Root open={open} onOpenChange={setOpen}>
    <Dialog.Trigger asChild><button type="button" className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-foreground hover:bg-muted lg:hidden" aria-label="Open navigation"><Menu className="h-5 w-5" /></button></Dialog.Trigger>
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

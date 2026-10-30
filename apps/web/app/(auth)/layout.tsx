import Link from 'next/link';
import {Brain} from 'lucide-react';
export default function AuthLayout({children}:{children:React.ReactNode}){
 return <div className="flex min-h-dvh bg-background text-foreground">
  <aside className="hidden w-1/2 flex-col justify-between border-r bg-card p-10 lg:flex">
   <Link href="/login" className="inline-flex min-h-11 items-center gap-3 text-xl font-semibold"><Brain className="h-7 w-7 text-primary"/>Second Brain</Link>
   <div className="max-w-lg space-y-5 py-12"><h1 className="text-4xl font-semibold leading-tight">Keep the context. Find it when you need it.</h1><p className="text-lg leading-relaxed text-muted-foreground">Save people, conversations and work in one place. Ask a question and check the supporting sources.</p><p className="rounded-xl border p-4 text-base leading-relaxed">Early closed beta. Avoid sensitive information. AI requests use minimized text, but automatic redaction can miss details.</p></div>
   <p className="text-sm text-muted-foreground">Second Brain · Closed beta</p>
  </aside>
  <main className="flex min-w-0 flex-1 items-center justify-center p-4 py-8 sm:p-8"><div className="w-full max-w-md space-y-6"><Link href="/login" className="inline-flex min-h-11 items-center gap-3 text-xl font-semibold lg:hidden"><Brain className="h-7 w-7 text-primary"/>Second Brain</Link>{children}</div></main>
 </div>;
}
import { redirect } from 'next/navigation';

export default function Home() {
  // Direct visitors straight to the secure authenticated Command Center dashboard
  redirect('/dashboard');
}

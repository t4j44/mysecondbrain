import Link from 'next/link';
import SignupForm from './signup-form';

// A web form is not a security boundary: staging/production Supabase Auth must
// also disable public signups. Invites are created using supported Auth admin APIs.
export default function SignupPage() {
  if (process.env.ALLOW_PUBLIC_SIGNUP === 'true') {
    return <SignupForm />;
  }
  return (
    <main className="space-y-5">
      <h1 className="text-3xl font-semibold">Second Brain is invite-only</h1>
      <p className="text-muted-foreground">We're testing a free, limited beta with a small
        group of invited users. Public registration is currently closed.</p>
      <p>Already have an invitation? <Link href="/login" className="underline">
        Sign in to your account</Link>.</p>
      <p className="text-sm text-muted-foreground">Before participating, review our
        <Link href="/privacy" className="underline"> beta privacy information</Link> and
        <Link href="/terms" className="underline"> participation information</Link>.
        These documents require operator approval before external invitations are issued.</p>
    </main>
  );
}

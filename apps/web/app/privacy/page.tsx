import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Beta privacy information',
  description: 'How Second Brain handles personal context during its limited, invitation-only beta.',
};

export default function BetaPrivacyInformation() {
  return (
    <main className="mx-auto max-w-3xl space-y-6 px-5 py-12 text-foreground">
      <Link href="/login" className="underline">Second Brain · Sign in</Link>
      <h1 className="text-3xl font-semibold">Closed-beta privacy information</h1>
      <p className="rounded-xl border p-4 text-sm">
        <strong>Pre-release disclosure — not a finalized legal privacy notice.</strong>{' '}
        The beta operator must approve the controller&apos;s legal identity, contact address, lawful basis,
        processors, international transfers and local legal obligations before inviting external testers.
        Do not treat this draft as permission for public signups.
      </p>
      <section className="space-y-3">
        <h2 className="text-xl font-semibold">What the beta may store</h2>
        <p>Account details, people and relationship notes, meetings and transcriptions, tasks,
          projects, commitments, uploaded documents and images, source references, integration
          settings, and security or activity events you choose to save. This is personal context,
          and it can include details about other people.</p>
        <h2 className="text-xl font-semibold">Where it is processed</h2>
        <p>The beta uses Supabase for authentication, PostgreSQL and private file storage,
          Render for the application backend, and Vercel for the web interface.
          Optional AI requests may send selected, minimized text to Google Gemini.
          Automatic redaction is imperfect. If you connect another AI assistant, that provider
          handles information according to its own terms and privacy policy.</p>
        <p><strong>Do not submit confidential, regulated, highly sensitive, or third-party
          personal information without an appropriate lawful basis and specific authorization.</strong></p>
        <h2 className="text-xl font-semibold">Who can access it</h2>
        <p>Product features are intended to restrict private content to the signed-in account
          owner and narrowly authorized technical operations. Any explicitly published portfolio
          material may become accessible through a share link; do not publish sensitive information.</p>
        <h2 className="text-xl font-semibold">Export and deletion limits</h2>
        <p>Account export provides supported structured records; <strong>original uploaded
          attachment bytes are not included</strong> in that archive. You must download or
          retain those files separately. Account deletion blocks access and queues cleanup;
          copies in provider backups, independent exports or other people&apos;s systems are
          not necessarily removed immediately. No fixed backup-purge period has been verified.</p>
        <h2 className="text-xl font-semibold">Pilot retention and contact</h2>
        <p>The final retention schedule, identity and contact details of the responsible
          operator, and escalation process must be supplied and approved with the beta invitation.
          Until then, this is a review draft, not a completed legal privacy policy.</p>
      </section>
      <p className="text-sm"><Link href="/terms" className="underline">Beta participation information</Link></p>
    </main>
  );
}

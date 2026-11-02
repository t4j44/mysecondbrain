import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Closed-beta participation information',
  description: 'Limitations and expected conduct for invited Second Brain beta testers.',
};

export default function BetaParticipationInformation() {
  return (
    <main className="mx-auto max-w-3xl space-y-6 px-5 py-12 text-foreground">
      <Link href="/login" className="underline">Second Brain · Sign in</Link>
      <h1 className="text-3xl font-semibold">Closed-beta participation information</h1>
      <p className="rounded-xl border p-4 text-sm">
        <strong>Review draft, not finalized Terms of Service.</strong> The beta operator must
        approve these terms, its legal identity, contact information and applicable law before
        issuing invitations.
      </p>
      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Invitation only, no payment</h2>
        <p>Participation in this pilot is free and limited to individually invited testers.
          There is no paid subscription or payment processing in this release.
          An invitation can be withdrawn and access may be suspended to protect the service.</p>
        <h2 className="text-xl font-semibold">Use restrictions</h2>
        <p>Use synthetic or low-risk information whenever possible. Do not upload sensitive,
          confidential or regulated records, another person&apos;s data without permission,
          credentials, or anything you lack authority to share. Do not attempt to access
          another user&apos;s workspace, evade access restrictions, or run abusive automated traffic.</p>
        <h2 className="text-xl font-semibold">Beta reliability and AI</h2>
        <p>Features may be incomplete, inaccurate or unavailable. AI answers, transcriptions,
          recommendations and inferred commitments require human verification. This beta is
          not suitable as the sole repository for important records or for safety-critical decisions.</p>
        <h2 className="text-xl font-semibold">Your control of information</h2>
        <p>Keep independent copies of important material. Supported account export omits
          original attachment bytes, and account deletion follows an asynchronous cleanup
          process with provider backup limits. See the <Link href="/privacy" className="underline">privacy information</Link>.</p>
        <h2 className="text-xl font-semibold">Feedback and support</h2>
        <p>Feedback may be used to improve the beta, but it does not grant permission to
          publish your name, data or words as a testimonial. The beta invitation must include
          an approved operator contact and support or incident reporting channel.</p>
      </section>
    </main>
  );
}

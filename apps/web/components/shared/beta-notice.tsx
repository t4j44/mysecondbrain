import Link from 'next/link';

/**
 * Compact status entry point. Full privacy disclosures remain in Settings,
 * while consent for sensitive AI/meeting actions stays at the point of use.
 */
export function BetaNotice() {
  return (
    <Link
      href="/settings/privacy"
      aria-label="Beta version — view privacy and data information"
      title="Beta · Privacy and data"
      className="sb-interactive inline-flex min-h-10 shrink-0 items-center gap-1.5 rounded-full border border-emerald-400/25 bg-emerald-400/10 px-3 text-[11px] font-semibold tracking-wide text-emerald-300 hover:border-emerald-400/50 hover:bg-emerald-400/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
    >
      <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" aria-hidden="true" />
      Beta
    </Link>
  );
}

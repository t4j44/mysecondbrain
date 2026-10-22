export function BetaNotice() {
  return (
    <aside aria-label="Closed beta privacy notice" className="border-b border-amber-500/20 bg-amber-500/5 px-4 text-sm leading-relaxed md:px-6">
      <details>
      <summary className="flex min-h-[44px] cursor-pointer items-center justify-between gap-2 text-amber-200"><span className="min-w-0">Beta · Avoid sensitive information</span><span className="shrink-0 underline">Privacy</span></summary>
      <p className="max-w-3xl pb-3 text-foreground"><strong>Early closed beta.</strong> Keep highly sensitive or confidential information out of this test.
      {' '}Your records are stored privately. AI features send minimized text to Google Gemini;
      automated redaction can miss identifying details. Google may use free-tier requests to
      improve its products. Connected AI assistants have their own data policies.</p>
      </details>
    </aside>
  );
}

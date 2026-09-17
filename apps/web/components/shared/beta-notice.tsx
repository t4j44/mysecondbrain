export function BetaNotice() {
  return (
    <aside aria-label="Closed beta privacy notice" className="mx-3 mt-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm leading-relaxed sm:mx-5 md:mx-6">
      <strong>Early closed beta.</strong> Keep highly sensitive or confidential information out of this test.
      {' '}Your records are stored privately. AI features send minimized text to Google Gemini;
      automated redaction can miss identifying details. Google may use free-tier requests to
      improve its products. Connected AI assistants have their own data policies.
    </aside>
  );
}

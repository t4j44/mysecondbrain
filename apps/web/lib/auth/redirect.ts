/**
 * Auth callbacks only redirect to paths on this application.
 * Never concatenate untrusted query parameters directly with the site origin.
 */
export function safeAuthReturnPath(candidate: string | null): string {
  const target = candidate || '/dashboard';
  if (
    !target.startsWith('/') ||
    target.startsWith('//') ||
    target.includes('\\') ||
    /[\u0000-\u001f\u007f]/.test(target)
  ) {
    return '/dashboard';
  }
  try {
    const url = new URL(target, 'https://local.invalid');
    if (url.origin !== 'https://local.invalid') return '/dashboard';
    return url.pathname + url.search + url.hash;
  } catch {
    return '/dashboard';
  }
}

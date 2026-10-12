export type Provider = 'google_drive' | 'google_calendar';
export type Integration = { id: string; provider_name: string; account_identifier?: string | null; is_connected: boolean };
export type AccountGroup = { key: string; name: string; email?: string; byProvider: Partial<Record<Provider, Integration>> };

export const UNKNOWN_ACCOUNT = 'Google account (not identified)';
export const PROVIDERS: { provider: Provider; label: string; blurb: string }[] = [
  { provider: 'google_drive', label: 'Drive', blurb: 'Save a Markdown copy of your records to your Drive.' },
  { provider: 'google_calendar', label: 'Calendar', blurb: 'Put tasks you choose on your calendar.' },
];

/** Connected capabilities grouped under the Google account they belong to, oldest account first. */
export function groupAccounts(items: Integration[]): AccountGroup[] {
  const groups = new Map<string, AccountGroup>();
  for (const item of items) {
    if (!item.is_connected || !PROVIDERS.some(entry => entry.provider === item.provider_name)) continue;
    const email = item.account_identifier?.trim().toLowerCase() || undefined;
    const key = email ?? '';
    const group = groups.get(key) ?? { key: key || 'unidentified', name: email ?? UNKNOWN_ACCOUNT, email, byProvider: {} };
    group.byProvider[item.provider_name as Provider] = item;
    groups.set(key, group);
  }
  return [...groups.values()];
}

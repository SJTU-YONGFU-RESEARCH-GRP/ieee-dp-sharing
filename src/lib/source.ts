/** Returns true only for URLs safe to show as "View source" on the public site. */

const PLACEHOLDER_PATTERNS = [
  /seed[-_]?sample/i,
  /example[-_]?dataport/i,
  /\/posts\/test-/i,
  /placeholder/i,
  /fake[-_]?/i,
  /sample[-_]?only/i,
];

export function isPublicSourceUrl(url: string | null | undefined): boolean {
  if (!url || !url.trim()) return false;
  try {
    const parsed = new URL(url);
    if (!['http:', 'https:'].includes(parsed.protocol)) return false;
    return !PLACEHOLDER_PATTERNS.some((re) => re.test(url));
  } catch {
    return false;
  }
}

export function sourceLinkLabel(url: string | null | undefined): string {
  if (!isPublicSourceUrl(url)) return 'Curated submission';
  return 'View source';
}

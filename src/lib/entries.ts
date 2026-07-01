import type { Entry, EntriesFile, FilterState } from './types';

import rawData from '../../data/entries.json';

const data = rawData as EntriesFile;

export function getAllEntries(): Entry[] {
  return data.entries;
}

export function getPublishedEntries(): Entry[] {
  return data.entries.filter(
    (e) =>
      e.moderation_status === 'approved' &&
      e.consent_status === 'granted' &&
      e.published_at !== null,
  );
}

export function getFeaturedEntries(): Entry[] {
  return getPublishedEntries().filter((e) => e.featured);
}

export function getPendingEntries(): Entry[] {
  return data.entries
    .filter((e) => e.moderation_status === 'pending')
    .sort((a, b) => (b.submitted_at ?? '').localeCompare(a.submitted_at ?? ''));
}

export function getPendingCount(): number {
  return data.entries.filter((e) => e.moderation_status === 'pending').length;
}

export function getUniqueValues(
  entries: Entry[],
  key: keyof Entry,
): string[] {
  const values = new Set<string>();
  for (const entry of entries) {
    const value = entry[key];
    if (typeof value === 'string' && value.trim()) {
      values.add(value);
    }
  }
  return [...values].sort();
}

export function getYears(entries: Entry[]): string[] {
  const years = new Set<string>();
  for (const entry of entries) {
    const date = entry.published_at ?? entry.submitted_at;
    if (date) years.add(date.slice(0, 4));
  }
  return [...years].sort().reverse();
}

export function filterEntries(
  entries: Entry[],
  filters: FilterState,
): Entry[] {
  const q = filters.query.trim().toLowerCase();

  return entries.filter((entry) => {
    if (filters.event && entry.event !== filters.event) return false;
    if (filters.society && entry.society !== filters.society) return false;
    if (filters.region && entry.region !== filters.region) return false;
    if (filters.topic && entry.dataset_topic !== filters.topic) return false;
    if (filters.postType && entry.post_type !== filters.postType) return false;
    if (filters.sentiment && entry.enrichment?.sentiment !== filters.sentiment) {
      return false;
    }
    if (filters.year) {
      const year = (entry.published_at ?? entry.submitted_at).slice(0, 4);
      if (year !== filters.year) return false;
    }
    if (!q) return true;

    const haystack = [
      entry.text,
      entry.display_name,
      entry.affiliation,
      entry.event,
      entry.society,
      entry.dataset_topic,
      ...(entry.tags ?? []),
      ...(entry.enrichment?.topics ?? []),
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase();

    return haystack.includes(q);
  });
}

export interface TopicCount {
  topic: string;
  count: number;
}

export function aggregateTopics(entries: Entry[]): TopicCount[] {
  const counts = new Map<string, number>();
  for (const entry of entries) {
    const topics = entry.enrichment?.topics ?? entry.tags ?? [];
    for (const topic of topics) {
      counts.set(topic, (counts.get(topic) ?? 0) + 1);
    }
  }
  return [...counts.entries()]
    .map(([topic, count]) => ({ topic, count }))
    .sort((a, b) => b.count - a.count);
}

export interface SentimentCount {
  sentiment: string;
  count: number;
}

export function aggregateSentiments(entries: Entry[]): SentimentCount[] {
  const counts = new Map<string, number>();
  for (const entry of entries) {
    const sentiment = entry.enrichment?.sentiment ?? 'unknown';
    counts.set(sentiment, (counts.get(sentiment) ?? 0) + 1);
  }
  const order = ['positive', 'mixed', 'neutral', 'negative', 'unknown'];
  return order
    .filter((s) => counts.has(s))
    .map((sentiment) => ({ sentiment, count: counts.get(sentiment)! }));
}

export function getDataMeta(): Pick<EntriesFile, 'version' | 'updated_at'> {
  return { version: data.version, updated_at: data.updated_at };
}

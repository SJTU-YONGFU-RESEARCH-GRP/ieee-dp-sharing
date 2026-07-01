export type ConsentStatus = 'pending' | 'granted' | 'revoked';
export type ModerationStatus = 'draft' | 'pending' | 'approved' | 'rejected';
export type SourceType =
  | 'linkedin_post'
  | 'linkedin_comment'
  | 'manual_submission'
  | 'event_feedback'
  | 'email_consented';
export type PostType =
  | 'testimonial'
  | 'discussion'
  | 'announcement'
  | 'question'
  | 'feedback'
  | null;
export type Region =
  | 'North America'
  | 'Europe'
  | 'Asia-Pacific'
  | 'Latin America'
  | 'Middle East & Africa'
  | 'Global'
  | null;
export type Sentiment = 'positive' | 'neutral' | 'mixed' | 'negative';

export interface Enrichment {
  sentiment: Sentiment;
  sentiment_score: number;
  topics: string[];
  quote: string | null;
  enriched_at: string;
}

export interface Entry {
  id: string;
  text: string;
  display_name: string;
  affiliation: string | null;
  profile_url: string | null;
  source_type: SourceType;
  source_url: string | null;
  event: string | null;
  society: string | null;
  region: Region;
  dataset_topic: string | null;
  post_type: PostType;
  consent_status: ConsentStatus;
  consent_note: string | null;
  moderation_status: ModerationStatus;
  approved_by: string | null;
  approved_at: string | null;
  submitted_at: string;
  published_at: string | null;
  featured: boolean;
  tags: string[];
  enrichment: Enrichment | null;
}

export interface EntriesFile {
  version: string;
  updated_at: string;
  entries: Entry[];
}

export interface FilterState {
  query: string;
  event: string;
  society: string;
  region: string;
  topic: string;
  year: string;
  postType: string;
  sentiment: string;
}

export const TOPIC_LABELS: Record<string, string> = {
  reproducibility: 'Reproducibility',
  citation: 'Citation',
  metadata: 'Metadata',
  'open-data': 'Open Data',
  discovery: 'Discovery',
  usability: 'Usability',
  trust: 'Trust',
  licensing: 'Licensing',
  community: 'Community',
  review: 'Peer Review',
};

export const REGIONS = [
  'North America',
  'Europe',
  'Asia-Pacific',
  'Latin America',
  'Middle East & Africa',
  'Global',
] as const;

export const POST_TYPES = [
  'testimonial',
  'discussion',
  'announcement',
  'question',
  'feedback',
] as const;

export const SOURCE_TYPES = [
  'linkedin_post',
  'linkedin_comment',
  'manual_submission',
  'event_feedback',
  'email_consented',
] as const;

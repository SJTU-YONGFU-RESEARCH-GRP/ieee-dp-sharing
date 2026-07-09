export const STAGING_FIELDS = [
  'status',
  'found_date',
  'hashtag',
  'post_url',
  'profile_url',
  'display_name',
  'affiliation',
  'text',
  'post_type',
  'event',
  'society',
  'region',
  'dataset_topic',
  'tags',
  'consent_observed',
  'editor_notes',
  'entry_id',
] as const;

export function csvEscape(value: string | null | undefined): string {
  const s = (value ?? '').replace(/\r?\n/g, ' ').trim();
  if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

export interface StagingRowInput {
  display_name: string;
  text: string;
  post_url?: string | null;
  affiliation?: string | null;
  post_type?: string | null;
  event?: string | null;
  society?: string | null;
  region?: string | null;
  dataset_topic?: string | null;
  tags?: string[];
  consent_observed?: string;
  editor_notes?: string | null;
}

export function buildStagingCsvLine(input: StagingRowInput): string {
  const today = new Date().toISOString().slice(0, 10);
  const tags = (input.tags?.length ? input.tags : ['ieeedataport']).join(';');
  const fields = [
    '',
    today,
    'ieeedataport',
    input.post_url ?? '',
    '',
    input.display_name,
    input.affiliation ?? '',
    input.text,
    input.post_type ?? 'testimonial',
    input.event ?? '',
    input.society ?? '',
    input.region ?? '',
    input.dataset_topic ?? '',
    tags,
    input.consent_observed ?? 'author_submitted',
    input.editor_notes ?? 'Submitted via website form.',
    '',
  ];
  return fields.map(csvEscape).join(',');
}

import type { PipelineStatus } from './types';

import rawStatus from '../../data/pipeline-status.json';

const status = rawStatus as PipelineStatus;

export function getPipelineStatus(): PipelineStatus {
  return status;
}

export function formatPipelineTime(iso: string | undefined): string {
  if (!iso) return '—';
  try {
    const d = new Date(iso.includes('T') ? iso : `${iso}T00:00:00Z`);
    return d.toLocaleString('en-US', {
      dateStyle: 'medium',
      timeStyle: 'short',
      timeZone: 'UTC',
    }) + ' UTC';
  } catch {
    return iso;
  }
}

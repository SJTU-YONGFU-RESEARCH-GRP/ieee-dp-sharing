import { defineConfig } from 'astro/config';

// GitHub project Pages serves at /{repo-name}/ — match website-trial-v1 pattern.
const GH_PAGES_BASE = process.env.GH_PAGES_BASE || 'ieee-dp-sharing';
const isProd = process.env.NODE_ENV === 'production';
const base = process.env.BASE_PATH || (isProd ? `/${GH_PAGES_BASE}/` : '/');

export default defineConfig({
  site: `https://sjtu-yongfu-research-grp.github.io`,
  base,
  output: 'static',
  build: {
    format: 'directory',
  },
});

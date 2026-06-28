import { defineConfig } from 'astro/config';

const base = process.env.ASTRO_BASE ?? '/';
const site = process.env.ASTRO_SITE ?? 'https://www.alexandreinteriors.com';

export default defineConfig({
  site,
  base,
  trailingSlash: 'never',
  build: {
    format: 'file',
  },
});

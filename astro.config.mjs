import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://www.alexandreinteriors.com',
  trailingSlash: 'never',
  build: {
    format: 'file',
  },
});

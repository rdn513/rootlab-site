// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import typograph from './scripts/typograph-integration.mjs';

export default defineConfig({
  site: 'https://root-lab.ru',
  trailingSlash: 'ignore',
  build: { format: 'directory', inlineStylesheets: 'always' },
  integrations: [
    sitemap({
      filter: (page) => !page.includes('/404'),
      i18n: undefined,
    }),
    typograph(),
  ],
});

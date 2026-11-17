// Готовит собранный сайт к показу на GitHub Pages по адресу с подпапкой
// (https://rdn513.github.io/rootlab-site/): добавляет префикс к ссылкам
// и закрывает копию от индексации. Боевую сборку для root-lab.ru не трогает.
// Запуск: node scripts/pages-preview.mjs /rootlab-site
import { readdir, readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

const base = (process.argv[2] || '').replace(/\/$/, '');
if (!base.startsWith('/')) throw new Error('Укажите базовый путь, например /rootlab-site');

async function walk(d) {
  const o = [];
  for (const e of await readdir(d, { withFileTypes: true })) {
    const p = join(d, e.name);
    e.isDirectory() ? o.push(...(await walk(p))) : o.push(p);
  }
  return o;
}

for (const f of await walk('dist')) {
  if (!/\.(html|css|js)$/.test(f)) continue;
  let s = await readFile(f, 'utf8');
  s = s
    .replace(/(href|src|action)="\/(?!\/)/g, `$1="${base}/`)
    .replace(/url\(\/(?!\/)/g, `url(${base}/`)
    .replace(/(["'])\/_astro\//g, `$1${base}/_astro/`);
  if (f.endsWith('.html')) {
    s = s.replace('<head>', '<head><meta name="robots" content="noindex, nofollow">');
  }
  await writeFile(f, s);
}
await writeFile('dist/robots.txt', 'User-agent: *\nDisallow: /\n');
console.log(`✓ Превью для GitHub Pages: база ${base}, индексация закрыта`);

// Проверка сборки: JSON-LD, метки бота, согласие в формах, заглушки.
// Запуск: node scripts/verify.mjs (после npm run build)
import { readdir, readFile } from 'node:fs/promises';
import { join } from 'node:path';
async function walk(d) { const o = []; for (const e of await readdir(d, { withFileTypes: true })) { const p = join(d, e.name); e.isDirectory() ? o.push(...await walk(p)) : p.endsWith('.html') && o.push(p); } return o; }
const tagPages = {}; let errors = 0; const ph = {};
for (const f of (await walk('dist')).sort()) {
  const h = await readFile(f, 'utf8');
  const page = f.replace(/^dist/, '').replace(/index\.html$/, '');
  const types = [];
  for (const m of h.matchAll(/<script type="application\/ld\+json">(.*?)<\/script>/gs)) {
    try { types.push(JSON.parse(m[1])['@type']); } catch { errors++; console.error('✗ JSON-LD', page); }
  }
  for (const m of h.matchAll(/href="(https:\/\/t\.me\/rootlab_help_bot[^"]*)"/g)) {
    const t = new URL(m[1].replace(/&amp;/g, '&')).searchParams.get('start');
    if (!t) { errors++; console.error('✗ кнопка без метки', page); }
    (tagPages[t] ??= new Set()).add(page);
  }
  for (const fm of h.matchAll(/<form class="lead"[\s\S]*?<\/form>/g)) {
    if (!/name="consent" required/.test(fm[0]) || !/href="\/privacy\/"/.test(fm[0])) { errors++; console.error('✗ форма без согласия', page); }
  }
  const text = h.replace(/<script[\s\S]*?<\/script>/g, '');
  for (const m of text.matchAll(/\[([^\]<>]*(?:уточнить|заглушка|утвердит)[^\]<>]*)\]/g)) (ph[`[${m[1]}]`] ??= new Set()).add(page);
  console.log(page.padEnd(14), 'schema:', types.join(', '));
}
console.log('\nМетки бота:'); for (const [t, p] of Object.entries(tagPages).sort()) console.log(' ', t.padEnd(28), [...p].length > 3 ? 'все страницы (шапка)' : [...p].join(' '));
console.log('\nЗаглушки:'); for (const [t, p] of Object.entries(ph).sort()) console.log(' ', t, '→', [...p].length > 8 ? 'все страницы' : [...p].join(' '));
if (errors) process.exit(1);

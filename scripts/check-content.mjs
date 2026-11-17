// Проверка собранного сайта на запрещённые формулировки из ТЗ.
// Запуск: npm run check:content (автоматически после npm run build).
import { readdir, readFile } from 'node:fs/promises';
import { join } from 'node:path';

const banned = [
  /704[\s -]*70[\s -]*70/, /499\)?[\s ]*704/, /2011/,
  /24\s*\/\s*7/, /15[\s ]*минут/i, /настоящий[\s ]+24/i, /вообще когда-нибудь спят/i,
  /highload/i, /правило[\s ]+15/i, /финансов\S*[\s ]+ответственност/i,
  /защит\S*[\s ]+информаци/i, /\bКИИ\b/, /ФСТЭК/i, /MLOps/i, /импортозамещ/i,
  /nixys/i, /99[,.]9/, /\d+\+[\s ]*(проект|клиент)/i,
];

async function walk(d) {
  const out = [];
  for (const e of await readdir(d, { withFileTypes: true })) {
    const p = join(d, e.name);
    if (e.isDirectory()) out.push(...(await walk(p)));
    else if (/\.(html|xml|txt|js)$/.test(p)) out.push(p);
  }
  return out;
}

let bad = 0;
for (const f of await walk('dist')) {
  const text = (await readFile(f, 'utf8'));
  for (const re of banned) {
    const m = text.match(re);
    if (m) { bad++; console.error(`✗ ${f}: «${m[0]}» (${re})`); }
  }
}
if (bad) { console.error(`\nНайдено запрещённых формулировок: ${bad}`); process.exit(1); }
console.log('✓ Запрещённых формулировок не найдено');

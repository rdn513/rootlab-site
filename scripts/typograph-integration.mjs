// Типограф: после сборки расставляет неразрывные пробелы в тексте страниц.
// Трогает только текст между тегами; <script>, <style>, <pre>, <code>, <svg>,
// <textarea> и атрибуты не изменяет.
import { readdir, readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const NB = ' ';
const SHORT =
  'в|во|и|с|со|к|ко|о|об|у|а|но|за|на|по|до|от|не|из|ни|для|при|без|или|что|как|раз|вы|мы|их|ее|её|его|это|то|же';

export function typo(text) {
  let t = text;
  // группы разрядов: 12 000, 1 000 000
  for (let i = 0; i < 3; i++) t = t.replace(/(\d) (\d{3})(?!\d)/g, `$1${NB}$2`);
  // число + единица/слово: 5 рабочих, 2 часа, 30 %
  t = t.replace(/(\d) (?=[а-яёА-ЯЁ%₽])/g, `$1${NB}`);
  // перед ₽ и тире
  t = t.replace(/ (₽|—)/g, `${NB}$1`);
  // после коротких слов (повтор для цепочек «и в»)
  const re = new RegExp(`(^|[\\s(« ])(${SHORT}) `, 'gi');
  for (let i = 0; i < 2; i++) t = t.replace(re, `$1$2${NB}`);
  // «от 90 000» — не отрывать «от»/«до» уже покрыто SHORT
  return t;
}

const SKIP = /^<(script|style|pre|code|svg|textarea)\b/i;

export function typographHtml(html) {
  const parts = html.split(/(<[^>]+>)/);
  let skip = null;
  for (let i = 0; i < parts.length; i++) {
    const p = parts[i];
    if (p.startsWith('<')) {
      if (!skip) {
        const m = p.match(SKIP);
        if (m && !p.endsWith('/>')) skip = m[1].toLowerCase();
      } else if (p.toLowerCase().startsWith(`</${skip}`)) {
        skip = null;
      }
      continue;
    }
    if (!skip && p.trim()) parts[i] = typo(p);
  }
  return parts.join('');
}

async function walk(dir) {
  const out = [];
  for (const e of await readdir(dir, { withFileTypes: true })) {
    const p = join(dir, e.name);
    if (e.isDirectory()) out.push(...(await walk(p)));
    else if (p.endsWith('.html')) out.push(p);
  }
  return out;
}

export default function typograph() {
  return {
    name: 'rootlab-typograph',
    hooks: {
      'astro:build:done': async ({ dir }) => {
        const root = fileURLToPath(dir);
        for (const f of await walk(root)) {
          const html = await readFile(f, 'utf8');
          await writeFile(f, typographHtml(html));
        }
      },
    },
  };
}

// Выгружает цены, тарифы, контакты и метки из src/data/site.ts для Telegram-бота.
// Так у сайта и бота один источник данных. Запускается в npm run build.
import { writeFile } from 'node:fs/promises';
const d = await import('../src/data/site.ts');
const out = {
  _comment: 'Файл генерируется из src/data/site.ts (npm run build). Не правьте вручную.',
  company: d.company,
  social: d.social,
  products: d.products,
  plans: d.plans,
  planRows: d.planRows,
  planNotes: d.planNotes,
  firstClients: d.firstClients,
  partners: d.partners,
  botTags: d.botTags,
  privacyUrl: `${d.company.url}/privacy/`,
};
await writeFile('bot/app/site_data.json', JSON.stringify(out, null, 2) + '\n');
console.log('✓ bot/app/site_data.json обновлён');

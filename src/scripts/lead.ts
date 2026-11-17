// Отправка заявки с формы.
// Адрес обработчика задаётся в src/data/site.ts → leadForm.endpoint.
// [куда отправлять заявки — уточнить]
import { goal } from './analytics';

export type Lead = {
  name: string;
  contact: string;
  site?: string;
  message?: string;
  consent?: string;
  source: string;
  company_website?: string; // ловушка для ботов, должна быть пустой
};

export async function sendLead(endpoint: string, lead: Lead): Promise<{ ok: boolean }> {
  if (lead.company_website) return { ok: true }; // бот — молча «принимаем»

  const payload = { ...lead, page: location.pathname, sentAt: new Date().toISOString() };
  delete (payload as Partial<Lead>).company_website;

  if (!endpoint) {
    // Демо-режим: обработчик ещё не подключён.
    console.info('[RootLab] Заявка (демо-режим, никуда не отправлена):', payload);
    goal('form_submit', { source: lead.source });
    return { ok: true };
  }

  try {
    const r = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (r.ok) goal('form_submit', { source: lead.source });
    return { ok: r.ok };
  } catch {
    return { ok: false };
  }
}

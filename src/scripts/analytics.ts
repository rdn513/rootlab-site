// Яндекс Метрика, баннер согласия и цели.
// Номер счётчика и режим согласия — в src/data/site.ts (analytics).
declare global {
  interface Window {
    __rl: { metrika: { id: string; requireConsent: boolean } };
    ym?: (...args: unknown[]) => void;
  }
}

const KEY = 'rl-cookie-consent';

function store(v?: string): string | null {
  try {
    if (v) localStorage.setItem(KEY, v);
    return localStorage.getItem(KEY);
  } catch {
    return null;
  }
}

function loadMetrika(id: string) {
  if (!id || window.ym) return;
  (function (m: any, e: Document, t: string, r: string, i: string) {
    m[i] = m[i] || function () { (m[i].a = m[i].a || []).push(arguments); };
    m[i].l = Date.now();
    const k = e.createElement(t) as HTMLScriptElement;
    k.async = true; k.src = r;
    e.head.appendChild(k);
  })(window, document, 'script', 'https://mc.yandex.ru/metrika/tag.js', 'ym');
  window.ym!(Number(id), 'init', { clickmap: true, trackLinks: true, accurateTrackBounce: true, webvisor: false });
}

/** Отправить цель в Метрику (если счётчик загружен). */
export function goal(name: string, params?: Record<string, unknown>) {
  const id = window.__rl?.metrika.id;
  if (id && window.ym) window.ym(Number(id), 'reachGoal', name, params);
}

export function initAnalytics() {
  const { id, requireConsent } = window.__rl.metrika;
  const banner = document.getElementById('cookie');
  const choice = store();

  if (!requireConsent || choice === 'yes') loadMetrika(id);
  if (requireConsent && !choice && banner) banner.hidden = false;

  banner?.addEventListener('click', (e) => {
    const b = (e.target as HTMLElement).closest<HTMLButtonElement>('[data-consent]');
    if (!b) return;
    const v = b.dataset.consent!;
    store(v);
    banner.hidden = true;
    if (v === 'yes') loadMetrika(id);
  });

  // Цели на клики по кнопкам бота: data-goal="bot_<метка>"
  document.addEventListener('click', (e) => {
    const a = (e.target as HTMLElement).closest<HTMLElement>('[data-goal]');
    if (a) goal(a.dataset.goal!);
  });
}

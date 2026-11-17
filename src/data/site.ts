/**
 * ЕДИНЫЙ ФАЙЛ ДАННЫХ САЙТА ROOTLAB
 * ------------------------------------------------------------------
 * Здесь лежат цены, тарифы, сроки, контакты, ссылки, метки бота,
 * команда, частые вопросы и настройки аналитики. Вёрстка берёт
 * всё отсюда: поменяли цифру — она обновится на всех страницах,
 * в таблицах и в разметке schema.org.
 *
 * Как править:
 *  - цены пишите числом без пробелов: 35000 (пробелы и «₽» сайт расставит сам);
 *  - текст в квадратных скобках вида «[ИНН — уточнить]» — заглушка,
 *    она подсвечивается на сайте жёлтым, чтобы её было видно;
 *  - после правки: `npm run build` и выложить папку dist/.
 */

/* ---------- Компания и контакты ---------- */

export const company = {
  name: 'RootLab',
  url: 'https://root-lab.ru',
  city: 'Екатеринбург',
  region: 'Свердловская область',
  /** Телефон в виде, как его показывать. Пока заглушка — ссылка tel: не создаётся. */
  phone: '[телефон — уточнить]',
  email: 'hello@root-lab.ru',
  copyright: '© 2026 RootLab',
  legal: {
    name: '[ООО «…» — уточнить]',
    inn: '[ИНН — уточнить]',
    ogrn: '[ОГРН — уточнить]',
  },
};

/** Ссылки на соцсети для подвала и schema.org */
export const social = [
  { name: 'Telegram-канал', url: 'https://t.me/journal_RL' },
  { name: 'Дзен', url: 'https://dzen.ru/rootlab' },
  { name: 'ВКонтакте', url: 'https://vk.com/journal_rl' },
];

/* ---------- Telegram-бот и метки источника ---------- */

export const bot = {
  url: 'https://t.me/rootlab_help_bot',
};

/**
 * Все метки ?start= для кнопок. Ключ — где стоит кнопка, значение — метка.
 * Метка попадает в бота и в цель Метрики «bot_<метка>».
 * Telegram разрешает латиницу, цифры, «_» и «-», до 64 символов.
 */
export const botTags = {
  header: 'site_header',
  mobileMenu: 'site_menu',
  hero: 'site_hero',
  heroQuestion: 'site_hero_question',
  heroCheckup: 'site_hero_checkup',
  pricingCheckup: 'site_pricing_checkup',
  pricingAudit: 'site_pricing_audit',
  pricingEmergency: 'site_pricing_emergency',
  pricingOrder: 'site_pricing_order',
  pricingBasic: 'site_pricing_basic',
  pricingBusiness: 'site_pricing_business',
  pricingNightShift: 'site_pricing_night',
  firstClients: 'site_first_clients',
  team: 'site_team_question',
  final: 'site_final',
  finalCheckup: 'site_final_checkup',
  // внутренние страницы
  auditPage: 'site_audit',
  auditPageCheckup: 'site_audit_checkup',
  auditPageBottom: 'site_audit_bottom',
  auditCardCheckup: 'site_audit_card_checkup',
  auditCardAudit: 'site_audit_card_audit',
  supportTop: 'site_support',
  supportBasic: 'site_support_basic',
  supportBusiness: 'site_support_business',
  supportBottom: 'site_support_bottom',
  supportNight: 'site_support_night',
  emergencyTop: 'site_emergency',
  emergencyAside: 'site_emergency_card',
  emergencyBottom: 'site_emergency_bottom',
  partners: 'site_partners',
  partnersBottom: 'site_partners_bottom',
  devops: 'site_devops',
  devopsBottom: 'site_devops_bottom',
  migration: 'site_migration',
  migrationBottom: 'site_migration_bottom',
  blog: 'site_blog',
  notFound: 'site_404',
  formError: 'site_form_error', // ссылка в сообщении об ошибке формы
} as const;

export type BotTag = keyof typeof botTags;

export function botLink(key: BotTag): string {
  return `${bot.url}?start=${botTags[key]}`;
}

/* ---------- Аналитика и форма ---------- */

export const analytics = {
  /** Номер счётчика Яндекс Метрики. Пусто — счётчик не подключается. */
  metrikaId: '', // [номер счётчика Метрики — уточнить]
  /**
   * true — Метрика загружается только после согласия в баннере cookie.
   * Поставьте false, если юрист подтвердит, что согласие не требуется.
   */
  requireConsent: true,
};

export const leadForm = {
  /**
   * Куда отправлять заявки с формы. Принимает бот на VPS (папка bot/),
   * карточка заявки приходит в Telegram-чат команды.
   * Пусто — демо-режим: форма показывает «Заявка принята» и пишет в консоль.
   */
  endpoint: 'https://api.root-lab.ru/lead',
};

/* ---------- Разовые продукты ---------- */

export type Product = {
  id: string;
  name: string;
  audience: string;
  summary: string;
  includes: string[];
  term: string;
  price: number;
  priceFrom?: boolean;
  unit?: string; // по умолчанию «₽»
  priceNote?: string;
  cta: string;
  tag: BotTag;
  page?: string;
};

export const products: Product[] = [
  {
    id: 'checkup',
    name: 'Техосмотр сайта',
    audience: 'Для владельцев интернет-магазинов, онлайн-школ, сервисов записи',
    summary: 'Проверим, что ваш сайт переживёт сбой, распродажу и уход подрядчика.',
    includes: [
      'Есть ли рабочие запасные копии сайта и базы заказов',
      'У кого есть доступы и где лежат пароли',
      'Выдержит ли сайт наплыв покупателей',
      'Незапертые двери, через которые можно унести базу клиентов',
      'Две страницы простым языком: что в порядке, что опасно, что сделать первым',
    ],
    term: '5 рабочих дней',
    price: 12000,
    cta: 'Заказать техосмотр',
    tag: 'pricingCheckup',
    page: '/audit/#checkup',
  },
  {
    id: 'audit',
    name: 'Экспресс-аудит инфраструктуры',
    audience: 'Для веб-студий и продуктовых команд',
    summary: 'Полная картина рисков и план работ, который можно отдать любому подрядчику.',
    includes: [
      'Отчёт с рисками по приоритетам',
      'План работ с оценкой в часах',
      'Часовой созвон с техническим директором',
    ],
    term: '5 рабочих дней',
    price: 30000,
    priceNote: 'засчитывается в стоимость работ',
    cta: 'Заказать аудит',
    tag: 'pricingAudit',
    page: '/audit/',
  },
  {
    id: 'emergency',
    name: 'Аварийная помощь',
    audience: 'Для всех, у кого прямо сейчас что-то упало',
    summary: 'Подключаемся, поднимаем сайт или сервер, коротко разбираем причину.',
    includes: [
      'Подключение к серверу и поиск причины',
      'Восстановление работы сайта',
      'Короткий разбор: что случилось и как не допустить снова',
    ],
    term: 'По факту',
    price: 5000,
    unit: '₽/час',
    priceNote: 'минимум 2 часа',
    cta: 'Нужна помощь сейчас',
    tag: 'pricingEmergency',
    page: '/emergency/',
  },
  {
    id: 'order',
    name: 'Проект «Порядок»',
    audience: 'Для клиентов после аудита',
    summary: 'Делаем то, что нашли на аудите, и оставляем систему, за которой легко следить.',
    includes: [
      'Запасные копии с проверкой восстановления',
      'Сигнализация: узнаём о сбое раньше покупателей',
      'Обновления сайта выходят без поломок и ночных работ',
      'Документация: схема, доступы, инструкции',
    ],
    term: '2–6 недель',
    price: 90000,
    priceFrom: true,
    cta: 'Обсудить проект',
    tag: 'pricingOrder',
    page: '/devops/',
  },
];

/* ---------- Ежемесячное сопровождение ---------- */

export type Plan = {
  id: 'basic' | 'business';
  name: string;
  price: number;
  scope: string;
  tag: BotTag;
  featured?: boolean;
};

export const plans: Plan[] = [
  { id: 'basic', name: 'Базовый', price: 35000, scope: 'До 3 серверов, один проект', tag: 'pricingBasic' },
  { id: 'business', name: 'Бизнес', price: 80000, scope: 'До 8 серверов', tag: 'pricingBusiness', featured: true },
];

/**
 * Строки сравнения тарифов. В каждой строке — подпись и значения
 * для «Базового» и «Бизнеса» (true = «Да», false = «Нет»).
 * plain — формулировка простым языком для главной, tech — для страницы /support.
 */
export type PlanRow = {
  plain: string;
  tech: string;
  basic: string | boolean;
  business: string | boolean;
};

export const planRows: PlanRow[] = [
  { plain: 'Объём', tech: 'Объём', basic: 'До 3 серверов, один проект', business: 'До 8 серверов' },
  {
    plain: 'Сигнализация о сбоях круглосуточно',
    tech: 'Автоматический мониторинг 24 часа в сутки',
    basic: true,
    business: true,
  },
  {
    plain: 'Запасные копии с проверкой восстановления',
    tech: 'Бэкапы с тестовым восстановлением',
    basic: 'Раз в месяц',
    business: 'Раз в месяц',
  },
  { plain: 'Часы инженера на ваши задачи', tech: 'Часы инженера на задачи', basic: '4 часа', business: '12 часов' },
  {
    plain: 'Помощь с выпуском обновлений',
    tech: 'Поддержка релизов и CI/CD',
    basic: false,
    business: true,
  },
  {
    plain: 'Начинаем чинить, если сайт не открывается',
    tech: 'Реакция на недоступность',
    basic: 'До 2 часов, с 9 до 21 по будням',
    business: 'До 1 часа, с 9 до 22 ежедневно',
  },
  {
    plain: 'Обычные заявки',
    tech: 'Плановые заявки',
    basic: 'Следующий рабочий день',
    business: 'В тот же день',
  },
  {
    plain: 'Компенсация, если мы опоздали',
    tech: 'Компенсация за нарушение срока реакции',
    basic: false,
    business: '5% месячной платы за случай, до 30%',
  },
  { plain: 'Отчёт', tech: 'Отчётность', basic: 'Раз в месяц', business: 'Раз в месяц + разбор раз в квартал' },
];

export const planNotes = {
  timezone: 'Время реакции указано по Екатеринбургу (UTC+5).',
  nightShift: 'Нужна круглосуточная дежурная смена? Напишите — обсудим отдельно.',
};

/* ---------- Предложение первым клиентам ---------- */

export const firstClients = {
  discount: 40, // %
  months: 3,
  slots: 3,
};

/* ---------- Условия для веб-студий ---------- */

export const partners = {
  revenueShare: 15, // % от платежей приведённого клиента
  revenueShareMonths: 6,
  whiteLabelDiscount: '20–30', // % при работе под именем студии
};

/* ---------- Команда ---------- */

export const team = [
  {
    name: 'Виктор',
    surname: 'Вайнер',
    role: 'CTO — технический директор',
    areas: 'Технологии · инфраструктура · безопасность · инженерия',
    text: 'Сам проводит аудиты, проектирует архитектуру и берёт сложные работы.',
    details: '[Стаж, проекты, сертификаты — уточнить]',
    photo: '/team/viktor-vayner.webp',
  },
  {
    name: 'Дмитрий',
    surname: 'Рензяк',
    role: 'CBO — директор по развитию бизнеса',
    areas: 'Бизнес · операции · аналитика · работа с клиентами',
    text: 'Договоры, сроки, связь с вами. Отвечает за то, чтобы вы всегда знали, что происходит.',
    details: '',
    photo: '/team/dmitriy-renzyak.webp',
  },
];

/* ---------- Частые вопросы главной ---------- */

export const faq: { q: string; a: string }[] = [
  {
    q: 'Чем вы лучше штатного админа?',
    a: 'Сопровождение стоит от 35 000 ₽ в месяц — заметно меньше зарплаты штатного DevOps-инженера. Вы не платите за отпуск и больничные, а всё, что мы делаем, записано в документации, а не в голове одного человека. Если админ у вас уже есть — возьмём то, до чего у него не доходят руки.',
  },
  {
    q: 'Что если вы пропадёте?',
    a: 'Всё, что мы настроили, описано в документации, которая хранится у вас. Доступы лежат в вашем менеджере паролей. Новый подрядчик или свой инженер продолжит работу без нас и без «разведки».',
  },
  {
    q: 'Работаете ли с 1С-Битрикс?',
    a: 'Да, с серверной частью: окружение, запасные копии, кеш, обновления, запас по нагрузке. Код сайта не дорабатываем — это работа вашего разработчика или студии.',
  },
  {
    q: 'Как вы получаете доступы и что с персональными данными?',
    a: 'Сначала подписываем соглашение о конфиденциальности, потом получаем доступы — через менеджер паролей, а не в чате. Каждому инженеру — отдельная учётная запись, которую вы можете отключить в любой момент. Данные ваших покупателей к себе не выгружаем: работаем на ваших серверах.',
  },
  {
    q: 'Нужно ли подписывать договор на год?',
    a: 'Нет. Техосмотр и аудит — разовая работа по фиксированной цене. Сопровождение — помесячное, отказаться можно с уведомлением за [срок — уточнить].',
  },
  {
    q: 'Что если после аудита мы не захотим продолжать?',
    a: 'Отчёт и план работ останутся у вас. Можно сделать всё самим или отдать план другому подрядчику. Если продолжите с нами, 30 000 ₽ за аудит засчитаем в стоимость работ.',
  },
  {
    q: 'Что будет, если сайт упадёт ночью?',
    a: 'Сигнализация работает круглосуточно. Срок, за который мы начинаем чинить, зависит от тарифа: на «Базовом» — до 2 часов с 9 до 21 по будням, на «Бизнесе» — до 1 часа с 9 до 22 ежедневно, по Екатеринбургу. Нужна ночная дежурная смена — обсудим отдельно.',
  },
  {
    q: 'С каким хостингом вы работаете?',
    a: 'С обычными VPS и выделенными серверами у любого хостера и с российскими облаками. Если сайт на виртуальном хостинге без доступа к серверу, честно скажем, что там можно сделать, а что нет. Переезд с зарубежного хостинга — тоже к нам.',
  },
];

/* ---------- Навигация ---------- */

export const nav = [
  { href: '/audit/', label: 'Аудит' },
  { href: '/support/', label: 'Сопровождение' },
  { href: '/#pricing', label: 'Цены' },
  { href: '/partners/', label: 'Веб-студиям' },
  { href: '/emergency/', label: 'Упал сайт?', alert: true },
];

export const footerNav = [
  { href: '/audit/', label: 'Аудит и техосмотр' },
  { href: '/support/', label: 'Сопровождение' },
  { href: '/emergency/', label: 'Аварийная помощь' },
  { href: '/devops/', label: 'Выпуск обновлений' },
  { href: '/migration/', label: 'Переезд в российское облако' },
  { href: '/partners/', label: 'Веб-студиям' },
  { href: '/blog/', label: 'Блог' },
];

/* ---------- Утилиты форматирования ---------- */

const NBSP = ' ';

/** 12000 → «12 000» с неразрывным пробелом */
export function num(n: number): string {
  return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, NBSP);
}

/** 12000 → «12 000 ₽» */
export function rub(n: number, unit = '₽'): string {
  return `${num(n)}${NBSP}${unit}`;
}

export function productPrice(p: Product): string {
  return `${p.priceFrom ? `от${NBSP}` : ''}${rub(p.price, p.unit ?? '₽')}`;
}

export function getProduct(id: string): Product {
  const p = products.find((x) => x.id === id);
  if (!p) throw new Error(`Нет продукта ${id}`);
  return p;
}

/** true, если строка — заглушка вида «[… — уточнить]» */
export function isPlaceholder(s: string | undefined | null): boolean {
  return !!s && /^\[.*\]$/.test(s.trim());
}

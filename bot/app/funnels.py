"""Воронки бота: какие вопросы задаём и в каком порядке.

Каждая кнопка сайта ведёт в бота с меткой ?start=… (см. botTags в
src/data/site.ts). Метка определяет воронку (TAG_FUNNEL) и иногда
заранее заполняет ответ (TAG_PREFILL) — тогда этот вопрос не задаём.

Чтобы поменять текст вопроса или варианты ответа — правьте этот файл.
Цены здесь не пишем: они берутся из site_data.json.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .data import plan, product, product_price, rub, site

Answers = dict[str, str]


@dataclass
class Step:
    key: str
    text: str
    kind: str = "choice"  # choice | text | contact
    options: list[tuple[str, str]] = field(default_factory=list)  # (value, подпись кнопки)
    skippable: bool = False
    label: str = ""  # как показать ответ в карточке для команды
    when: Callable[[Answers], bool] | None = None
    note: Callable[[Answers], str | None] | None = None  # подсказка после ответа


@dataclass
class Funnel:
    id: str
    title: str  # для карточки и статистики
    emoji: str
    intro: Callable[[], str]
    steps: list[Step]
    done: Callable[[Answers], str]
    urgent: bool = False
    remind_after_min: int | None = None  # своё время первого напоминания


def _contact_step() -> Step:
    return Step(
        key="contact_way",
        text="Как с вами связаться?",
        kind="contact",
        options=[("tg", "Пишите сюда, в Telegram"), ("phone", "Позвоните мне")],
        label="Связь",
    )


def _site_step(text: str = "Адрес сайта или проекта?") -> Step:
    return Step(key="site", text=text, kind="text", skippable=True, label="Сайт")


# ---------- Вопрос инженеру ----------

def _q_intro() -> str:
    return (
        "Здравствуйте! Это команда RootLab — инженеры для сайтов и сервисов без своего DevOps.\n\n"
        "Напишите вопрос одним сообщением. Ответит инженер в рабочее время."
    )


QUESTION = Funnel(
    id="question",
    title="Вопрос инженеру",
    emoji="💬",
    intro=_q_intro,
    steps=[
        Step(key="question", text="Ваш вопрос:", kind="text", label="Вопрос"),
        _site_step("Если вопрос про конкретный сайт — пришлите адрес."),
        _contact_step(),
    ],
    done=lambda a: "Вопрос у команды. Ответим здесь же, в этом чате.",
)


# ---------- Экспресс-аудит ----------

def _audit_intro() -> str:
    p = product("audit")
    return (
        f"<b>{p['name']}</b>\n"
        f"{p['term']} · {product_price('audit')}, {p['priceNote']}.\n\n"
        "Что получите: отчёт с рисками по приоритетам, план работ с оценкой в часах "
        "и часовой созвон с техническим директором.\n\n"
        "Несколько коротких вопросов — около минуты."
    )


def _audit_who_note(a: Answers) -> str | None:
    if a.get("who") == "shop":
        c = product("checkup")
        return (
            f"Для небольшого сайта обычно хватает техосмотра: {c['term']}, {product_price('checkup')}, "
            "две страницы простым языком. Если хотите — так и запишем, инженер уточнит при разговоре."
        )
    return None


AUDIT = Funnel(
    id="audit",
    title="Экспресс-аудит",
    emoji="🔎",
    intro=_audit_intro,
    steps=[
        Step(
            key="who",
            text="Кто вы?",
            options=[
                ("studio", "Веб-студия / агентство"),
                ("product", "Продуктовая команда"),
                ("shop", "Интернет-магазин, школа, сервис"),
                ("other", "Другое"),
            ],
            label="Кто",
            note=_audit_who_note,
        ),
        _site_step(),
        Step(
            key="servers",
            text="Сколько серверов?",
            options=[("1", "1"), ("2-3", "2–3"), ("4-8", "4–8"), ("8+", "Больше 8"), ("?", "Не знаю")],
            label="Серверов",
        ),
        Step(
            key="hosting",
            text="Где работает проект?",
            options=[
                ("vps", "VPS / выделенный сервер"),
                ("cloud", "Облако"),
                ("shared", "Виртуальный хостинг"),
                ("?", "Не знаю"),
            ],
            label="Хостинг",
        ),
        Step(key="pain", text="Что беспокоит больше всего? Пара слов.", kind="text", skippable=True, label="Беспокоит"),
        _contact_step(),
    ],
    done=lambda a: (
        "Заявка у команды. Свяжемся в рабочее время: уточним детали, пришлём договор "
        "и соглашение о конфиденциальности. Доступы до подписания не просим."
    ),
)


# ---------- Техосмотр ----------

def _checkup_intro() -> str:
    p = product("checkup")
    return (
        f"<b>{p['name']}</b>\n"
        f"{p['term']} · {product_price('checkup')}.\n\n"
        "Проверим запасные копии, доступы, запас по нагрузке и незапертые двери. "
        "Результат — две страницы простым языком: что в порядке, что опасно, что сделать первым.\n\n"
        "Пара вопросов — и заявка у инженера."
    )


def _platform_note(a: Answers) -> str | None:
    if a.get("platform") == "builder":
        return (
            "На конструкторе сервером занимается сама платформа, поэтому техосмотр там почти ничего не даст. "
            "Оставьте заявку — инженер честно скажет, есть ли смысл."
        )
    return None


CHECKUP = Funnel(
    id="checkup",
    title="Техосмотр сайта",
    emoji="🩺",
    intro=_checkup_intro,
    steps=[
        _site_step("Адрес сайта?"),
        Step(
            key="platform",
            text="На чём сделан сайт?",
            options=[
                ("bitrix", "1С-Битрикс"),
                ("wordpress", "WordPress"),
                ("builder", "Tilda или другой конструктор"),
                ("other", "Другое / не знаю"),
            ],
            label="Платформа",
            note=_platform_note,
        ),
        Step(
            key="pain",
            text="Что беспокоит?",
            options=[
                ("down", "Сайт падает или тормозит"),
                ("backups", "Не уверен в копиях"),
                ("access", "Доступы у бывшего подрядчика"),
                ("check", "Просто хочу проверить"),
            ],
            label="Беспокоит",
        ),
        _contact_step(),
    ],
    done=lambda a: "Заявка у инженера. Свяжемся в рабочее время, расскажем, что понадобится для проверки.",
)


# ---------- Аварийная помощь ----------

def _em_intro() -> str:
    p = product("emergency")
    return (
        "<b>Сайт не открывается?</b>\n"
        "Ответьте на пару вопросов — заявка сразу уйдёт инженеру с пометкой «срочно».\n\n"
        f"Аварийная помощь: {product_price('emergency')}, {p['priceNote']}."
    )


def _em_done(a: Answers) -> str:
    return (
        "Заявка у инженера с пометкой «срочно». Держите телефон рядом.\n\n"
        "<b>Пока ждёте:</b>\n"
        "1. Откройте сайт с телефона через мобильный интернет — вдруг проблема в вашей сети.\n"
        "2. Проверьте в панели хостинга и регистратора, оплачены ли хостинг и домен.\n"
        "3. Ничего не удаляйте и не переустанавливайте — можно потерять заказы.\n"
        "4. Найдите доступы: панель хостинга, сервер, админка сайта. Присылать их сюда не нужно — "
        "инженер скажет, как передать безопасно."
    )


EMERGENCY = Funnel(
    id="emergency",
    title="Аварийная помощь",
    emoji="🔴",
    intro=_em_intro,
    urgent=True,
    remind_after_min=10,
    steps=[
        _site_step("Адрес сайта?"),
        Step(
            key="symptom",
            text="Что видите?",
            options=[
                ("down", "Не открывается"),
                ("5xx", "Ошибка 500 / 502 / 503"),
                ("slow", "Очень медленно"),
                ("other", "Другое"),
            ],
            label="Симптом",
        ),
        Step(
            key="access",
            text="Доступы к серверу или хостингу у вас есть?",
            options=[("yes", "Да"), ("no", "Нет"), ("?", "Не знаю")],
            label="Доступы",
        ),
        _contact_step(),
    ],
    done=_em_done,
)


# ---------- Сопровождение ----------

def _support_intro() -> str:
    b, z = plan("basic"), plan("business")
    return (
        "<b>Ежемесячное сопровождение</b>\n"
        f"«{b['name']}» — {rub(b['price'])}/мес: {b['scope'].lower()}.\n"
        f"«{z['name']}» — {rub(z['price'])}/мес: {z['scope'].lower()}, помощь с выпуском обновлений, "
        "реакция до 1 часа.\n\n"
        "Подберём тариф — несколько коротких вопросов."
    )


def _recommend(a: Answers) -> str:
    if a.get("plan") in ("basic", "business"):
        return a["plan"]
    big = a.get("servers") in ("4-8", "8+")
    ci = a.get("releases") == "yes"
    return "business" if (big or ci) else "basic"


def _support_done(a: Answers) -> str:
    p = plan(_recommend(a))
    fc = site()["firstClients"]
    text = (
        f"Судя по ответам, вам подойдёт «{p['name']}» — {rub(p['price'])}/мес. "
        "Инженер уточнит при разговоре.\n\n"
        "Обычно начинаем с аудита: за 5 дней разбираемся, что где стоит, — и его стоимость засчитываем в работы."
    )
    if a.get("offer") == "first":
        text += (
            f"\n\nПредложение первым {fc['slots']} клиентам — минус {fc['discount']}% на первые "
            f"{fc['months']} месяца в обмен на кейс и отзыв — отметили в заявке."
        )
    return text


SUPPORT = Funnel(
    id="support",
    title="Сопровождение",
    emoji="🛠",
    intro=_support_intro,
    steps=[
        Step(
            key="project",
            text="Что сопровождаем?",
            options=[
                ("site", "Сайт или интернет-магазин"),
                ("service", "Онлайн-сервис"),
                ("studio", "Несколько проектов студии"),
            ],
            label="Проект",
        ),
        _site_step(),
        Step(
            key="servers",
            text="Сколько серверов?",
            options=[("1", "1"), ("2-3", "2–3"), ("4-8", "4–8"), ("8+", "Больше 8"), ("?", "Не знаю")],
            label="Серверов",
        ),
        Step(
            key="releases",
            text="Нужна помощь с выпуском обновлений (CI/CD)?",
            options=[("yes", "Да"), ("no", "Нет"), ("?", "Не знаю")],
            label="Выпуск обновлений",
        ),
        _contact_step(),
    ],
    done=_support_done,
)


# ---------- Веб-студиям ----------

def _partners_intro() -> str:
    pr = site()["partners"]
    return (
        "<b>Партнёрство для веб-студий</b>\n"
        f"{pr['revenueShare']}% от платежей приведённого клиента за первые {pr['revenueShareMonths']} месяцев "
        f"или скидка {pr['whiteLabelDiscount']}% при работе под именем студии. "
        "Клиентов не переманиваем и разработку им не предлагаем.\n\n"
        "Несколько вопросов о студии."
    )


PARTNERS = Funnel(
    id="partners",
    title="Партнёрство (студия)",
    emoji="🤝",
    intro=_partners_intro,
    steps=[
        Step(
            key="projects",
            text="Сколько проектов у студии на поддержке?",
            options=[("1-5", "1–5"), ("6-20", "6–20"), ("20+", "Больше 20")],
            label="Проектов",
        ),
        Step(
            key="format",
            text="Какой формат интересен?",
            options=[
                ("share", "Рекомендация за процент"),
                ("whitelabel", "Под именем студии"),
                ("?", "Пока не знаю"),
            ],
            label="Формат",
        ),
        _site_step("Сайт студии?"),
        _contact_step(),
    ],
    done=lambda a: "Спасибо! Свяжемся, обсудим формат и предложим начать с одного проекта.",
)


# ---------- Проект «Порядок», выпуск обновлений, переезд ----------

def _project_intro() -> str:
    p = product("order")
    return (
        "<b>Наводим порядок в инфраструктуре</b>\n"
        f"Проект «Порядок»: {p['term']}, {product_price('order')}. Копии с проверкой восстановления, "
        "мониторинг, автоматический выпуск обновлений, документация. Переезд в российское облако — тоже сюда.\n\n"
        "Несколько вопросов о проекте."
    )


PROJECT = Funnel(
    id="project",
    title="Проект: порядок / CI/CD / переезд",
    emoji="🧱",
    intro=_project_intro,
    steps=[
        Step(
            key="need",
            text="Что нужно?",
            options=[
                ("order", "Навести порядок после аудита"),
                ("cicd", "Выпуск обновлений (CI/CD)"),
                ("migration", "Переезд в российское облако"),
                ("other", "Другое"),
            ],
            label="Задача",
        ),
        _site_step(),
        Step(
            key="team",
            text="Сколько разработчиков в команде?",
            options=[("0", "Нет своих"), ("1-4", "1–4"), ("5-30", "5–30"), ("30+", "Больше 30")],
            label="Разработчиков",
        ),
        Step(key="hosting", text="Где сейчас работает проект? Пара слов.", kind="text", skippable=True, label="Хостинг"),
        _contact_step(),
    ],
    done=lambda a: (
        f"Заявка у команды. Обычно начинаем с аудита ({product_price('audit')}, засчитывается в стоимость), "
        "чтобы оценить работы в часах, а не на глаз."
    ),
)


FUNNELS: dict[str, Funnel] = {f.id: f for f in (QUESTION, AUDIT, CHECKUP, EMERGENCY, SUPPORT, PARTNERS, PROJECT)}

# Метка (ключ из botTags в site.ts) → воронка
TAG_FUNNEL: dict[str, str] = {
    # вопросы
    "header": "question", "mobileMenu": "question", "heroQuestion": "question",
    "team": "question", "blog": "question", "notFound": "question", "formError": "question",
    # аудит
    "hero": "audit", "pricingAudit": "audit", "final": "audit",
    "auditPage": "audit", "auditPageBottom": "audit", "auditCardAudit": "audit",
    # техосмотр
    "heroCheckup": "checkup", "pricingCheckup": "checkup", "finalCheckup": "checkup",
    "auditPageCheckup": "checkup", "auditCardCheckup": "checkup",
    # авария
    "pricingEmergency": "emergency", "emergencyTop": "emergency",
    "emergencyAside": "emergency", "emergencyBottom": "emergency",
    # сопровождение
    "pricingBasic": "support", "pricingBusiness": "support", "pricingNightShift": "support",
    "firstClients": "support", "supportTop": "support", "supportBasic": "support",
    "supportBusiness": "support", "supportBottom": "support", "supportNight": "support",
    # студии
    "partners": "partners", "partnersBottom": "partners",
    # проекты
    "pricingOrder": "project", "devops": "project", "devopsBottom": "project",
    "migration": "project", "migrationBottom": "project",
}

# Метка → заранее известные ответы (вопрос пропускается)
TAG_PREFILL: dict[str, Answers] = {
    "pricingBasic": {"plan": "basic"},
    "supportBasic": {"plan": "basic"},
    "pricingBusiness": {"plan": "business"},
    "supportBusiness": {"plan": "business"},
    "pricingNightShift": {"night": "yes"},
    "supportNight": {"night": "yes"},
    "firstClients": {"offer": "first"},
    "pricingOrder": {"need": "order"},
    "devops": {"need": "cicd"},
    "devopsBottom": {"need": "cicd"},
    "migration": {"need": "migration"},
    "migrationBottom": {"need": "migration"},
}

# Метка → где стоит кнопка (для карточки в чате команды)
TAG_PLACE: dict[str, str] = {
    "header": "шапка сайта", "mobileMenu": "мобильное меню", "hero": "главная, первый экран",
    "heroQuestion": "главная, «Задать вопрос инженеру»", "heroCheckup": "главная, первый экран, техосмотр",
    "pricingCheckup": "главная, цены, техосмотр", "pricingAudit": "главная, цены, аудит",
    "pricingEmergency": "главная, цены, авария", "pricingOrder": "главная, цены, «Порядок»",
    "pricingBasic": "главная, тариф «Базовый»", "pricingBusiness": "главная, тариф «Бизнес»",
    "pricingNightShift": "главная, дежурная смена", "firstClients": "главная, скидка первым клиентам",
    "team": "главная, блок команды", "final": "главная, финальный блок",
    "finalCheckup": "главная, финальный блок, техосмотр", "auditPage": "/audit, верх",
    "auditPageCheckup": "/audit, верх, техосмотр", "auditPageBottom": "/audit, низ",
    "auditCardCheckup": "/audit, карточка техосмотра", "auditCardAudit": "/audit, карточка аудита",
    "supportTop": "/support, верх", "supportBasic": "/support, «Базовый»",
    "supportBusiness": "/support, «Бизнес»", "supportBottom": "/support, низ",
    "supportNight": "/support, дежурная смена", "emergencyTop": "/emergency, верх",
    "emergencyAside": "/emergency, карточка", "emergencyBottom": "/emergency, низ",
    "partners": "/partners, верх", "partnersBottom": "/partners, низ", "devops": "/devops, верх",
    "devopsBottom": "/devops, низ", "migration": "/migration, верх", "migrationBottom": "/migration, низ",
    "blog": "блог", "notFound": "страница 404", "formError": "ошибка отправки формы",
}

# Подписи для заранее заполненных ответов
PREFILL_LABELS = {
    "plan": ("Тариф", {"basic": "Базовый", "business": "Бизнес"}),
    "night": ("Дежурная смена", {"yes": "интересует"}),
    "offer": ("Предложение", {"first": "скидка первым клиентам"}),
}

MENU = [
    ("audit", "🔎 Аудит инфраструктуры"),
    ("checkup", "🩺 Техосмотр сайта"),
    ("emergency", "🔴 Упал сайт"),
    ("support", "🛠 Сопровождение"),
    ("project", "🧱 Порядок, CI/CD, переезд"),
    ("partners", "🤝 Я из веб-студии"),
    ("question", "💬 Просто вопрос"),
]


def resolve(start_param: str | None) -> tuple[Funnel | None, str | None, Answers]:
    """?start=… → (воронка, ключ метки, предзаполненные ответы)."""
    from .data import tag_key

    if not start_param:
        return None, None, {}
    key = tag_key(start_param)
    if key and key in TAG_FUNNEL:
        return FUNNELS[TAG_FUNNEL[key]], key, dict(TAG_PREFILL.get(key, {}))
    # неизвестная метка (например, из рассылки) — спросим, что нужно
    return None, None, {}


def next_step(f: Funnel, answers: Answers) -> Step | None:
    for s in f.steps:
        if s.key in answers:
            continue
        if s.when and not s.when(answers):
            continue
        return s
    return None


def step_index(f: Funnel, key: str) -> int:
    for i, s in enumerate(f.steps):
        if s.key == key:
            return i
    raise KeyError(key)

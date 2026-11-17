// Разметка schema.org (JSON-LD). Все цены и контакты — из src/data/site.ts
import { company, social, products, plans, team, isPlaceholder, type Product } from '../data/site';

export function organization() {
  const org: Record<string, unknown> = {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    '@id': `${company.url}/#org`,
    name: company.name,
    url: company.url,
    logo: `${company.url}/icon-512.png`,
    email: company.email,
    description:
      'Инженеры для сайтов и онлайн-сервисов без своего DevOps: аудит инфраструктуры, запасные копии, мониторинг, выпуск обновлений и сопровождение серверов.',
    address: {
      '@type': 'PostalAddress',
      addressLocality: company.city,
      addressRegion: company.region,
      addressCountry: 'RU',
    },
    areaServed: { '@type': 'Country', name: 'Россия' },
    sameAs: social.map((s) => s.url),
    employee: team
      .filter((m) => m.surname && !isPlaceholder(m.surname))
      .map((m) => ({ '@type': 'Person', name: `${m.name} ${m.surname}`, jobTitle: m.role })),
  };
  if (!isPlaceholder(company.phone)) org.telephone = company.phone;
  return org;
}

const provider = { '@id': `${company.url}/#org` };

export function productService(p: Product) {
  const offer: Record<string, unknown> = {
    '@type': 'Offer',
    priceCurrency: 'RUB',
    availability: 'https://schema.org/InStock',
    url: `${company.url}${(p.page ?? '/').split('#')[0]}`,
  };
  if (p.priceFrom || p.unit) {
    offer.priceSpecification = {
      '@type': 'UnitPriceSpecification',
      priceCurrency: 'RUB',
      ...(p.priceFrom ? { minPrice: p.price } : { price: p.price }),
      ...(p.unit ? { unitText: 'час', unitCode: 'HUR' } : {}),
    };
  } else {
    offer.price = p.price;
  }
  return {
    '@context': 'https://schema.org',
    '@type': 'Service',
    name: p.name,
    description: p.summary,
    provider,
    areaServed: { '@type': 'Country', name: 'Россия' },
    offers: offer,
  };
}

export function supportService() {
  return {
    '@context': 'https://schema.org',
    '@type': 'Service',
    name: 'Ежемесячное сопровождение серверов',
    serviceType: 'DevOps на аутсорс',
    description: 'Мониторинг, запасные копии с проверкой восстановления, часы инженера и помощь с выпуском обновлений.',
    provider,
    areaServed: { '@type': 'Country', name: 'Россия' },
    offers: plans.map((pl) => ({
      '@type': 'Offer',
      name: `Тариф «${pl.name}»`,
      priceCurrency: 'RUB',
      priceSpecification: {
        '@type': 'UnitPriceSpecification',
        price: pl.price,
        priceCurrency: 'RUB',
        unitText: 'месяц',
        unitCode: 'MON',
      },
    })),
  };
}

export function allServices() {
  return [...products.map(productService), supportService()];
}

const strip = (s: string) => s.replace(/\s*\[[^\]]+\]/g, '').trim();

export function faqPage(items: { q: string; a: string }[]) {
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: items.map((i) => ({
      '@type': 'Question',
      name: i.q,
      acceptedAnswer: { '@type': 'Answer', text: strip(i.a) },
    })),
  };
}

export function breadcrumbs(items: { name: string; path: string }[]) {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [{ name: 'Главная', path: '/' }, ...items].map((it, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: it.name,
      item: `${company.url}${it.path}`,
    })),
  };
}

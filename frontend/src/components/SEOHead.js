import React from 'react';
import { Helmet } from 'react-helmet-async';

const BASE_URL = 'https://nexify-automate.com';

const META = {
  de: {
    title: 'NeXifyAI — Intelligente KI-Agenten für Enterprise-Automatisierung | DACH',
    description: 'NeXifyAI entwickelt autonome KI-Agenten für DACH-Unternehmen. 400+ Integrationen, DSGVO-konform, Enterprise-Grade. Chat it. Automate it.',
    keywords: 'KI-Agenten, Enterprise Automatisierung, DACH, KI-Beratung, Prozessautomatisierung, GPT, LLM, SAP Integration, CRM Automatisierung'
  },
  nl: {
    title: 'NeXifyAI — Intelligente AI-Agenten voor Enterprise-Automatisering',
    description: 'NeXifyAI ontwikkelt autonome AI-agenten voor bedrijven. 400+ integraties, AVG-conform, enterprise-grade. Chat it. Automate it.',
    keywords: 'AI-agenten, Enterprise automatisering, AI-advies, procesautomatisering, GPT, LLM, SAP integratie, CRM automatisering'
  },
  en: {
    title: 'NeXifyAI — Intelligent AI Agents for Enterprise Automation',
    description: 'NeXifyAI builds autonomous AI agents for enterprise businesses. 400+ integrations, GDPR-compliant, enterprise-grade. Chat it. Automate it.',
    keywords: 'AI agents, enterprise automation, AI consulting, process automation, GPT, LLM, SAP integration, CRM automation'
  }
};

const LANG_MAP = { de: 'de-DE', nl: 'nl-NL', en: 'en-GB' };

export default function SEOHead({ lang = 'de', page = 'home' }) {
  const m = META[lang] || META.en;
  const langTag = LANG_MAP[lang] || 'en-GB';
  const canonical = `${BASE_URL}/${lang}`;

  const orgSchema = {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: 'NeXify Automate',
    alternateName: 'NeXifyAI',
    url: BASE_URL,
    logo: `${BASE_URL}/icon-mark.svg`,
    description: m.description,
    address: [
      { '@type': 'PostalAddress', streetAddress: 'Graaf van Loonstraat 1E', addressLocality: 'Venlo', postalCode: '5921 JA', addressCountry: 'NL' },
      { '@type': 'PostalAddress', streetAddress: 'Wallstraße 9', addressLocality: 'Nettetal-Kaldenkirchen', postalCode: '41334', addressCountry: 'DE' }
    ],
    contactPoint: { '@type': 'ContactPoint', telephone: '+31-6-133-188-56', contactType: 'sales', availableLanguage: ['German', 'Dutch', 'English'] },
    sameAs: []
  };

  const webSchema = {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: 'NeXifyAI',
    url: BASE_URL,
    potentialAction: { '@type': 'SearchAction', target: `${BASE_URL}/search?q={search_term_string}`, 'query-input': 'required name=search_term_string' }
  };

  const serviceSchema = {
    '@context': 'https://schema.org',
    '@type': 'Service',
    serviceType: 'AI Agent Development & Enterprise Automation',
    provider: { '@type': 'Organization', name: 'NeXify Automate' },
    areaServed: ['DE', 'AT', 'CH', 'NL', 'EU'],
    hasOfferCatalog: {
      '@type': 'OfferCatalog',
      name: 'AI Agent Packages',
      itemListElement: [
        { '@type': 'Offer', name: 'Starter', price: '1900', priceCurrency: 'EUR', description: '1 AI Agent, 5 Integrations' },
        { '@type': 'Offer', name: 'Growth', price: '4500', priceCurrency: 'EUR', description: '5 AI Agents, Unlimited Integrations' },
        { '@type': 'Offer', name: 'Enterprise', price: '0', priceCurrency: 'EUR', description: 'Custom, Unlimited Agents' }
      ]
    }
  };

  return (
    <Helmet>
      <html lang={langTag} />
      <title>{m.title}</title>
      <meta name="description" content={m.description} />
      <meta name="keywords" content={m.keywords} />
      <meta name="robots" content="index, follow, max-image-preview:large" />
      <link rel="canonical" href={canonical} />

      {/* hreflang */}
      <link rel="alternate" hrefLang="de" href={`${BASE_URL}/de`} />
      <link rel="alternate" hrefLang="nl" href={`${BASE_URL}/nl`} />
      <link rel="alternate" hrefLang="en" href={`${BASE_URL}/en`} />
      <link rel="alternate" hrefLang="x-default" href={`${BASE_URL}/en`} />

      {/* Open Graph */}
      <meta property="og:type" content="website" />
      <meta property="og:site_name" content="NeXifyAI" />
      <meta property="og:title" content={m.title} />
      <meta property="og:description" content={m.description} />
      <meta property="og:url" content={canonical} />
      <meta property="og:locale" content={langTag.replace('-', '_')} />
      <meta property="og:image" content={`${BASE_URL}/og-image.png`} />
      <meta property="og:image:width" content="1200" />
      <meta property="og:image:height" content="630" />

      {/* Twitter */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={m.title} />
      <meta name="twitter:description" content={m.description} />

      {/* JSON-LD Structured Data */}
      {page === 'home' && <script type="application/ld+json">{JSON.stringify(orgSchema)}</script>}
      {page === 'home' && <script type="application/ld+json">{JSON.stringify(webSchema)}</script>}
      {page === 'home' && <script type="application/ld+json">{JSON.stringify(serviceSchema)}</script>}
    </Helmet>
  );
}

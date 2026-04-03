import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import { useLanguage } from '../../i18n/LanguageContext';
import { INTEGRATION_CATEGORIES, getFeaturedDetail } from '../../data/integrations';
import { AnimSection, I, fadeUp, stagger, scaleIn, track } from '../shared';

const Integrations = ({ onBook, t }) => {
  const { lang } = useLanguage();
  const popularSlugs = ['salesforce', 'hubspot', 'sap', 'datev', 'slack', 'aws', 'shopify', 'openai', 'stripe'];
  const popularItems = popularSlugs.map(s => {
    const f = getFeaturedDetail(s);
    for (const cat of INTEGRATION_CATEGORIES) {
      const item = cat.items.find(i => i.slug === s);
      if (item) return { ...item, category: cat, featured: f };
    }
    return null;
  }).filter(Boolean);

  const l = {
    de: { popular: 'Beliebte Integrationen', allCats: 'Alle Kategorien', checkCta: 'Details ansehen', protocols: 'Unterstützte Protokolle', requestCta: 'Anbindung anfragen', exploreCta: 'Alle Integrationen erkunden', customTitle: 'Ihre Wunsch-Integration nicht dabei?', customDesc: 'Kein Problem — wir realisieren jede erdenkliche Systemanbindung. Sprechen Sie mit uns über Ihre Anforderungen.', customCta: 'Integration besprechen', totalLabel: 'Verfügbare Systemintegrationen', totalDesc: 'Über REST API, GraphQL, Webhooks, OAuth 2.0, SAML und gRPC — nahtlos integriert in Ihre bestehende Infrastruktur.' },
    nl: { popular: 'Populaire integraties', allCats: 'Alle categorieen', checkCta: 'Details bekijken', protocols: 'Ondersteunde protocollen', requestCta: 'Koppeling aanvragen', exploreCta: 'Alle integraties verkennen', customTitle: 'Uw gewenste integratie niet gevonden?', customDesc: 'Geen probleem — wij realiseren elke denkbare systeemkoppeling. Bespreek uw vereisten met ons.', customCta: 'Integratie bespreken', totalLabel: 'Beschikbare systeemintegraties', totalDesc: 'Via REST API, GraphQL, Webhooks, OAuth 2.0, SAML en gRPC — naadloos geintegreerd in uw bestaande infrastructuur.' },
    en: { popular: 'Popular Integrations', allCats: 'All Categories', checkCta: 'View details', protocols: 'Supported protocols', requestCta: 'Request integration', exploreCta: 'Explore all integrations', customTitle: 'Don\'t see your integration?', customDesc: 'No problem — we can build any system connection you need. Talk to us about your requirements.', customCta: 'Discuss integration', totalLabel: 'Available system integrations', totalDesc: 'Via REST API, GraphQL, Webhooks, OAuth 2.0, SAML, and gRPC — seamlessly integrated into your existing infrastructure.' },
  };
  const lb = l[lang] || l.de;

  return (
    <AnimSection id="integrationen" className="section bg-s1" aria-labelledby="integ-t" data-testid="integrations-section">
      <div className="container">
        <div className="integ-header-row">
          <motion.div className="integ-header-left" variants={fadeUp}>
            <span className="label">{t.integrations.label}</span>
            <h2 id="integ-t" style={{ marginTop: 8 }}>{t.integrations.title}</h2>
            <p className="section-subtitle" style={{ maxWidth: 520 }}>{t.integrations.subtitle}</p>
          </motion.div>
          <motion.div className="integ-header-right" variants={fadeUp}>
            <div className="integ-count-box">
              <div className="integ-count">400+</div>
              <div className="integ-count-label">{lb.totalLabel}</div>
            </div>
            <p className="integ-count-desc">{lb.totalDesc}</p>
            <div className="integ-badges">
              {['REST API','GraphQL','Webhooks','OAuth 2.0','SAML','gRPC'].map(b => (
                <span key={b} className="integ-badge">{b}</span>
              ))}
            </div>
          </motion.div>
        </div>

        <motion.div className="integ-popular" variants={stagger}>
          <h3 className="integ-section-label"><I n="star" c="integ-section-label-icon" /> {lb.popular}</h3>
          <div className="integ-popular-grid" data-testid="integrations-popular">
            {popularItems.map((item) => (
              <motion.div key={item.slug} variants={scaleIn} whileHover={{ y: -6, transition: { duration: 0.25 } }}>
                <Link to={`/integrationen/${item.slug}`} className="integ-popular-card" data-testid={`integ-popular-${item.slug}`}>
                  <div className="integ-popular-icon" style={{ borderColor: item.featured?.color ? `${item.featured.color}25` : 'rgba(255,155,122,0.12)' }}>
                    <I n={item.featured?.logo || item.category.icon} />
                  </div>
                  <div className="integ-popular-info">
                    <div className="integ-popular-name">{item.name}</div>
                    <div className="integ-popular-cat">{item.category.name[lang] || item.category.name.de}</div>
                  </div>
                  <I n="arrow_forward" c="integ-popular-arrow" />
                </Link>
              </motion.div>
            ))}
          </div>
        </motion.div>

        <motion.div className="integ-all-cats" variants={stagger}>
          <h3 className="integ-section-label"><I n="category" c="integ-section-label-icon" /> {lb.allCats}</h3>
          <div className="integ-cats-grid" data-testid="integrations-categories">
            {INTEGRATION_CATEGORIES.map((cat, ci) => (
              <motion.div key={cat.key} className="integ-cat-card" variants={fadeUp} whileHover={{ borderColor: 'rgba(255,155,122,0.15)' }}>
                <div className="integ-cat-header">
                  <div className="integ-cat-icon-wrap"><I n={cat.icon} c="integ-cat-icon" /></div>
                  <div>
                    <div className="integ-cat-name-v2">{cat.name[lang] || cat.name.de}</div>
                    <div className="integ-cat-count">{cat.items.length} {lang === 'en' ? 'integrations' : lang === 'nl' ? 'integraties' : 'Integrationen'}</div>
                  </div>
                </div>
                <p className="integ-cat-desc">{cat.desc[lang] || cat.desc.de}</p>
                <div className="integ-cat-items-v2">
                  {cat.items.map((item) => {
                    const hasFeatured = getFeaturedDetail(item.slug);
                    return hasFeatured ? (
                      <Link key={item.slug} to={`/integrationen/${item.slug}`} className={`integ-item-v2 ${item.popular ? 'popular' : ''}`} data-testid={`integ-item-${item.slug}`}>
                        {item.name}
                        {item.popular && <span className="integ-item-dot"></span>}
                      </Link>
                    ) : (
                      <span key={item.slug} className="integ-item-v2" data-testid={`integ-item-${item.slug}`}>
                        {item.name}
                      </span>
                    );
                  })}
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        <motion.div className="integ-custom-cta" variants={fadeUp}>
          <div className="integ-custom-inner">
            <div>
              <h3>{lb.customTitle}</h3>
              <p>{lb.customDesc}</p>
            </div>
            <button className="btn btn-primary btn-glow" onClick={() => { onBook(); track('cta_click', { loc: 'integrations_custom' }); }} data-testid="integ-custom-cta-btn">
              {lb.customCta} <I n="arrow_forward" />
            </button>
          </div>
        </motion.div>
      </div>
    </AnimSection>
  );
};

export default Integrations;

import React from 'react';
import { motion } from 'framer-motion';
import { useLanguage } from '../../i18n/LanguageContext';
import { FULL_SERVICES, BUNDLES } from '../../data/products';
import { API, AnimSection, I, fadeUp, stagger, scaleIn, track } from '../shared';

const ServicesAll = ({ onBook }) => {
  const { lang } = useLanguage();
  const cats = FULL_SERVICES.categories[lang] || FULL_SERVICES.categories.de;
  const bundleItems = BUNDLES.items[lang] || BUNDLES.items.de;
  return (
    <AnimSection id="services" className="section bg-dark" data-testid="services-section">
      <div className="container">
        <motion.header className="section-header centered" variants={fadeUp}>
          <span className="label">{FULL_SERVICES.title[lang] || FULL_SERVICES.title.de}</span>
          <h2>{lang === 'en' ? 'Websites, Apps, SEO & AI Solutions' : lang === 'nl' ? 'Websites, Apps, SEO & AI-oplossingen' : 'Websites, Apps, SEO & KI-Lösungen'}</h2>
          <p className="section-subtitle">{FULL_SERVICES.subtitle[lang] || FULL_SERVICES.subtitle.de}</p>
        </motion.header>
        <div className="services-cat-grid" data-testid="services-categories">
          {cats.map((group, gi) => (
            <motion.div key={gi} className="svc-group" variants={fadeUp}>
              <h3 className="svc-group-title"><I n={group.icon} c="svc-group-icon" /> {group.name}</h3>
              <div className="svc-items">
                {group.items.map((s, si) => (
                  <div key={si} className={`svc-card ${s.hl ? 'hl' : ''}`} data-testid={`svc-${s.name.toLowerCase().replace(/\s/g,'-')}`}>
                    <div className="svc-card-top">
                      <div className="svc-name">{s.name}</div>
                      <div className="svc-price">{s.price}</div>
                    </div>
                    <div className="svc-desc">{s.desc}</div>
                    {s.time && <div className="svc-time"><I n="schedule" /> {s.time}</div>}
                    <ul className="svc-features">
                      {s.features.map((f, fi) => <li key={fi}><I n="check" c="svc-check" />{f}</li>)}
                    </ul>
                    <button className={`btn ${s.hl ? 'btn-primary' : 'btn-secondary'} svc-cta`} onClick={() => { onBook(); track('service_click', { service: s.name }); }}>{lang === 'en' ? 'Request quote' : lang === 'nl' ? 'Offerte aanvragen' : 'Angebot anfordern'}</button>
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>
        <motion.div className="bundles-wrap" variants={fadeUp} data-testid="bundles-section">
          <div className="section-header centered" style={{ marginTop: 72, marginBottom: 36 }}>
            <span className="label">{BUNDLES.title[lang] || BUNDLES.title.de}</span>
            <h2>{BUNDLES.subtitle[lang] || BUNDLES.subtitle.de}</h2>
          </div>
          <div className="bundles-grid">
            {bundleItems.map((b, i) => (
              <motion.div key={i} className={`bundle-card ${b.hl ? 'hl' : ''}`} variants={scaleIn} whileHover={{ y: -6 }}>
                {b.badge && <span className="price-badge">{b.badge}</span>}
                <div className="bundle-name">{b.name}</div>
                <div className="bundle-price">{b.price}</div>
                {b.saving && <div className="bundle-saving">{b.saving}</div>}
                <div className="bundle-desc">{b.desc}</div>
                <ul className="bundle-features">
                  {b.features.map((f, fi) => <li key={fi}><I n="check_circle" c="price-check" />{f}</li>)}
                </ul>
                <button className={`btn ${b.hl ? 'btn-primary btn-glow' : 'btn-secondary'} price-cta`} onClick={() => { onBook(); track('bundle_click', { bundle: b.name }); }} data-testid={`bundle-cta-${b.id}`}>{b.cta}</button>
              </motion.div>
            ))}
          </div>
        </motion.div>
        <motion.div className="tariff-download-bar" variants={fadeUp}>
          <div className="tariff-download-inner">
            <div>
              <h4>{lang === 'en' ? 'Complete tariff overview as PDF' : lang === 'nl' ? 'Volledig tariefoverzicht als PDF' : 'Komplette Tarifübersicht als PDF'}</h4>
              <p>{lang === 'en' ? 'All products, prices, features and bundles — printable, shareable, clear.' : lang === 'nl' ? 'Alle producten, prijzen, features en bundels — printbaar, deelbaar, overzichtelijk.' : 'Alle Produkte, Preise, Features und Bundles — druckbar, teilbar, übersichtlich.'}</p>
            </div>
            <a href={`${API}/api/product/tariff-sheet?category=all`} className="btn btn-secondary" target="_blank" rel="noopener noreferrer" data-testid="tariff-pdf-download">
              <I n="picture_as_pdf" /> {lang === 'en' ? 'Download PDF' : 'PDF herunterladen'}
            </a>
          </div>
        </motion.div>
      </div>
    </AnimSection>
  );
};

export default ServicesAll;

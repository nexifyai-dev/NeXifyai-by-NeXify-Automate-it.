import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLanguage } from '../../i18n/LanguageContext';
import { SEO_PRODUCT } from '../../data/products';
import { AnimSection, I, fadeUp, scaleIn, track } from '../shared';

const SEOProductSection = ({ onChat }) => {
  const { lang } = useLanguage();
  const [faqOpen, setFaqOpen] = useState(0);
  const d = SEO_PRODUCT;
  const benefits = d.benefits[lang] || d.benefits.de;
  const process = d.process[lang] || d.process.de;
  const tiers = d.tiers[lang] || d.tiers.de;
  const faq = d.faq[lang] || d.faq.de;
  return (
    <AnimSection id="ki-seo" className="section bg-s1" data-testid="seo-product-section">
      <div className="container">
        <motion.header className="section-header centered" variants={fadeUp}>
          <span className="label">{d.title[lang] || d.title.de}</span>
          <h2>{d.subtitle[lang] || d.subtitle.de}</h2>
          <p className="section-subtitle">{d.desc[lang] || d.desc.de}</p>
          <p className="seo-forwhom"><I n="groups" c="seo-forwhom-icon" /> {d.forWhom[lang] || d.forWhom.de}</p>
        </motion.header>
        <div className="seo-benefits-grid" data-testid="seo-benefits">
          {benefits.map((b, i) => (
            <motion.div key={i} className="seo-benefit-card" variants={fadeUp} whileHover={{ y: -4 }}>
              <I n={b.icon} c="seo-benefit-icon" />
              <h3>{b.title}</h3>
              <p>{b.desc}</p>
            </motion.div>
          ))}
        </div>
        <motion.h3 className="seo-sub-title" variants={fadeUp}>
          <I n="route" c="seo-sub-icon" /> {lang === 'en' ? 'How it works' : lang === 'nl' ? 'Hoe het werkt' : 'So funktioniert es'}
        </motion.h3>
        <div className="seo-process-grid">
          {process.map((s, i) => (
            <motion.div key={i} className="seo-process-card" variants={fadeUp}>
              <div className="seo-process-num">{s.num}</div>
              <h4>{s.title}</h4>
              <p>{s.desc}</p>
            </motion.div>
          ))}
        </div>
        <motion.h3 className="seo-sub-title" variants={fadeUp}>
          <I n="payments" c="seo-sub-icon" /> {lang === 'en' ? 'SEO Pricing' : lang === 'nl' ? 'SEO Tarieven' : 'SEO Tarife'}
        </motion.h3>
        <div className="pricing-grid" data-testid="seo-pricing">
          {tiers.map((pl, i) => (
            <motion.div key={i} className={`price-card ${pl.hl ? 'hl' : ''}`} variants={scaleIn} whileHover={{ y: -8, transition: { duration: 0.25 } }}>
              {pl.badge && <span className="price-badge">{pl.badge}</span>}
              <div className="price-name">{pl.name}</div>
              <div className="price-val">{pl.price}<span className="price-period"> {pl.period}</span></div>
              <ul className="price-features">{pl.features.map((f, fi) => <li key={fi} className="price-feat"><I n="check_circle" c="price-check" />{f}</li>)}</ul>
              {pl.time && <div className="seo-tier-time"><I n="schedule" /> {pl.time}</div>}
              <button className={`btn ${pl.hl ? 'btn-primary btn-glow' : 'btn-secondary'} price-cta`} onClick={() => { onChat(lang === 'en' ? `I'm interested in ${pl.name}` : lang === 'nl' ? `Ik ben geïnteresseerd in ${pl.name}` : `Ich interessiere mich für ${pl.name}`); track('seo_pricing_click', { plan: pl.name }); }} data-testid={`seo-price-cta-${pl.id}`}>{lang === 'en' ? 'Request quote' : lang === 'nl' ? 'Offerte aanvragen' : 'Angebot anfordern'}</button>
            </motion.div>
          ))}
        </div>
        <motion.h3 className="seo-sub-title" style={{ marginTop: 56 }} variants={fadeUp}>
          <I n="help" c="seo-sub-icon" /> FAQ
        </motion.h3>
        <div className="faq-list seo-faq" data-testid="seo-faq">
          {faq.map((f, i) => (
            <motion.div key={i} className={`faq-item ${faqOpen === i ? 'open' : ''}`} variants={fadeUp}>
              <button type="button" className="faq-q" onClick={() => setFaqOpen(faqOpen === i ? -1 : i)} data-testid={`seo-faq-q-${i}`}><span>{f.q}</span><I n={faqOpen === i ? 'expand_less' : 'expand_more'} /></button>
              <AnimatePresence>
                {faqOpen === i && (
                  <motion.div className="faq-a" initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.3 }}>
                    <div className="faq-a-inner">{f.a}</div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>
      </div>
    </AnimSection>
  );
};

export default SEOProductSection;

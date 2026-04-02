import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { motion, useInView, AnimatePresence } from 'framer-motion';
import { HeroScene, IntegrationsGlobe, ProcessScene } from './components/Scene3D';
import { useLanguage } from './i18n/LanguageContext';
import T from './i18n/translations';
import LanguageSwitcher from './components/LanguageSwitcher';
import SEOHead from './components/SEOHead';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './App.css';

const API = process.env.REACT_APP_BACKEND_URL || '';

const COMPANY = {
  name: 'NeXifyAI by NeXify', tagline: 'Chat it. Automate it.', legal: 'NeXify Automate',
  ceo: 'Pascal Courbois, Geschäftsführer',
  addr: { de: { s: 'Wallstraße 9', c: '41334 Nettetal-Kaldenkirchen', co: 'Deutschland' }, nl: { s: 'Graaf van Loonstraat 1E', c: '5921 JA Venlo', co: 'Niederlande' } },
  phone: '+31 6 133 188 56', email: 'support@nexify-automate.com', web: 'nexify-automate.com', kvk: '90483944', vat: 'NL865786276B01'
};

const LEGAL_PATHS = {
  de: { impressum: '/de/impressum', datenschutz: '/de/datenschutz', agb: '/de/agb', ki: '/de/ki-hinweise' },
  nl: { impressum: '/nl/impressum', datenschutz: '/nl/privacybeleid', agb: '/nl/voorwaarden', ki: '/nl/ai-informatie' },
  en: { impressum: '/en/imprint', datenschutz: '/en/privacy', agb: '/en/terms', ki: '/en/ai-transparency' }
};

const LOCALE_MAP = { de: 'de-DE', nl: 'nl-NL', en: 'en-GB' };

const genSid = () => `s_${Date.now()}_${Math.random().toString(36).substr(2, 8)}`;

const track = async (ev, props = {}) => {
  try {
    const sid = sessionStorage.getItem('nx_s') || genSid();
    sessionStorage.setItem('nx_s', sid);
    await fetch(`${API}/api/analytics/track`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ event: ev, properties: { ...props, ts: new Date().toISOString() }, session_id: sid }) });
  } catch (_) {}
};

const I = ({ n, c = '' }) => <span className={`material-symbols-outlined ${c}`} aria-hidden="true">{n}</span>;

/* ═══════════ ANIMATION VARIANTS ═══════════ */
const fadeUp = { hidden: { opacity: 0, y: 40 }, visible: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.25, 0.4, 0, 1] } } };
const fadeIn = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { duration: 0.6 } } };
const stagger = { visible: { transition: { staggerChildren: 0.1 } } };
const scaleIn = { hidden: { opacity: 0, scale: 0.9 }, visible: { opacity: 1, scale: 1, transition: { duration: 0.5, ease: [0.25, 0.4, 0, 1] } } };

function AnimSection({ children, className = '', id, ...props }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-80px' });
  return (
    <motion.section ref={ref} id={id} className={className} initial="hidden" animate={isInView ? 'visible' : 'hidden'} variants={stagger} {...props}>
      {children}
    </motion.section>
  );
}

/* ═══════════ LOGO ═══════════ */
const Logo = ({ size = 'md' }) => {
  const s = size === 'sm' ? 24 : size === 'lg' ? 40 : 32;
  const fs = size === 'sm' ? '.9375rem' : size === 'lg' ? '1.375rem' : '1.125rem';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: size === 'sm' ? 8 : 10 }}>
      <img src="/icon-mark.svg" alt="" width={s} height={s} style={{ display: 'block' }} />
      <span style={{ fontFamily: 'var(--f-display)', fontWeight: 800, fontSize: fs, color: '#fff', letterSpacing: '-.02em' }}>
        NeXify<span style={{ color: 'var(--nx-accent)' }}>AI</span>
      </span>
    </div>
  );
};

/* ═══════════ NAVIGATION ═══════════ */
const Nav = ({ onBook, t }) => {
  const [mob, setMob] = useState(false);
  const [sc, setSc] = useState(false);
  useEffect(() => { const h = () => setSc(window.scrollY > 50); window.addEventListener('scroll', h, { passive: true }); return () => window.removeEventListener('scroll', h); }, []);
  const links = [
    { l: t.nav.leistungen, h: '#loesungen' }, { l: t.nav.usecases, h: '#use-cases' },
    { l: t.nav.appdev, h: '#app-dev' }, { l: t.nav.integrationen, h: '#integrationen' },
    { l: t.nav.tarife, h: '#preise' }, { l: t.nav.faq, h: '#faq' }
  ];
  const go = (h) => { setMob(false); track('nav_click', { target: h }); };
  return (
    <nav className={`nav ${sc ? 'scrolled' : ''}`} role="navigation" data-testid="main-nav">
      <div className="container nav-inner">
        <a href="#hero" className="nav-logo" onClick={() => track('logo_click')} data-testid="nav-logo"><Logo /></a>
        <div className="nav-links" role="menubar">
          {links.map(l => <a key={l.h} href={l.h} className="nav-link" role="menuitem" onClick={() => go(l.h)}>{l.l}</a>)}
        </div>
        <div className="nav-actions">
          <LanguageSwitcher />
          <button className="btn btn-primary nav-cta" onClick={() => { onBook(); track('cta_click', { loc: 'nav' }); }} data-testid="nav-book-btn">{t.nav.cta}</button>
          <button className="nav-toggle" onClick={() => setMob(!mob)} aria-label={mob ? t.nav.menuClose : t.nav.menuOpen} aria-expanded={mob} data-testid="nav-toggle"><I n={mob ? 'close' : 'menu'} /></button>
        </div>
        <AnimatePresence>
          {mob && (
            <motion.div className="nav-mobile" role="menu" data-testid="nav-mobile-menu" initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }}>
              {links.map(l => <a key={l.h} href={l.h} role="menuitem" onClick={() => go(l.h)}>{l.l}</a>)}
              <LanguageSwitcher mobile />
              <button className="btn btn-primary nav-mobile-cta" onClick={() => { setMob(false); onBook(); }}>{t.nav.cta}</button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </nav>
  );
};

/* ═══════════ HERO ═══════════ */
const Hero = ({ onBook, t }) => {
  useEffect(() => { track('page_view', { section: 'hero' }); }, []);
  return (
    <section id="hero" className="hero" aria-labelledby="hero-t" data-testid="hero-section">
      <HeroScene />
      <div className="container hero-container">
        <div className="hero-inner">
          <motion.div className="hero-content" initial={{ opacity: 0, y: 50 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 1, ease: [0.25, 0.4, 0, 1] }}>
            <motion.span className="label hero-label" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }}>{t.hero.label}</motion.span>
            <h1 id="hero-t">{t.hero.h1[0]} <span className="text-accent">{t.hero.h1[1]}</span><br />{t.hero.h1[2]}</h1>
            <p className="hero-desc">{t.hero.desc}</p>
            <motion.div className="hero-actions" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }}>
              <button className="btn btn-primary btn-lg btn-glow" onClick={() => { onBook(); track('cta_click', { loc: 'hero' }); }} data-testid="hero-book-btn">{t.hero.cta1} <I n="arrow_forward" /></button>
              <a href="#loesungen" className="btn btn-secondary btn-lg" onClick={() => track('cta_click', { loc: 'hero', t: 'explore' })}>{t.nav.leistungen}</a>
            </motion.div>
            <motion.div className="hero-stats" data-testid="hero-stats" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.9 }}>
              {t.hero.stats.map((s, i) => (
                <div key={i} className="hero-stat"><div className="hero-stat-title">{s.title}</div><div className="hero-stat-value">{s.value}</div></div>
              ))}
            </motion.div>
          </motion.div>
        </div>
      </div>
    </section>
  );
};

/* ═══════════ SOLUTIONS ═══════════ */
const Solutions = ({ t }) => (
  <AnimSection id="loesungen" className="section bg-s1" aria-labelledby="sol-t" data-testid="solutions-section">
    <div className="container">
      <motion.header className="section-header" variants={fadeUp}>
        <span className="label">{t.solutions.label}</span>
        <h2 id="sol-t">{t.solutions.title}</h2>
        <p className="section-subtitle">{t.solutions.subtitle}</p>
      </motion.header>
      <div className="solutions-grid" role="list">
        {t.solutions.items.map((s, i) => (
          <motion.article key={i} className="sol-card" role="listitem" variants={scaleIn} whileHover={{ y: -6, transition: { duration: 0.25 } }}>
            <div className="sol-icon-wrap"><I n={s.icon} c="sol-icon" /></div>
            <h3 className="sol-title">{s.title}</h3>
            <p className="sol-desc">{s.desc}</p>
            <div className="sol-bar"></div>
          </motion.article>
        ))}
      </div>
    </div>
  </AnimSection>
);

/* ═══════════ USE CASES ═══════════ */
const UseCases = ({ t }) => (
  <AnimSection id="use-cases" className="section bg-dark" aria-labelledby="uc-t" data-testid="usecases-section">
    <div className="container">
      <motion.header className="section-header" variants={fadeUp}>
        <span className="label">{t.usecases.label}</span>
        <h2 id="uc-t">{t.usecases.title}</h2>
        <p className="section-subtitle">{t.usecases.subtitle}</p>
      </motion.header>
      <div className="uc-grid">
        {t.usecases.items.map((item, i) => {
          if (item.size === 'lg') return (
            <motion.article key={i} className="uc-card uc-lg" variants={fadeUp} whileHover={{ borderColor: 'rgba(255,155,122,0.3)' }}>
              <div className="uc-bg-icon"><I n={item.icon} /></div>
              <div className="uc-content"><span className="label">{t.usecases.label}</span><h3 className="uc-title">{item.title}</h3><p className="uc-desc">{item.desc}</p></div>
            </motion.article>
          );
          if (item.size === 'wd') return (
            <motion.article key={i} className="uc-card uc-wd" variants={fadeUp}>
              <div className="uc-split">
                <div><h3 className="uc-title">{item.title}</h3><p className="uc-desc">{item.desc}</p></div>
                <div className="orch-visual">
                  <div className="orch-hub">
                    <div className="orch-core"><I n={t.usecases.orchIcon} /></div>
                    <div className="orch-ring orch-ring-1"></div>
                    <div className="orch-ring orch-ring-2"></div>
                    <div className="orch-ring orch-ring-3"></div>
                    <div className="orch-node orch-node-1"><span>{t.usecases.orchLabels[0]}</span></div>
                    <div className="orch-node orch-node-2"><span>{t.usecases.orchLabels[1]}</span></div>
                    <div className="orch-node orch-node-3"><span>API</span></div>
                    <div className="orch-node orch-node-4"><span>KI</span></div>
                    <div className="orch-pulse orch-pulse-1"></div>
                    <div className="orch-pulse orch-pulse-2"></div>
                    <div className="orch-pulse orch-pulse-3"></div>
                  </div>
                </div>
              </div>
            </motion.article>
          );
          return (
            <motion.article key={i} className="uc-card uc-sm" variants={scaleIn} whileHover={{ y: -4 }}>
              <I n={item.icon} c="uc-icon" /><h3 className="uc-title">{item.title}</h3><p className="uc-desc">{item.desc}</p>
            </motion.article>
          );
        })}
      </div>
    </div>
  </AnimSection>
);

/* ═══════════ APP DEVELOPMENT ═══════════ */
const AppDev = ({ onBook, t }) => (
  <AnimSection id="app-dev" className="section bg-s2" aria-labelledby="appdev-t" data-testid="appdev-section">
    <div className="container">
      <motion.header className="section-header" variants={fadeUp}>
        <span className="label">{t.appdev.label}</span>
        <h2 id="appdev-t">{t.appdev.title}</h2>
        <p className="section-subtitle">{t.appdev.subtitle}</p>
      </motion.header>
      <div className="appdev-grid">
        {t.appdev.items.map((s, i) => (
          <motion.div key={i} className="appdev-card" variants={scaleIn} whileHover={{ y: -6, borderColor: 'rgba(255,155,122,0.25)' }}>
            <div className="appdev-icon-wrap"><I n={s.icon} c="appdev-icon" /></div>
            <h3 className="appdev-title">{s.title}</h3>
            <p className="appdev-desc">{s.desc}</p>
          </motion.div>
        ))}
        <motion.div className="appdev-highlight" variants={fadeUp}>
          <h3>{t.appdev.highlight.title}</h3>
          <p className="appdev-desc">{t.appdev.highlight.desc}</p>
          <div className="appdev-highlight-inner">
            {t.appdev.highlight.metrics.map((m, i) => (
              <div key={i} className="appdev-metric"><div className="appdev-metric-val">{m.val}</div><div className="appdev-metric-label">{m.label}</div></div>
            ))}
          </div>
          <button className="btn btn-primary btn-glow" onClick={() => { onBook(); track('cta_click', { loc: 'appdev' }); }} data-testid="appdev-book-btn">{t.hero.cta1} <I n="arrow_forward" /></button>
        </motion.div>
      </div>
    </div>
  </AnimSection>
);

/* ═══════════ PROCESS ═══════════ */
const Process = ({ t }) => (
  <AnimSection id="prozess" className="section bg-dark bg-grid" aria-labelledby="proc-t" data-testid="process-section">
    <div className="container">
      <motion.header className="section-header centered" variants={fadeUp}>
        <span className="label">{t.process.label}</span>
        <h2 id="proc-t">{t.process.title}</h2>
      </motion.header>
      <ProcessScene />
      <div className="process-grid" role="list">
        {t.process.steps.map((s, i) => (
          <motion.article key={i} className="proc-step" role="listitem" variants={fadeUp} whileHover={{ y: -4 }}>
            <div className="proc-num">{s.num}</div>
            <h3 className="proc-title">{s.title}</h3>
            <p className="proc-desc">{s.desc}</p>
            <div className="proc-bars">{[1,2,3,4].map(n => <div key={n} className={`proc-bar ${n <= s.bars ? 'on' : ''}`}></div>)}</div>
          </motion.article>
        ))}
      </div>
    </div>
  </AnimSection>
);

/* ═══════════ INTEGRATIONS (400+) ═══════════ */
const Integrations = ({ t }) => (
  <AnimSection id="integrationen" className="section bg-s1" aria-labelledby="integ-t" data-testid="integrations-section">
    <div className="container">
      <div className="integ-layout">
        <div className="integ-left">
          <motion.div variants={fadeUp}>
            <span className="label">{t.integrations.label}</span>
            <h2 id="integ-t" style={{ marginTop: 8 }}>{t.integrations.title}</h2>
            <p className="section-subtitle">{t.integrations.subtitle}</p>
          </motion.div>
          <motion.div className="integ-counter" variants={fadeUp}>
            <div className="integ-count">{t.integrations.counter}</div>
            <div className="integ-count-label">{t.integrations.counterLabel}</div>
            <div className="integ-badges" style={{ marginTop: 12 }}>
              {t.integrations.badges.map(b => <span key={b} className="integ-badge">{b}</span>)}
            </div>
          </motion.div>
          <IntegrationsGlobe />
          <motion.p variants={fadeUp} style={{ fontSize: '.8125rem', color: 'var(--nx-accent)', marginTop: 16, fontWeight: 600 }}>{t.integrations.customNote}</motion.p>
        </div>
        <motion.div className="integ-cats" data-testid="integrations-list" variants={stagger}>
          {t.integrations.cats.map((cat, ci) => (
            <motion.div key={ci} variants={fadeUp}>
              <div className="integ-cat-name">{cat.name}</div>
              <div className="integ-cat-items">{cat.items.map((item, ii) => <span key={ii} className="integ-item">{item}</span>)}</div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </div>
  </AnimSection>
);

/* ═══════════ GOVERNANCE ═══════════ */
const Governance = ({ t }) => (
  <AnimSection className="section bg-s2" style={{ borderTop: '1px solid var(--nx-border)', borderBottom: '1px solid var(--nx-border)' }} aria-labelledby="gov-t" data-testid="governance-section">
    <div className="container">
      <div className="gov-grid">
        <motion.div variants={fadeUp}>
          <span className="label">{t.governance.label}</span>
          <h2 id="gov-t">{t.governance.title}</h2>
          <div className="gov-list">
            {t.governance.items.map((f, i) => (
              <motion.div key={i} className="gov-item" variants={fadeUp} whileHover={{ x: 4 }}>
                <div className="gov-icon-box"><I n={f.icon} /></div>
                <div><h3 className="gov-item-title">{f.title}</h3><p className="gov-item-desc">{f.desc}</p></div>
              </motion.div>
            ))}
          </div>
        </motion.div>
        <motion.div className="cert-grid" variants={stagger}>
          {t.governance.certs.map((c, i) => (
            <motion.div key={i} className={`cert-card ${c.hl ? 'hl' : ''}`} variants={scaleIn} whileHover={{ scale: 1.03 }}>
              <span className="cert-label">{c.label}</span><div className="cert-title">{c.title}</div><p className="cert-desc">{c.desc}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </div>
  </AnimSection>
);

/* ═══════════ PRICING ═══════════ */
const Pricing = ({ onBook, t }) => (
  <AnimSection id="preise" className="section bg-dark" aria-labelledby="price-t" data-testid="pricing-section">
    <div className="container">
      <motion.header className="section-header centered" variants={fadeUp}>
        <span className="label">{t.pricing.label}</span>
        <h2 id="price-t">{t.pricing.title}</h2>
        <p className="section-subtitle">{t.pricing.subtitle}</p>
      </motion.header>
      <div className="pricing-grid" role="list">
        {t.pricing.plans.map((pl, i) => (
          <motion.article key={i} className={`price-card ${pl.hl ? 'hl' : ''}`} role="listitem" variants={scaleIn} whileHover={{ y: -8, transition: { duration: 0.25 } }}>
            {pl.badge && <span className="price-badge">{pl.badge}</span>}
            <div className="price-name">{pl.name}</div>
            <div className="price-val">{pl.price}<span className="price-period"> {pl.period}</span></div>
            <ul className="price-features">{pl.features.map((f, fi) => <li key={fi} className="price-feat"><I n="check_circle" c="price-check" />{f}</li>)}</ul>
            <button className={`btn ${pl.hl ? 'btn-primary btn-glow' : 'btn-secondary'} price-cta`} onClick={() => { onBook(); track('pricing_click', { plan: pl.name }); }} data-testid={`price-cta-${pl.name.toLowerCase()}`}>{pl.cta}</button>
          </motion.article>
        ))}
      </div>
    </div>
  </AnimSection>
);

/* ═══════════ FAQ ═══════════ */
const FAQ = ({ t }) => {
  const [open, setOpen] = useState(0);
  return (
    <AnimSection id="faq" className="section bg-s1" aria-labelledby="faq-t" data-testid="faq-section">
      <div className="container">
        <div className="faq-layout">
          <motion.div variants={fadeUp}>
            <span className="label">{t.faq.label}</span>
            <h2 id="faq-t">{t.faq.title}</h2>
            <p className="section-subtitle">{t.faq.subtitle}</p>
          </motion.div>
          <div className="faq-list" role="list">
            {t.faq.items.map((f, i) => (
              <motion.div key={i} className={`faq-item ${open === i ? 'open' : ''}`} role="listitem" variants={fadeUp}>
                <button type="button" className="faq-q" onClick={() => setOpen(open === i ? -1 : i)} aria-expanded={open === i} data-testid={`faq-q-${i}`}><span>{f.q}</span><I n={open === i ? 'expand_less' : 'expand_more'} /></button>
                <AnimatePresence>
                  {open === i && (
                    <motion.div className="faq-a" data-testid={`faq-a-${i}`} initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.3 }}>
                      <div className="faq-a-inner">{f.a}</div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </AnimSection>
  );
};

/* ═══════════ CONTACT ═══════════ */
const Contact = ({ onBook, t }) => {
  const [form, setForm] = useState({ vorname: '', nachname: '', email: '', telefon: '', unternehmen: '', nachricht: '', _hp: '' });
  const [errors, setErrors] = useState({});
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState(null);
  const v = () => { const e = {}; if (form.vorname.trim().length < 2) e.vorname = t.contact.validation.firstName; if (form.nachname.trim().length < 2) e.nachname = t.contact.validation.lastName; if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = t.contact.validation.email; if (form.nachricht.trim().length < 10) e.nachricht = t.contact.validation.message; setErrors(e); return !Object.keys(e).length; };
  const submit = async (e) => {
    e.preventDefault(); if (!v()) return; setBusy(true); track('form_submit', { form: 'contact' });
    try {
      const r = await fetch(`${API}/api/contact`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) });
      const d = await r.json();
      if (r.ok) { setStatus({ t: 'success', m: t.contact.form.success }); setForm({ vorname: '', nachname: '', email: '', telefon: '', unternehmen: '', nachricht: '', _hp: '' }); }
      else throw new Error(d.detail || 'Error');
    } catch (err) { setStatus({ t: 'error', m: t.contact.form.error }); track('form_error', { error: err.message }); }
    finally { setBusy(false); }
  };
  return (
    <AnimSection id="kontakt" className="section bg-dark" aria-labelledby="contact-t" data-testid="contact-section">
      <div className="container">
        <div className="contact-grid">
          <motion.div className="contact-info" variants={fadeUp}>
            <span className="label">{t.contact.label}</span>
            <h2 id="contact-t" style={{ fontSize: 'clamp(1.75rem,4vw,2.5rem)', fontWeight: 800 }}>{t.contact.title}</h2>
            <p className="section-subtitle">{t.contact.subtitle}</p>
            <div className="contact-benefits">
              {t.contact.benefits.map((b, i) => <div key={i} className="contact-benefit"><I n="verified" /><span>{b}</span></div>)}
            </div>
            <button className="btn btn-primary btn-lg btn-glow contact-cta-btn" onClick={() => { onBook(); track('cta_click', { loc: 'contact' }); }} data-testid="contact-book-btn">{t.contact.ctaBtn} <I n="calendar_month" /></button>
          </motion.div>
          <motion.div className="contact-form-box" variants={fadeUp}>
            <form onSubmit={submit} className="contact-form" noValidate data-testid="contact-form">
              <input type="text" name="_hp" value={form._hp} onChange={e => setForm({ ...form, _hp: e.target.value })} style={{ display: 'none' }} tabIndex={-1} autoComplete="off" />
              <div className="form-row">
                <div className="form-group"><label htmlFor="vorname" className="form-label">{t.contact.form.firstName} *</label><input type="text" id="vorname" className={`form-input ${errors.vorname ? 'error' : ''}`} value={form.vorname} onChange={e => setForm({ ...form, vorname: e.target.value })} disabled={busy} required data-testid="input-vorname" />{errors.vorname && <span className="form-error" role="alert">{errors.vorname}</span>}</div>
                <div className="form-group"><label htmlFor="nachname" className="form-label">{t.contact.form.lastName} *</label><input type="text" id="nachname" className={`form-input ${errors.nachname ? 'error' : ''}`} value={form.nachname} onChange={e => setForm({ ...form, nachname: e.target.value })} disabled={busy} required data-testid="input-nachname" />{errors.nachname && <span className="form-error" role="alert">{errors.nachname}</span>}</div>
              </div>
              <div className="form-row">
                <div className="form-group"><label htmlFor="email" className="form-label">{t.contact.form.email} *</label><input type="email" id="email" className={`form-input ${errors.email ? 'error' : ''}`} value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} disabled={busy} required data-testid="input-email" />{errors.email && <span className="form-error" role="alert">{errors.email}</span>}</div>
                <div className="form-group"><label htmlFor="telefon" className="form-label">{t.contact.form.phone}</label><input type="tel" id="telefon" className="form-input" value={form.telefon} onChange={e => setForm({ ...form, telefon: e.target.value })} disabled={busy} /></div>
              </div>
              <div className="form-group"><label htmlFor="unternehmen" className="form-label">{t.contact.form.company}</label><input type="text" id="unternehmen" className="form-input" value={form.unternehmen} onChange={e => setForm({ ...form, unternehmen: e.target.value })} disabled={busy} /></div>
              <div className="form-group"><label htmlFor="nachricht" className="form-label">{t.contact.form.message} *</label><textarea id="nachricht" rows="4" className={`form-textarea ${errors.nachricht ? 'error' : ''}`} value={form.nachricht} onChange={e => setForm({ ...form, nachricht: e.target.value })} disabled={busy} required data-testid="input-nachricht"></textarea>{errors.nachricht && <span className="form-error" role="alert">{errors.nachricht}</span>}</div>
              <button type="submit" className="btn btn-primary btn-glow contact-submit" disabled={busy} data-testid="contact-submit-btn">{busy ? <><span className="spinner"></span>{t.contact.form.sending}</> : t.contact.form.submit}</button>
              {status && <div className={`form-status ${status.t}`} role="alert" data-testid="contact-status"><I n={status.t === 'success' ? 'check_circle' : 'error'} />{status.m}</div>}
            </form>
          </motion.div>
        </div>
      </div>
    </AnimSection>
  );
};

/* ═══════════ LIVE CHAT ═══════════ */
const LiveChat = ({ isOpen, onClose, initialQ, t, lang }) => {
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sid] = useState(() => genSid());
  const [qual, setQual] = useState({});
  const endRef = useRef(null);
  const inputRef = useRef(null);
  const sentInitial = useRef(false);

  /* Reset chat on language change */
  useEffect(() => {
    setMsgs([]);
    sentInitial.current = false;
  }, [lang]);

  useEffect(() => {
    if (isOpen && msgs.length === 0) {
      setMsgs([{ role: 'assistant', content: t.chat.welcome, ts: Date.now() }]);
      track('chat_started');
    }
  }, [isOpen, msgs.length, t.chat.welcome]);

  useEffect(() => {
    if (initialQ && isOpen && !sentInitial.current) {
      sentInitial.current = true;
      setTimeout(() => send(initialQ), 300);
    }
  }, [initialQ, isOpen]);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [msgs]);
  useEffect(() => {
    if (isOpen) { inputRef.current?.focus(); document.body.style.overflow = 'hidden'; }
    return () => { document.body.style.overflow = ''; };
  }, [isOpen]);

  const send = async (text = input) => {
    const txt = (typeof text === 'string' ? text : input).trim();
    if (!txt || loading) return;
    setMsgs(prev => [...prev, { role: 'user', content: txt, ts: Date.now() }]);
    setInput('');
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/chat/message`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sid, message: txt, language: lang })
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || 'Error');
      setMsgs(prev => [...prev, { role: 'assistant', content: d.message, ts: Date.now(), actions: d.actions }]);
      setQual(d.qualification || {});
      if (d.should_escalate) track('chat_escalation', { qual: d.qualification });
    } catch (_) {
      setMsgs(prev => [...prev, { role: 'assistant', content: t.contact.form.error, ts: Date.now() }]);
    } finally { setLoading(false); }
  };

  const onKey = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } };

  if (!isOpen) return null;
  return (
    <div className="chat-overlay" onClick={e => e.target === e.currentTarget && onClose()} role="dialog" aria-modal="true" aria-labelledby="chat-t" data-testid="chat-modal">
      <motion.div className="chat-modal" initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} transition={{ duration: 0.3 }}>
        <button className="chat-close" onClick={onClose} aria-label="Close" data-testid="chat-close"><I n="close" /></button>
        <div className="chat-layout">
          <div className="chat-sidebar">
            <h2 id="chat-t" className="chat-sidebar-title">{t.chat.sidebarTitle}</h2>
            <p className="chat-sidebar-desc">{t.chat.sidebarDesc}</p>
            <div className="chat-presets">
              {t.chat.presets.map((q, i) => (
                <button key={i} className="chat-preset" onClick={() => { track('preset_click', { q }); send(q); }} data-testid={`chat-preset-${i}`}><svg className="chat-preset-arrow" width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M1 7h10M8 3.5L11.5 7 8 10.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg><span>{q}</span></button>
              ))}
            </div>
            <div className="chat-sidebar-cta"><button className="btn btn-primary btn-glow" onClick={() => { track('chat_booking_click'); send(t.chat.presets[3] || 'Book a meeting'); }} style={{ width: '100%' }} data-testid="chat-sidebar-book-btn">{t.chat.bookBtn}</button></div>
          </div>
          <div className="chat-main">
            <div className="chat-header"><div className="chat-status"><span className="status-dot on"></span>{t.chat.status}</div><span className="chat-topic">{t.chat.topicLabel}</span></div>
            <div className="chat-msgs" data-testid="chat-messages">
              {msgs.map((m, i) => (
                <motion.div key={i} className={`chat-msg ${m.role}`} data-testid={`chat-msg-${i}`} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }}>
                  {m.role === 'assistant' ? (
                    <div className="chat-md">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
                    </div>
                  ) : (
                    <div>{m.content}</div>
                  )}
                  {m.actions && m.actions.length > 0 && <div className="chat-msg-actions">{m.actions.map((a, ai) => <button key={ai} className="btn btn-sm btn-primary" onClick={() => send(t.booking.title)}>{a.label}</button>)}</div>}
                </motion.div>
              ))}
              {loading && <div className="chat-msg assistant"><div className="chat-typing"><span></span><span></span><span></span></div></div>}
              <div ref={endRef} />
            </div>
            <div className="chat-input-area">
              <input ref={inputRef} type="text" className="chat-input" placeholder={t.chat.placeholder} value={input} onChange={e => setInput(e.target.value)} onKeyDown={onKey} disabled={loading} aria-label="Message" data-testid="chat-input" />
              <button className="chat-send" onClick={() => send()} disabled={!input.trim() || loading} aria-label="Send" data-testid="chat-send"><I n="send" /></button>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

/* ═══════════ BOOKING MODAL ═══════════ */
const Booking = ({ isOpen, onClose, t, lang }) => {
  const locale = LOCALE_MAP[lang] || 'de-DE';
  const fmtDate = (d) => new Date(d).toLocaleDateString(locale, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  const fmtDateShort = (d) => new Date(d).toLocaleDateString(locale, { weekday: 'short', day: 'numeric', month: 'short' });

  const [step, setStep] = useState(1);
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');
  const [slots, setSlots] = useState([]);
  const [form, setForm] = useState({ vorname: '', nachname: '', email: '', telefon: '', unternehmen: '', thema: '' });
  const [errors, setErrors] = useState({});
  const [busy, setBusy] = useState(false);
  const [ok, setOk] = useState(null);
  const dates = useMemo(() => { const d = []; const now = new Date(); for (let i = 1; i <= 14; i++) { const x = new Date(now); x.setDate(now.getDate() + i); if (x.getDay() !== 0 && x.getDay() !== 6) d.push(x.toISOString().split('T')[0]); } return d; }, []);
  useEffect(() => { if (date) { fetch(`${API}/api/booking/slots?date=${date}`).then(r => r.json()).then(d => setSlots(d.slots || [])).catch(() => setSlots(['09:00','10:00','11:00','14:00','15:00','16:00'])); } }, [date]);
  useEffect(() => { if (isOpen) { document.body.style.overflow = 'hidden'; track('booking_modal_opened'); } return () => { document.body.style.overflow = ''; }; }, [isOpen]);
  const v = () => { const e = {}; if (form.vorname.trim().length < 2) e.vorname = t.booking.validation.firstName; if (form.nachname.trim().length < 2) e.nachname = t.booking.validation.lastName; if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = t.booking.validation.email; setErrors(e); return !Object.keys(e).length; };
  const submit = async () => {
    if (!v()) return; setBusy(true); track('booking_submit', { date, time });
    try {
      const r = await fetch(`${API}/api/booking`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...form, date, time }) });
      const d = await r.json();
      if (r.ok) { setOk(d); track('calendar_booked', { id: d.booking_id }); } else throw new Error(d.detail);
    } catch (e) { setErrors({ submit: e.message || 'Booking failed' }); } finally { setBusy(false); }
  };
  if (!isOpen) return null;
  return (
    <div className="booking-overlay" onClick={e => e.target === e.currentTarget && onClose()} role="dialog" aria-modal="true" aria-labelledby="book-t" data-testid="booking-modal">
      <motion.div className="booking-modal" initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} transition={{ duration: 0.3 }}>
        <button className="booking-close" onClick={onClose} aria-label="Close" data-testid="booking-close"><I n="close" /></button>
        {ok ? (
          <div className="booking-success" data-testid="booking-success"><I n="check_circle" c="booking-success-icon" /><h2>{t.booking.successTitle}</h2><p>{fmtDate(date)} — {time}</p><p>{t.booking.successText.replace('{email}', form.email)}</p><button className="btn btn-primary btn-glow" onClick={onClose}>{t.booking.close}</button></div>
        ) : (
          <>
            <h2 id="book-t" className="booking-title">{t.booking.title}</h2>
            <div className="booking-steps">{t.booking.steps.map((s, i) => <div key={i} className={`booking-step-ind ${step >= i + 1 ? 'active' : ''}`}>{i + 1}. {s}</div>)}</div>
            {step === 1 && (
              <div className="booking-step" data-testid="booking-step-1">
                <h3>{t.booking.selectDate}</h3>
                <div className="booking-dates">{dates.map(d => <button key={d} className={`booking-date ${date === d ? 'sel' : ''}`} onClick={() => setDate(d)} data-testid={`booking-date-${d}`}>{fmtDateShort(d)}</button>)}</div>
                {date && <><h3>{t.booking.selectTime}</h3><div className="booking-times">{slots.length > 0 ? slots.map(s => <button key={s} className={`booking-time ${time === s ? 'sel' : ''}`} onClick={() => setTime(s)} data-testid={`booking-time-${s}`}>{s}</button>) : <p style={{ color: 'var(--nx-muted)' }}>{t.booking.noTimes}</p>}</div></>}
                <button className="btn btn-primary btn-glow booking-next" disabled={!date || !time} onClick={() => setStep(2)} data-testid="booking-next">{t.booking.next} <I n="arrow_forward" /></button>
              </div>
            )}
            {step === 2 && (
              <div className="booking-step" data-testid="booking-step-2">
                <button className="booking-back" onClick={() => setStep(1)}><I n="arrow_back" /> {t.booking.back}</button>
                <div className="booking-selected"><I n="event" /><span>{fmtDate(date)} — {time}</span></div>
                <div className="booking-form">
                  <div className="form-row">
                    <div className="form-group"><label htmlFor="b-vn" className="form-label">{t.booking.firstName} *</label><input type="text" id="b-vn" className={`form-input ${errors.vorname ? 'error' : ''}`} value={form.vorname} onChange={e => setForm({ ...form, vorname: e.target.value })} data-testid="booking-vorname" /></div>
                    <div className="form-group"><label htmlFor="b-nn" className="form-label">{t.booking.lastName} *</label><input type="text" id="b-nn" className={`form-input ${errors.nachname ? 'error' : ''}`} value={form.nachname} onChange={e => setForm({ ...form, nachname: e.target.value })} data-testid="booking-nachname" /></div>
                  </div>
                  <div className="form-group"><label htmlFor="b-em" className="form-label">{t.booking.email} *</label><input type="email" id="b-em" className={`form-input ${errors.email ? 'error' : ''}`} value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} data-testid="booking-email" /></div>
                  <div className="form-row">
                    <div className="form-group"><label htmlFor="b-tel" className="form-label">{t.booking.phone}</label><input type="tel" id="b-tel" className="form-input" value={form.telefon} onChange={e => setForm({ ...form, telefon: e.target.value })} /></div>
                    <div className="form-group"><label htmlFor="b-co" className="form-label">{t.booking.company}</label><input type="text" id="b-co" className="form-input" value={form.unternehmen} onChange={e => setForm({ ...form, unternehmen: e.target.value })} /></div>
                  </div>
                  <div className="form-group"><label htmlFor="b-th" className="form-label">{t.booking.message}</label><input type="text" id="b-th" className="form-input" value={form.thema} onChange={e => setForm({ ...form, thema: e.target.value })} /></div>
                  {errors.submit && <div className="form-error">{errors.submit}</div>}
                  <button className="btn btn-primary btn-glow booking-submit" onClick={submit} disabled={busy} data-testid="booking-submit">{busy ? <><span className="spinner"></span></> : t.booking.submit}</button>
                </div>
              </div>
            )}
          </>
        )}
      </motion.div>
    </div>
  );
};

/* ═══════════ FOOTER ═══════════ */
const Ft = ({ onCookieSettings, t, lang }) => {
  const lp = LEGAL_PATHS[lang] || LEGAL_PATHS.de;
  return (
    <footer className="footer" role="contentinfo" data-testid="footer">
      <div className="container">
        <div className="footer-grid">
          <div className="footer-brand">
            <div className="footer-logo"><img src="/icon-mark.svg" alt="" width="28" height="28" /><span>NeXify<em>AI</em></span></div>
            <div className="footer-tagline">{t.footer.tagline}</div>
            <div className="footer-legal-name">{COMPANY.legal}</div>
            <address className="footer-contact">
              <p><strong>NL:</strong> {COMPANY.addr.nl.s}, {COMPANY.addr.nl.c}</p>
              <p><strong>DE:</strong> {COMPANY.addr.de.s}, {COMPANY.addr.de.c}</p>
              <p>Tel: <a href={`tel:${COMPANY.phone.replace(/\s/g, '')}`}>{COMPANY.phone}</a></p>
              <p>E-Mail: <a href={`mailto:${COMPANY.email}`}>{COMPANY.email}</a></p>
            </address>
          </div>
          <nav className="footer-nav-col">
            <h3 className="footer-nav-title">{t.footer.nav}</h3>
            <ul className="footer-links">
              <li><a href="#loesungen">{t.nav.leistungen}</a></li><li><a href="#use-cases">{t.nav.usecases}</a></li>
              <li><a href="#app-dev">{t.nav.appdev}</a></li><li><a href="#integrationen">{t.nav.integrationen}</a></li>
              <li><a href="#preise">{t.nav.tarife}</a></li><li><a href="#kontakt">{t.footer.kontakt}</a></li>
            </ul>
          </nav>
          <nav className="footer-nav-col">
            <h3 className="footer-nav-title">{t.footer.legal}</h3>
            <ul className="footer-links">
              <li><a href={lp.impressum}>{t.footer.impressum}</a></li>
              <li><a href={lp.datenschutz}>{t.footer.datenschutz}</a></li>
              <li><a href={lp.agb}>{t.footer.agb}</a></li>
              <li><a href={lp.ki}>{t.footer.ki}</a></li>
              <li><button onClick={onCookieSettings} style={{ background: 'none', border: 'none', color: 'inherit', font: 'inherit', cursor: 'pointer', padding: 0 }}>{t.footer.cookie}</button></li>
            </ul>
            <div className="footer-ids"><p>KvK: {COMPANY.kvk}</p><p>USt-ID: {COMPANY.vat}</p></div>
          </nav>
          <div>
            <h3 className="footer-nav-title">{t.footer.kontakt}</h3>
            <ul className="footer-links">
              <li><a href={`tel:${COMPANY.phone.replace(/\s/g, '')}`}>{COMPANY.phone}</a></li>
              <li><a href={`mailto:${COMPANY.email}`}>{COMPANY.email}</a></li>
              <li><a href={`https://${COMPANY.web}`} target="_blank" rel="noopener noreferrer">{COMPANY.web}</a></li>
            </ul>
          </div>
        </div>
        <div className="footer-bottom">
          <span className="footer-copy">{t.footer.copy.replace('{y}', new Date().getFullYear())}</span>
          <div className="footer-status"><span className="status-dot on"></span>{t.footer.status}</div>
        </div>
      </div>
    </footer>
  );
};

/* ═══════════ CHAT TRIGGER ═══════════ */
const ChatTrigger = ({ onClick, t }) => (
  <motion.button className="chat-trigger" onClick={onClick} aria-label={t.hero.cta2} data-testid="chat-trigger" whileHover={{ y: -3, scale: 1.02 }} whileTap={{ scale: 0.98 }}>
    <span className="chat-trigger-text">{t.hero.cta2}</span>
    <span className="chat-trigger-icon"><I n="forum" /></span>
  </motion.button>
);

/* ═══════════ COOKIE CONSENT ═══════════ */
const CookieConsent = ({ show, onAccept, onReject, t, lang }) => {
  if (!show) return null;
  const lp = LEGAL_PATHS[lang] || LEGAL_PATHS.de;
  return (
    <motion.div className="cookie-banner" role="dialog" aria-label="Cookies" data-testid="cookie-banner" initial={{ y: 100 }} animate={{ y: 0 }} transition={{ duration: 0.4 }}>
      <div className="cookie-inner">
        <div className="cookie-text">{t.cookie.text} <a href={lp.datenschutz}>{t.cookie.link}</a>.</div>
        <div className="cookie-actions">
          <button className="btn btn-sm btn-secondary" onClick={onReject} data-testid="cookie-reject">{t.cookie.reject}</button>
          <button className="btn btn-sm btn-primary" onClick={onAccept} data-testid="cookie-accept">{t.cookie.accept}</button>
        </div>
      </div>
    </motion.div>
  );
};

/* ═══════════ MAIN APP ═══════════ */
function App() {
  const { lang } = useLanguage();
  const t = T[lang] || T.de;

  const [chatOpen, setChatOpen] = useState(false);
  const [bookOpen, setBookOpen] = useState(false);
  const [chatQ, setChatQ] = useState('');
  const [showCookie, setShowCookie] = useState(false);

  useEffect(() => {
    track('page_view', { page: 'landing', lang });
    const consent = localStorage.getItem('nx_cookie_consent');
    if (!consent) setShowCookie(true);
    let maxSc = 0;
    const h = () => { const p = Math.round((window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100); if (p > maxSc) { maxSc = p; if ([25, 50, 75, 100].includes(p)) track('scroll_depth', { depth: p }); } };
    window.addEventListener('scroll', h, { passive: true });
    return () => window.removeEventListener('scroll', h);
  }, [lang]);

  const acceptCookies = () => { localStorage.setItem('nx_cookie_consent', 'all'); setShowCookie(false); };
  const rejectCookies = () => { localStorage.setItem('nx_cookie_consent', 'essential'); setShowCookie(false); };
  const openCookieSettings = () => { localStorage.removeItem('nx_cookie_consent'); setShowCookie(true); };

  return (
    <div className="app" data-testid="app-root">
      <SEOHead lang={lang} page="home" />
      <a href="#loesungen" className="skip-link">Skip to content</a>
      <Nav onBook={() => setBookOpen(true)} t={t} />
      <main id="main-content">
        <Hero onBook={() => setBookOpen(true)} t={t} />
        <Solutions t={t} />
        <UseCases t={t} />
        <AppDev onBook={() => setBookOpen(true)} t={t} />
        <Process t={t} />
        <Integrations t={t} />
        <Governance t={t} />
        <Pricing onBook={() => setBookOpen(true)} t={t} />
        <FAQ t={t} />
        <Contact onBook={() => setBookOpen(true)} t={t} />
      </main>
      <Ft onCookieSettings={openCookieSettings} t={t} lang={lang} />
      <ChatTrigger onClick={() => { setChatOpen(true); track('chat_trigger_click'); }} t={t} />
      <LiveChat isOpen={chatOpen} onClose={() => setChatOpen(false)} initialQ={chatQ} t={t} lang={lang} />
      <Booking isOpen={bookOpen} onClose={() => setBookOpen(false)} t={t} lang={lang} />
      <CookieConsent show={showCookie} onAccept={acceptCookies} onReject={rejectCookies} t={t} lang={lang} />
    </div>
  );
}

export default App;
